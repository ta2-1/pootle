# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import pytest

from datetime import datetime

from pytest_pootle.factories import ScoreLogFactory, SubmissionFactory

from pootle_statistics.models import (ScoreLog, SubmissionTypes, SubmissionFields,
                                      SIMILARITY_THRESHOLD)


TEST_EDIT_TYPES = (SubmissionTypes.NORMAL, SubmissionTypes.SYSTEM,
                   SubmissionTypes.UPLOAD)


@pytest.mark.parametrize('submission_type', TEST_EDIT_TYPES)
@pytest.mark.django_db
def test_record_submission(member, submission_type):
    from pootle_store.models import Store
    store = Store.objects.first()
    unit = store.units.first()

    submission_params = {
        'store': store,
        'unit': unit,
        'field': SubmissionFields.TARGET,
        'type': submission_type,
        'old_value': unit.target,
        'new_value': 'New target',
        'similarity': 0,
        'mt_similarity': 0,
        'submitter': member,
        'translation_project': store.translation_project,
        'creation_time': datetime.now(),
    }

    sub = SubmissionFactory(**submission_params)
    assert ScoreLog.objects.filter(submission=sub).count() == 1


@pytest.mark.parametrize('similarity', (0, 0.1, 0.49, 0.5, 0.51, 0.6, 1))
def test_get_similarity(similarity):
    score_log = ScoreLogFactory.build(similarity=similarity)
    if similarity >= SIMILARITY_THRESHOLD:
        assert score_log.get_similarity() == similarity
    else:
        assert score_log.get_similarity() == 0


@pytest.mark.parametrize('similarity, mt_similarity', [(0, 1), (0.5, 0.5), (1, 0)])
def test_is_similarity_taken_from_mt(similarity, mt_similarity):
    submission = SubmissionFactory.build(similarity=similarity,
                                         mt_similarity=mt_similarity)
    score_log = ScoreLogFactory.build(submission=submission)
    if submission.similarity < submission.mt_similarity:
        assert score_log.is_similarity_taken_from_mt()
    else:
        assert not score_log.is_similarity_taken_from_mt()


from pootle_store.util import FUZZY, TRANSLATED, UNTRANSLATED
from pootle_statistics.models import TranslationActionCodes


class SubmissionHandler(object):

    def __init__(self):
        self.score = {}

    def handle_create_with_tranlation(self):
        pass

    def handle_translate(self):
        pass

    def handle_delete_translation(self):
        pass

    def handle_edit_own_translation(self):
        pass

    def handle_edit_translation(self):
        pass

    def handle_review_translation(self):
        pass

    def handle_mark_as_fuzzy(self):
        pass

    def handle_add_suggestion(self):
        pass

    def handle_accept_suggestion(self):
        pass

    def handle_reject_suggestion(self):
        pass

    def set_params(self, submission):
        self.score.update({
            'creation_time': submission.creation_time,
            'wordcount': submission.unit.source_wordcount,
            'similarity': submission.max_similarity,
            'submission': submission,
        })

    def process_submission(self, submission):
        if submission.unit.reviewed_by:
            reviewer = submission.unit.reviewed_by
        else:
            reviewer = submission.unit.submitted_by

        if (submission.type == SubmissionTypes.UNIT_CREATE
            and submission.new_value != ''):
            self.handle_create_with_tranlation()

        elif (submission.field == SubmissionFields.TARGET
              and submission.type in SubmissionTypes.EDIT_TYPES):
            if (submission.new_value != '' and submission.old_value == ''):
                self.handle_translate()
            else:
                if submission.new_value == '':
                    self.handle_delete_translation()
                else:
                    if (reviewer is not None and
                        submission.submitter.id == reviewer.id):
                        self.handle_edit_own_translation()
                    else:
                        self.handle_edit_translation()

        elif submission.field == SubmissionFields.STATE:
            if (int(submission.old_value) == FUZZY and
                int(submission.new_value) == TRANSLATED and
                not submission.unit._target_updated):
                self.handle_review_translation()

            elif (int(submission.old_value) == TRANSLATED and
                  int(submission.new_value) == FUZZY):
                self.handle_mark_as_fuzzy()

        elif submission.type == SubmissionTypes.SUGG_ADD:
            self.handle_add_suggestion()

        elif submission.type == SubmissionTypes.SUGG_ACCEPT:
            self.handle_accept_suggestion()

        elif submission.type == SubmissionTypes.SUGG_REJECT:
            self.handle_reject_suggestion()

        if self.score['action_code']:
            self.set_params(submission)


