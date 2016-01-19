#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import functools

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.urlresolvers import reverse
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect
from django.utils.functional import cached_property
from django.utils.lru_cache import lru_cache

from import_export.views import handle_upload_form
from pootle.core.browser import (
    get_children, get_parent, get_table_headings)
from pootle.core.decorators import (
    get_path_obj, permission_required)
from pootle.core.helpers import (
    get_sidebar_announcements_context)
from pootle.core.views import (
    PootleBrowseView, PootleTranslateView, PootleExportView)
from pootle_app.models import Directory
from pootle_app.models.permissions import (
    check_permission, get_matching_permissions)
from pootle_app.views.admin.permissions import admin_permissions as admin_perms
from pootle_language.models import Language
from pootle_store.models import Store
from virtualfolder.helpers import (
    extract_vfolder_from_path, make_vfolder_treeitem_dict)
from virtualfolder.models import VirtualFolderTreeItem

from .models import TranslationProject


@get_path_obj
@permission_required('administrate')
def admin_permissions(request, translation_project):
    ctx = {
        'page': 'admin-permissions',

        'translation_project': translation_project,
        'project': translation_project.project,
        'language': translation_project.language,
        'directory': translation_project.directory,
    }
    return admin_perms(request, translation_project.directory,
                       'translation_projects/admin/permissions.html', ctx)


def redirect_to_tp_on_404(f):

    @functools.wraps(f)
    def method_wrapper(self, request, *args, **kwargs):
        User = get_user_model()
        request.profile = User.get(self.request.user)
        try:
            request.permissions = get_matching_permissions(
                request.profile,
                self.permission_context) or []
        except Http404 as e:
            lang = Language.get_canonical(kwargs['language_code'])
            if lang is not None and lang.code != kwargs['language_code']:
                kwargs["language_code"] = lang.code
                if kwargs.get("filename", None) is None:
                    return redirect(
                        reverse(
                            'pootle-tp-browse',
                            kwargs=kwargs))
                else:
                    return redirect(
                        reverse(
                            'pootle-tp-store-browse',
                            kwargs=kwargs))

            elif kwargs["dir_path"] or kwargs.get("filename", None):
                try:
                    tp = TranslationProject.objects \
                        .select_related('language').get(
                            project__code=kwargs["project_code"],
                            language__code=kwargs["language_code"]
                        )
                    # the TP exists so redirect to it
                    return redirect(
                        reverse(
                            'pootle-tp-browse',
                            kwargs={
                                k: v
                                for k, v
                                in kwargs.items()
                                if k in [
                                    "language_code",
                                    "project_code"]}))
                except TranslationProject.DoesNotExist:
                    pass

            # if we get here - the TP does not exist
            user_choice = self.request.COOKIES.get(
                'user-choice', None)
            if user_choice:
                url = None
                if user_choice == 'language':
                    url = reverse(
                        'pootle-language-browse',
                        args=[kwargs["language_code"]])
                elif user_choice == "project":
                    url = reverse(
                        'pootle-project-browse',
                        args=[kwargs["project_code"], '', ''])
                if url:
                    response = redirect(url)
                    response.delete_cookie('user-choice')
                    return response
            raise e
        return f(self, request, *args, **kwargs)
    return method_wrapper


class TPMixin(object):
    """This Mixin is used by all TP views.

    The context object may be a resource with the TP, ie a Directory or Store.
    """

    @redirect_to_tp_on_404
    def dispatch(self, request, *args, **kwargs):
        return super(TPMixin, self).dispatch(request, *args, **kwargs)

    @property
    def ctx_path(self):
        return self.tp.pootle_path

    @property
    def resource_path(self):
        return self.object.pootle_path.replace(self.ctx_path, "")

    @property
    def dir_path(self):
        return self.resource_path

    @cached_property
    def tp(self):
        return self.object.translation_project

    @cached_property
    def project(self):
        return self.tp.project

    @cached_property
    def language(self):
        return self.tp.language

    @cached_property
    def sidebar_announcements(self):
        return get_sidebar_announcements_context(
            self.request,
            (self.project, self.language, self.tp))


class TPDirectoryMixin(TPMixin):
    model = Directory
    browse_url_path = "pootle-tp-browse"
    export_url_path = "pootle-tp-export"
    translate_url_path = "pootle-tp-translate"

    @property
    def object_related(self):
        tp_prefix = (
            "parent__" * self.kwargs.get("dir_path", "").count("/"))
        return [
            "%stranslationproject" % tp_prefix,
            "%stranslationproject__language" % tp_prefix,
            "%stranslationproject__project" % tp_prefix]

    @lru_cache()
    def get_object(self):
        return get_object_or_404(
            Directory.objects.select_related(*self.object_related),
            pootle_path=self.path)

    @property
    def url_kwargs(self):
        return {
            "language_code": self.language.code,
            "project_code": self.project.code,
            "dir_path": self.dir_path}


class TPStoreMixin(TPMixin):
    model = Store
    browse_url_path = "pootle-tp-store-browse"
    export_url_path = "pootle-tp-store-export"
    translate_url_path = "pootle-tp-store-translate"
    is_store = True

    @property
    def permission_context(self):
        return self.get_object().parent

    @property
    def dir_path(self):
        return self.resource_path.replace(self.object.name, "")

    @property
    def url_kwargs(self):
        return {
            "language_code": self.language.code,
            "project_code": self.project.code,
            "dir_path": self.dir_path,
            "filename": self.object.name}

    @lru_cache()
    def get_object(self):
        path = (
            "/%(language_code)s/%(project_code)s/%(dir_path)s%(filename)s"
            % self.kwargs)
        return get_object_or_404(
            Store.objects.select_related(
                "parent",
                "translation_project__language",
                "translation_project__project"),
            pootle_path=path)


