"""RepeaterBook's own North American state and province identifiers.

RepeaterBook scopes North American queries with a ``state_id`` whose values
are its own invention. They are *not* ISO 3166-2, and cannot be derived from
it, so a general-purpose library such as ``pycountry`` is no help here:

===============  ==============  ==============
Subdivision      RepeaterBook    ISO 3166-2
===============  ==============  ==============
California       ``06``          ``US-CA``
Alberta          ``CA01``        ``CA-AB``
Jalisco          ``MX14``        ``MX-JAL``
===============  ==============  ==============

The United States uses two-digit FIPS codes, which RepeaterBook's API
documentation calls out as "State ID (FIPS)". Canada and Mexico use bespoke
``CA##``/``MX##`` numbering that RepeaterBook does not document at all --
hence this module. Canada numbers its provinces alphabetically and appends
the three territories; Mexico follows the INEGI alphabetical ordering.

Knowing these up front matters because the API truncates a response at 3500
results. Querying a whole country silently returns a partial answer, and any
subdivision missing from that slice is invisible -- so the identifiers cannot
be discovered by downloading first and reading them back off the data.

The values are also unforgiving: ``"6"`` is not ``"06"`` and returns an empty
result rather than an error, and lower-case ``ca01`` is rejected outright.
Selecting a member avoids inventing either mistake.
"""

from __future__ import annotations

__all__: tuple[str, ...] = (
    "NAState",
    "state_country",
)

from enum import StrEnum


