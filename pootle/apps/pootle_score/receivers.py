# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import logging

from django.db.models.signals import post_save
from django.dispatch import receiver

from pootle.core.signals import update_score_data
from pootle_statistics.models import Submission
from pootle_store.models import Suggestion

from .models import UserStoreScore


logger = logging.getLogger(__name__)


@receiver(post_save, sender=UserStoreScore)
def handle_tp_score_data_save(**kwargs):
    tp = kwargs["instance"].store.translation_project
    update_score_data.send(tp.__class__, instance=tp)


@receiver(post_save, sender=Submission)
def handle_store_score_data(**kwargs):
    submission = kwargs["instance"]
    update_score_data.send(submission.__class__, instance=submission)


@receiver(post_save, sender=Suggestion)
def handle_store_score_data_on_suggestion_save(**kwargs):
    suggestion = kwargs["instance"]
    update_score_data.send(suggestion.__class__, instance=suggestion)
