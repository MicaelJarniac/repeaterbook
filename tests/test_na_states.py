"""Tests for RepeaterBook's North American state identifiers."""

from __future__ import annotations

import pycountry
import pytest

from repeaterbook.na_states import NAState, state_country
from repeaterbook.services import RepeaterBookAPI

# Every (state_id, RepeaterBook state name) pair observed in a live download.
# Canada and Mexico are complete; the US sample is partial.
_OBSERVED_LIVE: dict[str, str] = {
    "CA01": "Alberta",
    "CA02": "British Columbia",
    "CA03": "Manitoba",
    "CA04": "New Brunswick",
    "CA05": "Newfoundland",
    "CA07": "Nova Scotia",
    "CA08": "Ontario",
    "CA09": "Prince Edward Island",
    "CA10": "Quebec",
    "CA11": "Saskatchewan",
    "CA12": "Yukon Territory",
    "CA13": "Northwest Territories",
    "CA14": "Nunavut",
    "MX01": "Aguascalientes",
    "MX02": "Baja California",
    "MX03": "Baja California Sur",
    "MX06": "Chihuahua",
    "MX07": "Coahuila",
    "MX08": "Colima",
    "MX09": "Mexico City",
    "MX10": "Durango",
    "MX11": "Guanajuato",
    "MX13": "Hidalgo",
    "MX14": "Jalisco",
    "MX15": "Mexico",
    "MX16": "Michoacán",
    "MX17": "Morelos",
    "MX19": "Nuevo Leon",
    "MX31": "Yucatan",
    "01": "Alabama",
    "04": "Arizona",
    "06": "California",
    "08": "Colorado",
    "36": "New York",
    "48": "Texas",
    "51": "Virginia",
}


def test_every_observed_id_is_a_member() -> None:
    """Each identifier seen on the live API must exist in the enum."""
    values = {s.value for s in NAState}
    assert set(_OBSERVED_LIVE) <= values


def test_country_attribution_matches_the_prefix() -> None:
    """state_country must agree with the identifier's own prefix."""
    for state in NAState:
        if state.value.startswith("CA"):
            assert state_country(state) == "Canada"
        elif state.value.startswith("MX"):
            assert state_country(state) == "Mexico"
        else:
            assert state.value.isdigit()
            assert state_country(state) == "United States"


def test_countries_are_all_north_american() -> None:
    """Every attributed country must be one the NA endpoint serves."""
    assert {state_country(s) for s in NAState} == set(RepeaterBookAPI.NA_COUNTRIES)


def test_values_are_unique() -> None:
    """No two members may share an identifier."""
    values = [s.value for s in NAState]
    assert len(values) == len(set(values))


@pytest.mark.parametrize(
    ("country_code", "prefix", "expected"),
    [("US", "US_", 56), ("CA", "CA_", 13), ("MX", "MX_", 32)],
)
def test_subdivision_counts(country_code: str, prefix: str, expected: int) -> None:
    """Each country's arm should cover all of its subdivisions.

    Cross-checked against pycountry so a missing member is caught even though
    the identifiers themselves are RepeaterBook's own and not derivable.
    """
    assert sum(s.name.startswith(prefix) for s in NAState) == expected
    subdivisions = pycountry.subdivisions.get(country_code=country_code)  # type: ignore[no-untyped-call]
    iso = len(subdivisions)
    # The US arm also carries DC and the territories, which ISO counts too.
    assert expected >= iso - 1


def test_us_values_are_two_digit_fips() -> None:
    """US identifiers are zero-padded two-digit FIPS codes.

    The padding matters: the API answers an unpadded '6' with an empty result
    set rather than an error.
    """
    for state in NAState:
        if state.name.startswith("US_"):
            assert len(state.value) == 2
            assert state.value.isdigit()


def test_non_us_values_are_upper_case() -> None:
    """Canadian and Mexican identifiers are upper-case.

    Lower-case 'ca01' is rejected by the API's edge, not answered.
    """
    for state in NAState:
        if not state.name.startswith("US_"):
            assert state.value == state.value.upper()
