"""Tests for database module."""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING

import pytest

from repeaterbook.database import RepeaterBook
from repeaterbook.models import Repeater, Status, Use

if TYPE_CHECKING:
    from pathlib import Path as StdPath

from anyio import Path


@pytest.fixture
def sample_repeater() -> Repeater:
    """Create a sample Repeater for testing."""
    return Repeater(
        state_id="CA",
        repeater_id=123,
        frequency=Decimal("146.940000"),
        input_frequency=Decimal("146.340000"),
        pl_ctcss_uplink="100.0",
        pl_ctcss_tsq_downlink="100.0",
        location_nearest_city="Los Angeles",
        landmark="Downtown",
        region=None,
        country="United States",
        county="Los Angeles",
        state="California",
        latitude=Decimal("34.0522"),
        longitude=Decimal("-118.2437"),
        precise=True,
        callsign="W6ABC",
        use_membership=Use.OPEN,
        operational_status=Status.ON_AIR,
        ares=None,
        races=None,
        skywarn=None,
        canwarn=None,
        allstar_node=None,
        echolink_node=None,
        irlp_node=None,
        wires_node=None,
        dmr_capable=False,
        dmr_id=None,
        dmr_color_code=None,
        d_star_capable=False,
        nxdn_capable=False,
        apco_p_25_capable=False,
        p_25_nac=None,
        m17_capable=False,
        m17_can=None,
        tetra_capable=False,
        tetra_mcc=None,
        tetra_mnc=None,
        yaesu_system_fusion_capable=False,
        ysf_digital_id_uplink=None,
        ysf_digital_id_downlink=None,
        ysf_dsc=None,
        analog_capable=True,
        fm_bandwidth=Decimal(25),
        notes=None,
        last_update=date(2024, 1, 15),
    )


