# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from django.forms import ValidationError
from django.http import Http404
from django.utils.functional import cached_property

from pootle.core.url_helpers import split_pootle_path
from pootle.core.utils.stats import TOP_CONTRIBUTORS_CHUNK_SIZE
from pootle.core.views.base import PootleJSON

from pootle_app.models import Directory
from pootle_language.models import Language
from pootle_project.models import Project, ProjectSet
from pootle_translationproject.models import TranslationProject


from .forms import StatsForm


class TopContributorsJSON(PootleJSON):
    form_class = StatsForm

    @cached_property
    def request_args(self):
        stats_form = self.get_form()
        if not stats_form.is_valid():
            raise Http404(
                ValidationError(stats_form.errors).messages)
        return stats_form.cleaned_data

    def get_object(self, queryset=None):
        (language_code, project_code,
         dir_path, filename) = split_pootle_path(self.path)
        if language_code and project_code:
            tp = TranslationProject.objects.get(language__code=language_code,
                                                project__code=project_code)
            return tp.directory
        elif language_code:
            return Language.objects.get(code=language_code).directory
        elif project_code:
            return Project.objects.get(code=project_code).directory

        return Directory.objects.projects

    def get_form(self):
        return self.form_class(self.request.GET)

    @property
    def path(self):
        return self.request_args.get("path")

    def get_context_data(self, **kwargs_):
        offset = self.kwargs.get("offset", 0)
        chunk_size = TOP_CONTRIBUTORS_CHUNK_SIZE
        scores = self.object.scores

        def scores_to_json(score):
            score["user"] = score["user"].to_dict()
            return score
        top_scorers = scores.display(
            offset=offset,
            limit=chunk_size,
            formatter=scores_to_json)
        return dict(
            items=list(top_scorers),
            has_more_items=len(scores.top_scorers) > (offset + chunk_size))
