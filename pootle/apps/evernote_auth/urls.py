#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2013-2014 Evernote Corporation
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

from django.conf.urls import patterns, url

from .views import LinkView


urlpatterns = patterns('evernote_auth.views',
    #url(r'^$',
    #    'account_info',
    #    name='en-auth-account-info'),

    #url(r'^link/?$',
    #    LinkView.as_view(),
    #    name='en-auth-account-link'),
    #url(r'^unlink/?$',
    #    'unlink',
    #    name='en-auth-account-unlink'),

    url(r'^evernote/login/?$',
        'sso_login',
        name='en-auth-sso-login'),
    url(r'^evernote/return/(?P<redirect_to>.*)/?$',
        'sso_callback',
        name='en-auth-sso-callback'),
)