class TestRepeaterBookDatabase:
    """Tests for RepeaterBook database wrapper."""

    def test_database_path(self, tmp_path: StdPath) -> None:
        """database_path should return correct path."""
        rb = RepeaterBook(working_dir=Path(tmp_path))
        expected = Path(tmp_path) / "repeaterbook.db"
        assert rb.database_path == expected

    def test_database_uri(self, tmp_path: StdPath) -> None:
        """database_uri should return correct SQLite URI."""
        rb = RepeaterBook(working_dir=Path(tmp_path))
        assert str(rb.database_uri).startswith("sqlite:///")
        assert "repeaterbook.db" in rb.database_uri

    def test_custom_database_name(self, tmp_path: StdPath) -> None:
        """Custom database name should be used."""
        rb = RepeaterBook(working_dir=Path(tmp_path), database="custom.db")
        assert "custom.db" in str(rb.database_path)

    def test_init_db_creates_tables(self, tmp_path: StdPath) -> None:
        """init_db should create the database tables."""
        rb = RepeaterBook(working_dir=Path(tmp_path))
        rb.init_db()
        # Check that database file exists
        assert (tmp_path / "repeaterbook.db").exists()

    def test_populate_inserts_repeaters(
        self, tmp_path: StdPath, sample_repeater: Repeater
    ) -> None:
        """Populate should insert repeaters into the database."""
        rb = RepeaterBook(working_dir=Path(tmp_path))
        rb.populate([sample_repeater])

        # Query should return the repeater
        results = rb.query()
        assert len(results) == 1
        assert results[0].state_id == "CA"
        assert results[0].repeater_id == 123

    def test_populate_merges_duplicates(
        self, tmp_path: StdPath, sample_repeater: Repeater
    ) -> None:
        """Populate should merge (update) existing repeaters."""
        rb = RepeaterBook(working_dir=Path(tmp_path))

        # Insert initial repeater
        rb.populate([sample_repeater])

        # Modify and re-insert (same primary key)
        modified = Repeater(
            state_id=sample_repeater.state_id,
            repeater_id=sample_repeater.repeater_id,
            frequency=sample_repeater.frequency,
            input_frequency=sample_repeater.input_frequency,
            pl_ctcss_uplink=sample_repeater.pl_ctcss_uplink,
            pl_ctcss_tsq_downlink=sample_repeater.pl_ctcss_tsq_downlink,
            location_nearest_city="Updated City",  # Changed
            landmark=sample_repeater.landmark,
            region=sample_repeater.region,
            country=sample_repeater.country,
            county=sample_repeater.county,
            state=sample_repeater.state,
            latitude=sample_repeater.latitude,
            longitude=sample_repeater.longitude,
            precise=sample_repeater.precise,
            callsign=sample_repeater.callsign,
            use_membership=sample_repeater.use_membership,
            operational_status=sample_repeater.operational_status,
            ares=sample_repeater.ares,
            races=sample_repeater.races,
            skywarn=sample_repeater.skywarn,
            canwarn=sample_repeater.canwarn,
            allstar_node=sample_repeater.allstar_node,
            echolink_node=sample_repeater.echolink_node,
            irlp_node=sample_repeater.irlp_node,
            wires_node=sample_repeater.wires_node,
            dmr_capable=sample_repeater.dmr_capable,
            dmr_id=sample_repeater.dmr_id,
            dmr_color_code=sample_repeater.dmr_color_code,
            d_star_capable=sample_repeater.d_star_capable,
            nxdn_capable=sample_repeater.nxdn_capable,
            apco_p_25_capable=sample_repeater.apco_p_25_capable,
            p_25_nac=sample_repeater.p_25_nac,
            m17_capable=sample_repeater.m17_capable,
            m17_can=sample_repeater.m17_can,
            tetra_capable=sample_repeater.tetra_capable,
            tetra_mcc=sample_repeater.tetra_mcc,
            tetra_mnc=sample_repeater.tetra_mnc,
            yaesu_system_fusion_capable=sample_repeater.yaesu_system_fusion_capable,
            ysf_digital_id_uplink=sample_repeater.ysf_digital_id_uplink,
            ysf_digital_id_downlink=sample_repeater.ysf_digital_id_downlink,
            ysf_dsc=sample_repeater.ysf_dsc,
            analog_capable=sample_repeater.analog_capable,
            fm_bandwidth=sample_repeater.fm_bandwidth,
            notes=sample_repeater.notes,
            last_update=sample_repeater.last_update,
        )
        rb.populate([modified])

        # Should still have only 1 repeater
        results = rb.query()
        assert len(results) == 1
        assert results[0].location_nearest_city == "Updated City"

    def test_query_with_where_clause(
        self, tmp_path: StdPath, sample_repeater: Repeater
    ) -> None:
        """Query should filter with where clause."""
        rb = RepeaterBook(working_dir=Path(tmp_path))

        # Insert multiple repeaters with different states
        repeaters = [
            sample_repeater,
            Repeater(
                state_id="TX",
                repeater_id=456,
                frequency=Decimal("147.000"),
                input_frequency=Decimal("147.600"),
                pl_ctcss_uplink=None,
                pl_ctcss_tsq_downlink=None,
                location_nearest_city="Houston",
                landmark=None,
                region=None,
                country="United States",
                county=None,
                state="Texas",
                latitude=Decimal("29.7604"),
                longitude=Decimal("-95.3698"),
                precise=True,
                callsign="W5XYZ",
                use_membership=Use.OPEN,
                operational_status=Status.ON_AIR,
                ares=None,
                races=None,
                skywarn=None,
                canwarn=None,
                allstar_node=None,
                echolink_node=None,
                irlp_node=None,
                wires_node=None,
                dmr_capable=True,
                dmr_id="12345",
                dmr_color_code="1",
                d_star_capable=False,
                nxdn_capable=False,
                apco_p_25_capable=False,
                p_25_nac=None,
                m17_capable=False,
                m17_can=None,
                tetra_capable=False,
                tetra_mcc=None,
                tetra_mnc=None,
                yaesu_system_fusion_capable=False,
                ysf_digital_id_uplink=None,
                ysf_digital_id_downlink=None,
                ysf_dsc=None,
                analog_capable=True,
                fm_bandwidth=None,
                notes=None,
                last_update=date(2024, 1, 15),
            ),
        ]
        rb.populate(repeaters)

        # Query for CA only
        results = rb.query(Repeater.state_id == "CA")
        assert len(results) == 1
        assert results[0].state_id == "CA"

        # Query for DMR capable
        results = rb.query(Repeater.dmr_capable == True)  # noqa: E712
        assert len(results) == 1
        assert results[0].state_id == "TX"

    def test_query_empty_database(self, tmp_path: StdPath) -> None:
        """Query on empty database should return empty list."""
        rb = RepeaterBook(working_dir=Path(tmp_path))
        rb.init_db()
        results = rb.query()
        assert len(results) == 0