class SubmitterScore(SubmissionHandler):
    def handle_translate(self):
        self.score['action_code'] = TranslationActionCodes.NEW

    def handle_delete_translation(self):
        self.score['action_code'] = TranslationActionCodes.DELETED

    def handle_edit_own_translation(self):
        self.score['action_code'] = TranslationActionCodes.EDITED_OWN

    def handle_edit_translation(self):
        self.score['action_code'] = TranslationActionCodes.EDITED

    def handle_mark_as_fuzzy(self):
        self.score['action_code'] = TranslationActionCodes.MARKED_FUZZY

    def handle_review_translation(self):
        self.score['action_code'] = TranslationActionCodes.REVIEWED

    def handle_add_suggestion(self):
        self.score['action_code'] = TranslationActionCodes.SUGG_ADDED

    def handle_accept_suggestion(self):
        self.score['action_code'] = TranslationActionCodes.SUGG_REVIEWED_ACCEPTED

    def handle_reject_suggestion(self):
        self.score['action_code'] = TranslationActionCodes.SUGG_REVIEWED_REJECTED

    def process_submission(self, submission):
        super(SubmitterScore, self).process_submission(submission)
        if self.score['action_code'] is None:
            return

        self.score['user'] = submission.submitter


class PreviousTranslatorScore(SubmissionHandler):
    def handle_delete_translation(self):
        self.score['action_code'] = TranslationActionCodes.EDIT_PENALTY

    def process_submission(self, submission):
        translator = submission.unit.submitted_by
        if not translator:
            return

        super(PreviousTranslatorScore, self).process_submission(submission)
        if self.score['action_code'] is None:
            return

        self.score['user'] = translator


class PreviousReviewerScore(SubmissionHandler):

    def handle_delete_translation(self):
        self.score['action_code'] = TranslationActionCodes.REVIEW_PENALTY

    def handle_mark_as_fuzzy(self):
        self.score['action_code'] = TranslationActionCodes.REVIEW_PENALTY

    def process_submission(self, submission):
        if submission.unit.reviewed_by:
            reviewer = submission.unit.reviewed_by
        else:
            reviewer = submission.unit.submitted_by

        super(PreviousReviewerScore, self).process_submission(submission)
        if self.score['action_code'] is None:
            return

        self.score['user'] = reviewer


class SuggesterScore(SubmissionHandler):

    def handle_accept_suggestion(self):
        self.score['action_code'] = TranslationActionCodes.SUGG_ACCEPTED

    def handle_reject_suggestion(self):
        self.score['action_code'] = TranslationActionCodes.SUGG_ACCEPTED

    def process_submission(self, submission):
        if submission.suggestion is None:
            return

        super(SuggesterScore, self).process_submission(submission)
        if self.score['action_code'] is None:
            return

        self.score['user'] = submission.suggestion.user


class DummySubmission(object):

    def __init__(self, *args, **kwargs):
        self.creation_time = None
        self.unit.source_wordcount = None
        self.max_similarity = None
        self.unit.submitted_by = None
        self.submitter = None
        self.suggestion = None

    def score_dict(self):
        return {
            'creation_time': self.creation_time,
            'wordcount': self.unit.source_wordcount,
            'similarity': self.max_similarity,
            'submission': self,
        }
