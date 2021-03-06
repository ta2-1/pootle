# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from datetime import date, timedelta

from django.contrib.auth import get_user_model
from django.db.models import Sum
from django.utils.functional import cached_property

from pootle.core.bulk import BulkCRUD
from pootle.core.contextmanagers import bulk_operations, keep_data
from pootle.core.delegate import event_score, log, score_updater
from pootle.core.signals import create, update, update_scores
from pootle_log.utils import LogEvent
from pootle_score.models import UserStoreScore, UserTPScore
from pootle_translationproject.models import TranslationProject

from .utils import to_datetime


class UserRelatedScoreCRUD(BulkCRUD):

    def post_create(self, **kwargs):
        if "objects" in kwargs and kwargs["objects"] is not None:
            self.update_scores(kwargs["objects"])

    def post_update(self, **kwargs):
        if "objects" in kwargs and kwargs["objects"] is not None:
            self.update_scores(kwargs["objects"])


class UserStoreScoreCRUD(UserRelatedScoreCRUD):
    model = UserStoreScore

    def select_for_update(self, qs):
        return qs.select_related("store", "store__translation_project")

    def update_scores(self, objects):
        users = set()
        stores = {}
        tps = {}
        for score in objects:
            users.add(score.user_id)
            if score.store_id not in stores:
                stores[score.store_id] = score.store
        for store in stores.values():
            if store.translation_project_id not in tps:
                tps[store.translation_project_id] = store.translation_project
                tp = store.translation_project
                update_scores.send(
                    tp.__class__,
                    instance=tp,
                    stores=stores.values(),
                    users=users)


class UserTPScoreCRUD(UserRelatedScoreCRUD):
    model = UserTPScore

    def select_for_update(self, qs):
        return qs.select_related("tp")

    def update_scores(self, objects):
        update_scores.send(
            get_user_model(),
            users=set(score.user_id for score in objects))


class ScoreUpdater(object):
    event_class = LogEvent
    related_object = None

    def __init__(self, context, *args, **kwargs):
        self.context = context

    @cached_property
    def logs(self):
        return log.get(self.context.__class__)(self.context)

    @cached_property
    def scoring(self):
        return event_score.gather(self.event_class)

    def set_scores(self, calculated_scores, existing=None):
        calculated_scores = list(self.iterate_scores(calculated_scores))
        score_dict = {
            (score[0], score[1]): score[2]
            for score
            in calculated_scores}
        updates = {}
        if existing:
            scores = existing
        else:
            scores = self.find_existing_scores(calculated_scores) or []
        for score in scores:
            id, date, user, score, reviewed, suggested, translated = score
            newscore = score_dict.get((date, user), None)
            if newscore is None:
                # delete ?
                continue
            oldscore = dict(
                score=score,
                reviewed=reviewed,
                translated=translated,
                suggested=suggested)
            for k in ["score", "suggested", "reviewed", "translated"]:
                _newscore = round(newscore.get(k, 0), 2)
                if round(oldscore[k], 2) != _newscore:
                    updates[id] = updates.get(id, {})
                    updates[id][k] = _newscore
            del score_dict[(date, user)]
        if updates:
            update.send(
                self.score_model,
                updates=updates)
        if score_dict:
            self.create_scores(score_dict)

    def filter_users(self, qs, users):
        field = "user_id"
        if not users:
            return qs
        return (
            qs.filter(**{field: list(users).pop()})
            if len(users) == 1
            else qs.filter(**{"%s__in" % field: users}))

    def find_existing_scores(self, scores):
        existing_scores = self.score_model.objects.none()
        users = set()
        tstamps = set()
        for timestamp, user, user_scores in scores:
            users.add(user)
            tstamps.add(timestamp)
        if not users and not tstamps:
            return
        existing_scores = self.score_model.objects.filter(
            user__in=users)
        existing_scores = existing_scores.filter(
            date__in=tstamps)
        existing_scores = existing_scores.filter(
            **{self.related_field: self.context.pk})
        return existing_scores.values_list(
            "id",
            "date",
            "user_id",
            "score",
            "reviewed",
            "suggested",
            "translated").iterator()

    def new_scores(self, scores):
        for (timestamp, user), user_scores in scores.items():
            created = self.score_model(
                date=timestamp,
                user_id=user,
                **user_scores)
            if self.related_object:
                setattr(created, self.related_object, self.context)
            yield created

    def create_scores(self, scores):
        created = list(self.new_scores(scores))
        create.send(
            self.score_model,
            objects=created)
        return created

    def update(self, users=None, existing=None, date=None):
        if date is not None:
            start = date
            end = date + timedelta(days=1)
        else:
            start = end = None
        return self.set_scores(
            self.calculate(users=users, start=start, end=end),
            existing=existing)

    def get_tp_scores(self):
        tp_scores = self.tp_score_model.objects.order_by("tp_id").values_list(
            "tp_id",
            "id",
            "date",
            "user_id",
            "score",
            "reviewed",
            "suggested",
            "translated")
        scores = {}
        for tp_score in tp_scores.iterator():
            tp = tp_score[0]
            scores[tp] = scores.get(tp, [])
            scores[tp].append(tp_score[1:])
        return scores

    def get_store_scores(self, tp):
        store_scores = self.store_score_model.objects.filter(
            store__translation_project_id=tp.id).order_by("store_id").values_list(
                "store_id",
                "id",
                "date",
                "user_id",
                "score",
                "reviewed",
                "suggested",
                "translated")
        scores = {}
        for store_score in store_scores.iterator():
            store = store_score[0]
            scores[store] = scores.get(store, [])
            scores[store].append(store_score[1:])
        return scores