class TPBrowseBaseView(PootleBrowseView):
    template_extends = 'translation_projects/base.html'

    def get_context_data(self, *args, **kwargs):
        ctx = super(TPBrowseBaseView, self).get_context_data(*args, **kwargs)
        ctx.update(
            {'parent': get_parent(self.object)})
        return ctx


class TPBrowseStoreView(TPStoreMixin, TPBrowseBaseView):
    pass


class TPBrowseView(TPDirectoryMixin, TPBrowseBaseView):
    table_id = "tp"
    table_fields = [
        'name', 'progress', 'total', 'need-translation',
        'suggestions', 'critical', 'last-updated', 'activity']

    @cached_property
    def items(self):
        return get_children(self.object)

    def get_upload_widget(self, project):
        ctx = {}
        has_upload = (
            "import_export" in settings.INSTALLED_APPS
            and self.request.user.is_authenticated()
            and check_permission('translate', self.request))
        if has_upload:
            ctx.update(handle_upload_form(self.request, project))
            ctx.update(
                {'display_download': True,
                 'has_sidebar': True})
        return ctx

    @cached_property
    def has_vfolders(self):
        return self.object.has_vfolders

    @cached_property
    def vfolders(self):
        vftis = self.object.vf_treeitems
        if not self.is_admin:
            vftis = vftis.filter(vfolder__is_public=True)
        return [
            make_vfolder_treeitem_dict(vfolder_treeitem)
            for vfolder_treeitem
            in vftis.order_by('-vfolder__priority').select_related("vfolder")
            if (self.is_admin
                or vfolder_treeitem.is_visible)]

    @cached_property
    def vfolder_data(self):
        ctx = {}
        if 'virtualfolder' not in settings.INSTALLED_APPS:
            return {}
        if len(self.vfolders) > 0:
            table_fields = [
                'name', 'priority', 'progress', 'total',
                'need-translation', 'suggestions', 'critical',
                'last-updated', 'activity']
            ctx.update({
                'vfolders': {
                    'id': 'vfolders',
                    'fields': table_fields,
                    'headings': get_table_headings(table_fields),
                    'items': self.vfolders}})
        return ctx

    @cached_property
    def vfolder_stats(self):
        if 'virtualfolder' not in settings.INSTALLED_APPS:
            return {}
        stats = {"vfolders": {}}
        for vfolder_treeitem in self.vfolders or []:
            stats['vfolders'][
                vfolder_treeitem['code']] = vfolder_treeitem["stats"]
            del vfolder_treeitem["stats"]
        return stats

    @cached_property
    def stats(self):
        stats = self.vfolder_stats
        if stats and stats["vfolders"]:
            stats.update(self.object.get_stats())
        else:
            stats = self.object.get_stats()
        return stats

    def get_context_data(self, *args, **kwargs):
        ctx = super(TPBrowseView, self).get_context_data(*args, **kwargs)
        ctx.update(self.get_upload_widget(self.project))
        ctx.update(self.vfolder_data)
        return ctx


class TPTranslateBaseView(PootleTranslateView):
    translate_url_path = "pootle-tp-translate"
    browse_url_path = "pootle-tp-browse"
    export_url_path = "pootle-tp-export"
    template_extends = 'translation_projects/base.html'

    @property
    def pootle_path(self):
        return "%s%s" % (self.ctx_path, self.resource_path)

    @property
    def display_vfolder_priority(self):
        if 'virtualfolder' not in settings.INSTALLED_APPS:
            return False
        return VirtualFolderTreeItem.objects.filter(
            pootle_path__startswith=self.object.pootle_path).exists()


class TPTranslateView(TPDirectoryMixin, TPTranslateBaseView):

    @property
    def request_path(self):
        return "/%(language_code)s/%(project_code)s/%(dir_path)s" % self.kwargs

    @cached_property
    def extracted_path(self):
        return extract_vfolder_from_path(self.request_path)

    @property
    def display_vfolder_priority(self):
        if 'virtualfolder' not in settings.INSTALLED_APPS:
            return False
        vfolder = self.extracted_path[0]
        if vfolder:
            return False
        return VirtualFolderTreeItem.objects.filter(
            pootle_path__startswith=self.object.pootle_path).exists()

    @property
    def resource_path(self):
        vfolder = self.extracted_path[0]
        path = ""
        if vfolder:
            path = "%s/" % vfolder.name
        return (
            "%s%s"
            % (path,
               self.object.pootle_path.replace(self.ctx_path, "")))

    @property
    def path(self):
        return self.extracted_path[1]

    @property
    def vfolder_pk(self):
        vfolder = self.extracted_path[0]
        if vfolder:
            return vfolder.pk
        return ""


class TPTranslateStoreView(TPStoreMixin, TPTranslateBaseView):
    pass


class TPExportBaseView(PootleExportView):

    @property
    def source_language(self):
        return self.project.source_language


class TPExportView(TPDirectoryMixin, TPExportBaseView):
    pass


class TPExportStoreView(TPStoreMixin, TPExportBaseView):
    pass
