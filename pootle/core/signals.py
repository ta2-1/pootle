#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from django.dispatch import Signal


changed = Signal(
    providing_args=["instance", "updates"],
    use_caching=True)
update_data = Signal(providing_args=["instance"], use_caching=True)
update_score_data = Signal()
filetypes_changed = Signal(
    providing_args=["instance", "filetype"],
    use_caching=True)
