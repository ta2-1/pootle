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
from pootle_statistics.models import Submission, ScoreLog, TranslationActionCodes
from pootle_store.models import Suggestion, UnitSource, Store

from .models import UserStoreScore


logger = logging.getLogger(__name__)


@receiver(post_save, sender=UserStoreScore)
def handle_tp_score_data_save(**kwargs):
    tp = kwargs["instance"].store.translation_project
    update_score_data.send(tp.__class__, instance=tp)


@receiver(post_save, sender=Submission)
def handle_store_score_data_on_submission_save(**kwargs):
    submission = kwargs["instance"].unit.store
    update_score_data.send(submission.__class__, instance=submission)


@receiver(post_save, sender=Suggestion)
def handle_store_score_data_on_suggestion_save(**kwargs):
    suggestion = kwargs["instance"]
    update_score_data.send(suggestion.__class__, instance=suggestion)


def handle_scorelog_save(**kwargs):
    scorelog = kwargs["instance"]
    store = scorelog.submission.unit.store
    created = False
    changed = dict(suggested=0, translated=0, reviewed=0)
    review_actions = [
        TranslationActionCodes.SUGG_REVIEWED_ACCEPTED,
        TranslationActionCodes.REVIEWED,
        TranslationActionCodes.EDITED]
    if scorelog.translated_wordcount is not None:
        changed["translated"] = scorelog.translated_wordcount
    elif scorelog.action_code in review_actions:
        changed["reviewed"] = scorelog.wordcount
    try:
        user_score = store.user_scores.get(
            date=scorelog.creation_time.date(),
            user=scorelog.user)
    except store.user_scores.model.DoesNotExist:
        user_score = store.user_scores.create(
            date=scorelog.creation_time.date(),
            user=scorelog.user,
            score=scorelog.score_delta,
            **changed)
        created = True
    if not created:
        user_score.score += scorelog.score_delta
        for k, v in changed.items():
            existing = getattr(user_score, k)
            if v is not 0:
                setattr(user_score, k, existing + v)
        user_score.save()
