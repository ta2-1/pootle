#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2015 Evernote Corporation
#
# This file is part of Pootle.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, see <http://www.gnu.org/licenses/>.

import logging
import os

# This must be run before importing Django.
os.environ['DJANGO_SETTINGS_MODULE'] = 'pootle.settings'

from pootle_store.models import Store

from . import PootleCommand


logger = logging.getLogger('stats')


class Command(PootleCommand):
    help = "Allow stats and text indices to be refreshed manually."

    cached_methods = None
    process_disabled_projects = True

    def handle_all_stores(self, translation_project, **options):
        store_filter = {
            'translation_project': translation_project,
        }

        self.process(store_filter=store_filter, **options)

    def handle_store(self, store, **options):
        store_filter = {
            'pk': store.pk,
        }

        self.process(store_filter=store_filter, **options)

    def process(self, **options):
        store_filter = options.get('store_filter', {})

        stores = Store.objects.all()
        if store_filter:
            stores = stores.filter(**store_filter)

        for store in stores.iterator():
            logger.info('Add job to update stats for %s' % store.pootle_path)
            store.update_all_cache()
