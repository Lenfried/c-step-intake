# -*- coding: utf-8 -*-
"""Single-page add and edit forms for both application types.

Plone renders each schema fieldset as a tab by default. These forms switch
tabbing off, so every fieldset is drawn in order on one page under its own
legend. The fieldsets themselves are unchanged.
"""
from plone.dexterity.browser import add
from plone.dexterity.browser import edit


class AddForm(add.DefaultAddForm):
    enable_form_tabbing = False


class AddView(add.DefaultAddView):
    form = AddForm


class EditForm(edit.DefaultEditForm):
    enable_form_tabbing = False