class StoreScoreUpdater(ScoreUpdater):
    score_model = UserStoreScore
    related_field = "store_id"
    related_object = "store"

    def __init__(self, *args, **kwargs):
        self.user = kwargs.get('user')
        super(StoreScoreUpdater, self).__init__(*args, **kwargs)

    @property
    def store(self):
        return self.context

    def score_event(self, event, calculated_scores):
        if event.action not in self.scoring:
            return
        scores = self.scoring[event.action](event).get_score()
        if not scores or not any(x > 0 for x in scores.values()):
            return
        calculated_scores[event.timestamp.date()] = (
            calculated_scores.get(event.timestamp.date(), {}))
        calculated_scores[event.timestamp.date()][event.user.id] = (
            calculated_scores[event.timestamp.date()].get(event.user.id, {}))
        for k, score in scores.items():
            if not score:
                continue
            calculated_scores[event.timestamp.date()][event.user.id][k] = (
                calculated_scores[event.timestamp.date()][event.user.id].get(k, 0)
                + score)

    def calculate(self, start=None, end=None, users=None):
        calculated_scores = {}
        scored_events = self.logs.get_events(
            users=users,
            start=to_datetime(start),
            end=to_datetime(end),
            include_meta=False,
            event_sources=("suggestion", "submission"))
        for event in scored_events:
            self.score_event(event, calculated_scores)
        return calculated_scores

    def iterate_scores(self, scores):
        for timestamp, date_scores in scores.items():
            for user, user_scores in date_scores.items():
                yield timestamp, user, user_scores


class TPScoreUpdater(ScoreUpdater):
    related_field = "tp_id"
    score_model = UserTPScore
    store_score_model = UserStoreScore
    user_score_model = get_user_model()
    related_object = "tp"

    @property
    def tp(self):
        return self.context

    def iterate_scores(self, scores):
        score_values = scores.values(
            "date",
            "user_id",
            "score",
            "translated",
            "reviewed",
            "suggested")
        for score in score_values.iterator():
            yield (
                score.pop("date"),
                score.pop("user_id"),
                score)

    def calculate(self, start=None, end=None, users=None):
        qs = self.filter_users(self.store_score_model.objects, users)
        qs = qs.filter(store__translation_project=self.tp)
        return qs.order_by(
            "date", "user").values_list(
                "date", "user").annotate(
                    score=Sum("score"),
                    translated=Sum("translated"),
                    reviewed=Sum("reviewed"),
                    suggested=Sum("suggested"))

    def refresh_scores(self, users=None, existing=None, existing_tps=None):
        suppress_tp_scores = keep_data(
            signals=(update_scores, ),
            suppress=(TranslationProject, ))
        existing = existing or self.get_store_scores(self.tp)
        with bulk_operations(UserTPScore):
            with suppress_tp_scores:
                with bulk_operations(UserStoreScore):
                    for store in self.tp.stores.iterator():
                        score_updater.get(store.__class__)(store).update(
                            users=users,
                            existing=existing.get(store.id))
            self.update(users=users, existing=existing_tps)


class UserScoreUpdater(ScoreUpdater):
    tp_score_model = UserTPScore
    store_score_model = UserStoreScore
    score_model = get_user_model()

    def __init__(self, users=None, **kwargs):
        self.users = users

    def calculate(self, start=date.today(), end=None, **kwargs):
        return self.filter_users(
            self.tp_score_model.objects,
            kwargs.get("users")).order_by("user").values_list(
                "user").annotate(score=Sum("score"))

    def set_scores(self, calculated_scores, existing=None):
        update.send(
            self.score_model,
            updates={
                user: dict(score=score)
                for user, score
                in calculated_scores.iterator()})

    def clear(self):
        tp_scores = self.tp_score_model.objects.all()
        store_scores = self.store_score_model.objects.all()
        scores = self.score_model.objects.all()
        if self.users:
            tp_scores = tp_scores.filter(user_id__in=self.users)
            store_scores = store_scores.filter(user_id__in=self.users)
            scores = scores.filter(id__in=self.users)
        tp_scores.delete()
        store_scores.delete()
        scores.update(score=0)

    def refresh_scores(self, users=None, **kwargs):
        suppress_user_scores = keep_data(
            signals=(update_scores, ),
            suppress=(get_user_model(), ))
        tp_scores = self.get_tp_scores()

        with bulk_operations(get_user_model()):
            with suppress_user_scores:
                for tp in TranslationProject.objects.all():
                    score_updater.get(tp.__class__)(tp).refresh_scores(
                        users=users,
                        existing_tps=tp_scores.get(tp.id))
                self.update(users=users)
