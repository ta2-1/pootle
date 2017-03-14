# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.


class UserScoreDataUpdater(object):
    def __init__(self, user, *args, **kwargs):
        self.user = user


class UserStoreScoreDataUpdater(object):
    pass


class UserTPScoreDataUpdater(object):
    pass
