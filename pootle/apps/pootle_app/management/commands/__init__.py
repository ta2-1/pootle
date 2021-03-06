# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import datetime
import logging

from django.db import transaction
from django.core.management.base import BaseCommand, CommandError

from pootle.runner import set_sync_mode
from pootle_language.models import Language
from pootle_project.models import Project
from pootle_translationproject.models import TranslationProject


class SkipChecksMixin(object):
    def check(self, app_configs=None, tags=None, display_num_errors=False,
              include_deployment_checks=False):
        skip_tags = getattr(self, 'skip_system_check_tags', None)
        if skip_tags is not None:
            from django.core.checks.registry import registry
            tags = registry.tags_available() - set(skip_tags)

        super(SkipChecksMixin, self).check(
            app_configs=app_configs,
            tags=tags,
            display_num_errors=display_num_errors,
            include_deployment_checks=include_deployment_checks)


class PootleCommand(BaseCommand):
    """Base class for handling recursive pootle store management commands."""

    atomic_default = "tp"
    process_disabled_projects = False

    def add_arguments(self, parser):
        parser.add_argument(
            '--project',
            action='append',
            dest='projects',
            help='Project to refresh',
        )
        parser.add_argument(
            '--language',
            action='append',
            dest='languages',
            help='Language to refresh',
        )
        parser.add_argument(
            "--noinput",
            action="store_true",
            default=False,
            help=u"Never prompt for input",
        )
        parser.add_argument(
            "--no-rq",
            action="store_true",
            default=False,
            help=(u"Run all jobs in a single process, without "
                  "using rq workers"),
        )
        parser.add_argument(
            "--atomic",
            action="store",
            default=self.atomic_default,
            choices=["tp", "all", "none"],
            help=(
                u"Run commands using database atomic "
                u"transactions"))

    def __init__(self, *args, **kwargs):
        self.languages = []
        self.projects = []
        super(PootleCommand, self).__init__(*args, **kwargs)

    def do_translation_project(self, tp, **options):
        if hasattr(self, "handle_translation_project"):
            logging.info(u"Running %s over %s", self.name, tp)
            if not self.handle_translation_project(tp, **options):
                return
        if hasattr(self, "handle_all_stores"):
            logging.info(u"Running %s over %s's files", self.name, tp)
            self.handle_all_stores(tp, **options)
        elif hasattr(self, "handle_store"):
            store_query = tp.stores.live()
            for store in store_query.iterator():
                logging.info(u"Running %s over %s",
                             self.name, store.pootle_path)
                self.handle_store(store, **options)

    def check_projects(self, project_codes):
        existing_projects = Project.objects.filter(
            code__in=project_codes
        ).values_list("code", flat=True)
        if len(existing_projects) != len(project_codes):
            unrecognized_projects = list(set(project_codes) -
                                         set(existing_projects))
            raise CommandError("Unrecognized projects: %s" %
                               unrecognized_projects)

    def check_languages(self, language_codes):
        existing_languages = Language.objects.filter(
            code__in=language_codes
        ).values_list("code", flat=True)
        if len(existing_languages) != len(language_codes):
            unrecognized_languages = list(set(language_codes) -
                                          set(existing_languages))
            raise CommandError("Unrecognized languages: %s" %
                               unrecognized_languages)

    def handle(self, **options):
        if options["atomic"] == "all":
            with transaction.atomic():
                return self._handle(**options)
        else:
            return self._handle(**options)

    def _handle(self, **options):
        # adjust debug level to the verbosity option
        debug_levels = {
            0: logging.ERROR,
            1: logging.WARNING,
            2: logging.INFO,
            3: logging.DEBUG
        }
        logging.getLogger().setLevel(
            debug_levels.get(options['verbosity'], logging.DEBUG)
        )

        # reduce size of parse pool early on
        self.name = self.__class__.__module__.split('.')[-1]
        self.projects = options.pop('projects', [])
        self.languages = options.pop('languages', [])
        if self.projects:
            self.check_projects(self.projects)
        if self.languages:
            self.check_languages(self.languages)

        # info start
        start = datetime.datetime.now()
        logging.info('Start running of %s', self.name)

        try:
            self.handle_all(**options)
        except Exception as e:
            raise CommandError(e)

        # info finish
        end = datetime.datetime.now()
        logging.info('All done for %s in %s', self.name, end - start)

    def handle_all(self, **options):
        if options["no_rq"]:
            set_sync_mode(options['noinput'])

        tps = TranslationProject.objects.live().order_by(
            "project__code", "language__code").select_related(
                "project",
                "language",
                "directory",
                "project__source_language")

        if not self.process_disabled_projects:
            tps = tps.exclude(project__disabled=True)

        if self.projects:
            tps = tps.filter(project__code__in=self.projects)

        if self.languages:
            tps = tps.filter(language__code__in=self.languages)

        for tp in tps.iterator():
            if options["atomic"] == "tp":
                with transaction.atomic():
                    self.do_translation_project(tp, **options)
            else:
                self.do_translation_project(tp, **options)
