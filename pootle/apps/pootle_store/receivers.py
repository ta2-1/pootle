# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from django.dispatch import receiver

from pootle.core.signals import update_checks

from .models import Unit


@receiver(update_checks, sender=Unit)
def handle_unit_checks(**kwargs):
    unit = kwargs["instance"]
    keep_false_positives = kwargs.get("keep_false_positives", False)
    unit.update_qualitychecks(keep_false_positives=keep_false_positives)