class NAState(StrEnum):
    """A North American ``state_id`` accepted by RepeaterBook's export API.

    Members are named ``<country>_<subdivision>`` using each country's usual
    abbreviations, and each value is the identifier RepeaterBook expects.
    """

    # United States -- two-digit FIPS codes.
    US_AL = "01"
    """Alabama."""
    US_AK = "02"
    """Alaska."""
    US_AZ = "04"
    """Arizona."""
    US_AR = "05"
    """Arkansas."""
    US_CA = "06"
    """California."""
    US_CO = "08"
    """Colorado."""
    US_CT = "09"
    """Connecticut."""
    US_DE = "10"
    """Delaware."""
    US_DC = "11"
    """District of Columbia."""
    US_FL = "12"
    """Florida."""
    US_GA = "13"
    """Georgia."""
    US_HI = "15"
    """Hawaii."""
    US_ID = "16"
    """Idaho."""
    US_IL = "17"
    """Illinois."""
    US_IN = "18"
    """Indiana."""
    US_IA = "19"
    """Iowa."""
    US_KS = "20"
    """Kansas."""
    US_KY = "21"
    """Kentucky."""
    US_LA = "22"
    """Louisiana."""
    US_ME = "23"
    """Maine."""
    US_MD = "24"
    """Maryland."""
    US_MA = "25"
    """Massachusetts."""
    US_MI = "26"
    """Michigan."""
    US_MN = "27"
    """Minnesota."""
    US_MS = "28"
    """Mississippi."""
    US_MO = "29"
    """Missouri."""
    US_MT = "30"
    """Montana."""
    US_NE = "31"
    """Nebraska."""
    US_NV = "32"
    """Nevada."""
    US_NH = "33"
    """New Hampshire."""
    US_NJ = "34"
    """New Jersey."""
    US_NM = "35"
    """New Mexico."""
    US_NY = "36"
    """New York."""
    US_NC = "37"
    """North Carolina."""
    US_ND = "38"
    """North Dakota."""
    US_OH = "39"
    """Ohio."""
    US_OK = "40"
    """Oklahoma."""
    US_OR = "41"
    """Oregon."""
    US_PA = "42"
    """Pennsylvania."""
    US_RI = "44"
    """Rhode Island."""
    US_SC = "45"
    """South Carolina."""
    US_SD = "46"
    """South Dakota."""
    US_TN = "47"
    """Tennessee."""
    US_TX = "48"
    """Texas."""
    US_UT = "49"
    """Utah."""
    US_VT = "50"
    """Vermont."""
    US_VA = "51"
    """Virginia."""
    US_WA = "53"
    """Washington."""
    US_WV = "54"
    """West Virginia."""
    US_WI = "55"
    """Wisconsin."""
    US_WY = "56"
    """Wyoming."""
    US_AS = "60"
    """American Samoa."""
    US_GU = "66"
    """Guam."""
    US_MP = "69"
    """Northern Mariana Islands."""
    US_PR = "72"
    """Puerto Rico."""
    US_VI = "78"
    """Virgin Islands."""

    # Canada -- provinces alphabetically, then the territories. CA06 is unused.
    CA_AB = "CA01"
    """Alberta."""
    CA_BC = "CA02"
    """British Columbia."""
    CA_MB = "CA03"
    """Manitoba."""
    CA_NB = "CA04"
    """New Brunswick."""
    CA_NL = "CA05"
    """Newfoundland. RepeaterBook omits "and Labrador"."""
    CA_NS = "CA07"
    """Nova Scotia."""
    CA_ON = "CA08"
    """Ontario."""
    CA_PE = "CA09"
    """Prince Edward Island."""
    CA_QC = "CA10"
    """Quebec."""
    CA_SK = "CA11"
    """Saskatchewan."""
    CA_YT = "CA12"
    """Yukon Territory. RepeaterBook retains the pre-2003 name."""
    CA_NT = "CA13"
    """Northwest Territories."""
    CA_NU = "CA14"
    """Nunavut."""

    # Mexico -- INEGI alphabetical ordering.
    MX_AGU = "MX01"
    """Aguascalientes."""
    MX_BCN = "MX02"
    """Baja California."""
    MX_BCS = "MX03"
    """Baja California Sur."""
    MX_CAM = "MX04"
    """Campeche."""
    MX_CHP = "MX05"
    """Chiapas."""
    MX_CHH = "MX06"
    """Chihuahua."""
    MX_COA = "MX07"
    """Coahuila."""
    MX_COL = "MX08"
    """Colima."""
    MX_CMX = "MX09"
    """Mexico City. INEGI lists this as Distrito Federal."""
    MX_DUR = "MX10"
    """Durango."""
    MX_GUA = "MX11"
    """Guanajuato."""
    MX_GRO = "MX12"
    """Guerrero."""
    MX_HID = "MX13"
    """Hidalgo."""
    MX_JAL = "MX14"
    """Jalisco."""
    MX_MEX = "MX15"
    """Mexico, the state."""
    MX_MIC = "MX16"
    """Michoacan."""
    MX_MOR = "MX17"
    """Morelos."""
    MX_NAY = "MX18"
    """Nayarit."""
    MX_NLE = "MX19"
    """Nuevo Leon."""
    MX_OAX = "MX20"
    """Oaxaca."""
    MX_PUE = "MX21"
    """Puebla."""
    MX_QUE = "MX22"
    """Queretaro."""
    MX_ROO = "MX23"
    """Quintana Roo."""
    MX_SLP = "MX24"
    """San Luis Potosi."""
    MX_SIN = "MX25"
    """Sinaloa."""
    MX_SON = "MX26"
    """Sonora."""
    MX_TAB = "MX27"
    """Tabasco."""
    MX_TAM = "MX28"
    """Tamaulipas."""
    MX_TLA = "MX29"
    """Tlaxcala."""
    MX_VER = "MX30"
    """Veracruz."""
    MX_YUC = "MX31"
    """Yucatan."""
    MX_ZAC = "MX32"
    """Zacatecas."""


def state_country(state: NAState) -> str:
    """Return the country name a ``state_id`` belongs to.

    Used to reject a scope that pairs a subdivision with the wrong country,
    which the API would otherwise answer with an empty result set.
    """
    if state.name.startswith("CA_"):
        return "Canada"
    if state.name.startswith("MX_"):
        return "Mexico"
    return "United States"
