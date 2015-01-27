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

from django.core.urlresolvers import reverse
from django.utils.http import urlencode

from allauth.socialaccount import providers
from allauth.socialaccount.providers.base import Provider, ProviderAccount


class TranslateEvernoteProvider(Provider):
    id = 'evernote'
    name = 'Evernote'
    package = 'evernote_auth'
    #account_class = ProviderAccount

    def get_login_url(self, request, **kwargs):
        url = reverse('en-auth-sso-login')
        if kwargs:
            url += '?' + urlencode(kwargs)
        return url

    #def extract_extra_data(self, response):
    #    return {}

    #def extract_uid(self, response):
    #    return response.identity_url

    #def extract_common_fields(self, response):
    #    return {}


providers.registry.register(TranslateEvernoteProvider)
