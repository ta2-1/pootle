# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import pytest

from pootle.core.delegate import data_tool, frozen
from pootle_store.models import Unit

from pootle_store.utils import move_store_within_tp


@pytest.mark.django_db
def test_frozen_unit(store0):
    unit = store0.units.first()
    frozen_unit = frozen.get(Unit)(unit)
    assert frozen_unit.source == unit.source_f
    assert frozen_unit.target == unit.target_f
    assert frozen_unit.state == unit.state
    assert frozen_unit.translator_comment == unit.getnotes(origin="translator")


@pytest.mark.django_db
def test_move_store_within_tp(store0, tp0):
    directory = tp0.directory.child_dirs.first()
    directory_data_tool = data_tool.get(directory.__class__)(directory)
    old_stats = directory_data_tool.get_stats()

    move_store_within_tp(store0, directory, 'moved_' + store0.name)

    assert store0.parent == directory
    stats = directory_data_tool.get_stats()
    assert stats['total'] == old_stats['total'] + store0.data.total_words
    assert (stats['critical'] ==
            old_stats['critical'] + store0.data.critical_checks)
