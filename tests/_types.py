"""Shared typing aliases for the test suite."""

from __future__ import annotations

from collections.abc import Callable

from repeaterbook.models import Repeater

SampleRepeaterFactory = Callable[..., Repeater]
"""Return type of the ``sample_repeater`` fixture: a Repeater factory."""
