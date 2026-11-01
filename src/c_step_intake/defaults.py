# -*- coding: utf-8 -*-
"""Pre-fill application forms from the logged-in user's account.

Used as ``defaultFactory`` on the identity fields. A default applies only
when the add form opens, so it never overwrites a saved application, and the
applicant can still change it. It is a convenience, not a record of who
created the application.

Accounts differ in what they carry: ``first_name``, ``last_name`` and
``employeeID`` are not standard Plone properties and exist only if the site's
login setup (SSO, LDAP, a custom member schema) fills them in. Every function
here returns None when a value is missing, so the field is simply left
blank. Anonymous visitors get blanks too.

A missing value is ``None``, not ``''``: the Email field rejects an empty
string as an invalid address, which would break the form for anyone whose
account has no email.
"""
from plone import api


def _current_user():
    if api.user.is_anonymous():
        return None
    return api.user.get_current()


def _property(user, name):
    value = user.getProperty(name, None) if user is not None else None
    return str(value).strip() if value else ''


def _split_fullname(user):
    """Return (first, last) from the standard ``fullname`` property."""
    first, _sep, last = _property(user, 'fullname').partition(' ')
    return first.strip(), last.strip()


def first_name():
    user = _current_user()
    return _property(user, 'first_name') or _split_fullname(user)[0] or None


def last_name():
    user = _current_user()
    return _property(user, 'last_name') or _split_fullname(user)[1] or None


def email():
    return _property(_current_user(), 'email') or None


def emplid():
    """The CUNY EMPLID, kept only if it is a valid 8-digit one."""
    value = _property(_current_user(), 'employeeID')
    return value if value.isdigit() and len(value) == 8 else None
