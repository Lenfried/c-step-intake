# -*- coding: utf-8 -*-
"""Marker and behavior interfaces for c_step_intake."""
from zope.interface import Interface


class IApplication(Interface):
    """Marker implemented by every application content type.

    StepApplication and CstepApplication both implement this, so the
    eligibility event handler is registered once rather than once per type.
    """


class IEligibilityRecordMarker(Interface):
    """Marker enabling the eligibility record behavior."""


class IEligibilityRecord(Interface):
    """Append-only audit trail of eligibility decisions for one application.

    Every submit or resubmit appends an entry. Entries are never mutated, so a
    NYSED audit can reconstruct which inputs and which rule set produced each
    outcome, including for applications that were resubmitted after a request
    for more information.
    """

    def record(decision, payload):
        """Append one decision plus the payload it was derived from."""

    def entries():
        """Return every recorded decision, oldest first."""

    def latest():
        """Return the most recent decision entry, or None."""
