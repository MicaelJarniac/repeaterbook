# Examples

Real-world examples of using **RepeaterBook** for common amateur radio tasks.

## Example 1: Build a Repeater Directory Website

Create a web-based repeater directory with search functionality.

```python
import asyncio
from flask import Flask, jsonify, request
from repeaterbook import RepeaterBook, Repeater
from repeaterbook.services import RepeaterBookAPI
from repeaterbook.models import ExportQuery, Status
from repeaterbook.queries import square, filter_radius, band, Bands
from repeaterbook.utils import LatLon, Radius
import pycountry

app = Flask(__name__)
rb = RepeaterBook("repeaters.db")

async def initialize_database():
    """Download and populate database on startup."""
    api = RepeaterBookAPI()

    # Download data for multiple countries
    countries = [
        pycountry.countries.get(alpha_2="US"),
        pycountry.countries.get(alpha_2="CA"),
        pycountry.countries.get(alpha_2="MX"),
    ]

    all_repeaters = []
    for country in countries:
        repeaters = await api.download(
            query=ExportQuery(countries={country})
        )
        all_repeaters.extend(repeaters)

    rb.populate(all_repeaters)
    print(f"Database initialized with {len(all_repeaters)} repeaters")

@app.route('/api/search')
def search_repeaters():
    """Search repeaters by location and filters."""
    # Get query parameters
    lat = float(request.args.get('lat'))
    lon = float(request.args.get('lon'))
    distance = float(request.args.get('distance', 50))
    mode = request.args.get('mode')  # 'dmr', 'p25', 'nxdn', 'analog'
    band_filter = request.args.get('band')  # '2m', '70cm', etc.

    # Build query
    radius = Radius(origin=LatLon(lat=lat, lon=lon), distance=distance)
    conditions = [
        square(radius),
        Repeater.operational_status == Status.ON_AIR
    ]

    # Add mode filter
    if mode == 'dmr':
        conditions.append(Repeater.dmr_capable == True)
    elif mode == 'p25':
        conditions.append(Repeater.apco_p_25_capable == True)
    elif mode == 'nxdn':
        conditions.append(Repeater.nxdn_capable == True)

    # Add band filter
    if band_filter == '2m':
        conditions.append(band(Bands.M_2))
    elif band_filter == '70cm':
        conditions.append(band(Bands.CM_70))

    # Execute query
    results = rb.query(*conditions)
    nearby = filter_radius(results, radius)

    # filter_radius returns repeaters sorted by distance
    # Limit to first 50 results
    sorted_results = nearby[:50]

    # Convert to JSON
    from haversine import haversine
    return jsonify([{
        'callsign': r.callsign,
        'frequency': r.frequency,
        'location': r.location_nearest_city,
        'distance': round(haversine(radius.origin, (r.latitude, r.longitude), unit=radius.unit), 2),
        'ctcss': r.pl_ctcss_uplink,
        'dmr': r.dmr_capable,
        'dmr_id': r.dmr_id,
        'dmr_cc': r.dmr_color_code,
    } for r in sorted_results])

if __name__ == '__main__':
    # Initialize database
    asyncio.run(initialize_database())

    # Start server
    app.run(debug=True)
```

## Example 2: Generate Codeplug for DMR Radio

Create a CSV file for importing into a DMR radio codeplug.

```python
import asyncio
import csv
from repeaterbook import RepeaterBook, Repeater
from repeaterbook.services import RepeaterBookAPI
from repeaterbook.models import ExportQuery, Status, Use
from repeaterbook.queries import square, filter_radius, band, Bands
from repeaterbook.utils import LatLon, Radius
import pycountry

async def generate_codeplug():
    """Generate DMR codeplug from RepeaterBook data."""

    # Download California repeaters
    api = RepeaterBookAPI()
    usa = pycountry.countries.get(alpha_2="US")
    repeaters = await api.download(
        query=ExportQuery(countries={usa}, state_ids={"California"})
    )

    # Store in database
    rb = RepeaterBook()
    rb.populate(repeaters)

    # Find DMR repeaters near San Francisco
    sf = LatLon(lat=37.7749, lon=-122.4194)
    radius = Radius(origin=sf, distance=100)

    dmr_repeaters = rb.query(
        square(radius),
        Repeater.dmr_capable == True,
        Repeater.operational_status == Status.ON_AIR,
        Repeater.use_membership == Use.OPEN,
        band(Bands.CM_70)  # 70cm only
    )

    nearby_dmr = filter_radius(dmr_repeaters, radius)
    # filter_radius returns repeaters sorted by distance

    # Generate CSV for Anytone/TYT radios
    with open('dmr_codeplug.csv', 'w', newline='') as f:
        writer = csv.writer(f)

        # Header row
        writer.writerow([
            'No.', 'Channel Name', 'Receive Frequency', 'Transmit Frequency',
            'Channel Type', 'Transmit Power', 'Band Width', 'CTCSS/DCS Decode',
            'CTCSS/DCS Encode', 'Contact', 'Contact Call Type', 'Radio ID',
            'Busy Lock/TX Permit', 'Squelch Mode', 'Optional Signal',
            'DTMF ID', 'Color Code', 'Slot', 'Scan List', 'Group List',
            'GPS System', 'Emergency System'
        ])

        # Data rows
        for idx, rep in enumerate(nearby_dmr[:100], start=1):
            # Calculate offset
            offset = rep.frequency - rep.input_frequency

            # Channel name
            name = f"{rep.callsign} {rep.location_nearest_city[:20]}"

            writer.writerow([
                idx,                          # No.
                name,                         # Channel Name
                f"{rep.frequency:.5f}",       # Receive Frequency
                f"{rep.input_frequency:.5f}", # Transmit Frequency
                'D-Digital',                  # Channel Type
                'High',                       # Transmit Power
                '12.5K',                      # Band Width
                f"{rep.pl_ctcss_uplink:.1f}" if rep.pl_ctcss_uplink else '',  # CTCSS Decode
                f"{rep.pl_ctcss_uplink:.1f}" if rep.pl_ctcss_uplink else '',  # CTCSS Encode
                'Worldwide',                  # Contact
                'Group Call',                 # Contact Call Type
                'None',                       # Radio ID
                'Always',                     # Busy Lock/TX Permit
                'Carrier',                    # Squelch Mode
                'Off',                        # Optional Signal
                '1',                          # DTMF ID
                rep.dmr_color_code or 1,      # Color Code
                '2',                          # Slot (usually TS2 for Worldwide)
                'All',                        # Scan List
                'Worldwide',                  # Group List
                'None',                       # GPS System
                'None'                        # Emergency System
            ])

    print(f"Generated codeplug with {len(nearby_dmr[:100])} channels")
    print(f"Import dmr_codeplug.csv into your radio programming software")

if __name__ == '__main__':
    asyncio.run(generate_codeplug())
```

## Example 3: Repeater Coverage Map

Generate a heatmap of repeater coverage using folium.

```python
import asyncio
import folium
from folium.plugins import HeatMap
from repeaterbook import RepeaterBook, Repeater
from repeaterbook.services import RepeaterBookAPI
from repeaterbook.models import ExportQuery, Status
import pycountry

async def create_coverage_map():
    """Create an interactive map of repeater locations."""

    # Download repeater data
    api = RepeaterBookAPI()
    uk = pycountry.countries.get(alpha_2="GB")
    repeaters = await api.download(query=ExportQuery(countries={uk}))

    # Store in database
    rb = RepeaterBook()
    rb.populate(repeaters)

    # Get operational repeaters
    operational = rb.query(Repeater.operational_status == Status.ON_AIR)

    # Create base map centered on UK
    m = folium.Map(
        location=[54.5, -4.0],
        zoom_start=6,
        tiles='OpenStreetMap'
    )

    # Add markers for each repeater
    for rep in operational:
        # Determine icon color by mode
        if rep.dmr_capable:
            color = 'blue'
            icon = 'info-sign'
        elif rep.apco_p_25_capable:
            color = 'green'
            icon = 'info-sign'
        elif rep.nxdn_capable:
            color = 'orange'
            icon = 'info-sign'
        else:
            color = 'red'
            icon = 'record'

        # Create popup with repeater info
        popup_html = f"""
        <div style="width:200px">
            <h4>{rep.callsign}</h4>
            <p><b>Frequency:</b> {rep.frequency:.4f} MHz</p>
            <p><b>Location:</b> {rep.location_nearest_city}</p>
            <p><b>Input Tone:</b> {rep.pl_ctcss_uplink or 'None'}</p>
            <p><b>Use:</b> {rep.use_membership.value}</p>
        </div>
        """

        folium.Marker(
            location=[rep.latitude, rep.longitude],
            popup=folium.Popup(popup_html, max_width=250),
            tooltip=rep.callsign,
            icon=folium.Icon(color=color, icon=icon)
        ).add_to(m)

    # Add heatmap layer
    heat_data = [[r.latitude, r.longitude] for r in operational]
    HeatMap(heat_data, radius=15).add_to(m)

    # Save map
    m.save('repeater_coverage.html')
    print("Map saved to repeater_coverage.html")

if __name__ == '__main__':
    asyncio.run(create_coverage_map())
```

## Example 4: Repeater Statistics Dashboard

Analyze repeater data and generate statistics.

```python
import asyncio
import pandas as pd
import matplotlib.pyplot as plt
from repeaterbook import RepeaterBook, Repeater
from repeaterbook.services import RepeaterBookAPI
from repeaterbook.models import ExportQuery
import pycountry

async def generate_statistics():
    """Generate statistics and visualizations from repeater data."""

    # Download data for multiple European countries
    api = RepeaterBookAPI()
    countries = [
        pycountry.countries.get(name="Germany"),
        pycountry.countries.get(name="France"),
        pycountry.countries.get(name="Italy"),
        pycountry.countries.get(name="Spain"),
        pycountry.countries.get(name="United Kingdom"),
    ]

    all_repeaters = []
    for country in countries:
        repeaters = await api.download(query=ExportQuery(countries={country}))
        all_repeaters.extend(repeaters)

    # Store in database
    rb = RepeaterBook()
    rb.populate(all_repeaters)

    # Query all repeaters
    all_data = rb.query()

    # Convert to DataFrame
    df = pd.DataFrame([r.model_dump() for r in all_data])

    # Statistics
    print("=== Repeater Statistics ===\n")

    print(f"Total Repeaters: {len(df)}")
    print(f"\nBy Status:")
    print(df['operational_status'].value_counts())

    print(f"\nBy Use/Membership:")
    print(df['use_membership'].value_counts())

    print(f"\nDigital Mode Capabilities:")
    print(f"DMR: {df['dmr_capable'].sum()}")
    print(f"P25: {df['apco_p_25_capable'].sum()}")
    print(f"NXDN: {df['nxdn_capable'].sum()}")
    print(f"Analog: {df['analog_capable'].sum()}")

    # Visualizations
    fig, axes = plt.subplots(2, 2, figsize=(12, 10))

    # 1. Frequency distribution
    df['frequency'].hist(bins=50, ax=axes[0, 0])
    axes[0, 0].set_title('Frequency Distribution')
    axes[0, 0].set_xlabel('Frequency (MHz)')
    axes[0, 0].set_ylabel('Count')

    # 2. Status pie chart
    df['operational_status'].value_counts().plot.pie(
        ax=axes[0, 1],
        autopct='%1.1f%%',
        title='Operational Status'
    )

    # 3. Digital modes bar chart
    modes = {
        'DMR': df['dmr_capable'].sum(),
        'P25': df['apco_p_25_capable'].sum(),
        'NXDN': df['nxdn_capable'].sum(),
        'Analog': df['analog_capable'].sum(),
    }
    pd.Series(modes).plot.bar(ax=axes[1, 0], title='Mode Capabilities')
    axes[1, 0].set_ylabel('Count')

    # 4. Access type distribution
    df['use_membership'].value_counts().plot.bar(
        ax=axes[1, 1],
        title='Access Type'
    )
    axes[1, 1].set_ylabel('Count')

    plt.tight_layout()
    plt.savefig('repeater_statistics.png', dpi=300)
    print("\nStatistics chart saved to repeater_statistics.png")

if __name__ == '__main__':
    asyncio.run(generate_statistics())
```

## Example 5: Travel Planner

Find repeaters along a route for road trips.

```python
import asyncio
from typing import List
from repeaterbook import RepeaterBook, Repeater
from repeaterbook.services import RepeaterBookAPI
from repeaterbook.models import ExportQuery, Status, Use
from repeaterbook.queries import filter_radius, square, band, Bands
from repeaterbook.utils import LatLon, Radius
import pycountry

class TravelPlanner:
    """Find repeaters along a travel route."""

    def __init__(self, rb: RepeaterBook):
        self.rb = rb

    def find_along_route(
        self,
        waypoints: List[LatLon],
        search_distance: float = 50,
        preferred_band: Bands = Bands.M_2,
        dmr_only: bool = False
    ) -> dict:
        """Find repeaters along a route."""

        results = {}

        for idx, waypoint in enumerate(waypoints):
            print(f"Searching around waypoint {idx + 1}...")

            # Build query
            radius = Radius(origin=waypoint, distance=search_distance)
            conditions = [
                square(radius),
                Repeater.operational_status == Status.ON_AIR,
                Repeater.use_membership == Use.OPEN,
                band(preferred_band)
            ]

            if dmr_only:
                conditions.append(Repeater.dmr_capable == True)

            # Execute query
            candidates = self.rb.query(*conditions)
            nearby = filter_radius(candidates, radius)

            # filter_radius returns repeaters sorted by distance
            # Take top 5 closest
            closest_repeaters = nearby[:5]

            results[f"Waypoint {idx + 1}"] = {
                'location': waypoint,
                'repeaters': closest_repeaters
            }

        return results

    def generate_report(self, results: dict) -> str:
        """Generate a text report of repeaters along route."""

        report = ["=" * 80]
        report.append("REPEATER TRAVEL PLAN")
        report.append("=" * 80)

        for waypoint_name, data in results.items():
            report.append(f"\n{waypoint_name}:")
            report.append(f"Location: {data['location']}")
            report.append(f"\nTop Repeaters:")

            for rep in data['repeaters']:
                # Calculate distance for display
                from haversine import haversine
                distance = haversine(data['location'], (rep.latitude, rep.longitude))
                report.append(f"\n  {rep.callsign} - {rep.frequency:.4f} MHz")
                report.append(f"  Location: {rep.location_nearest_city}")
                report.append(f"  Distance: {distance:.1f} km")
                if rep.pl_ctcss_uplink:
                    report.append(f"  Tone: {rep.pl_ctcss_uplink} Hz")
                if rep.dmr_capable:
                    report.append(f"  DMR: CC{rep.dmr_color_code}, ID {rep.dmr_id}")
                report.append(f"  Notes: {rep.notes or 'None'}")

            report.append("-" * 80)

        return "\n".join(report)

async def plan_road_trip():
    """Plan repeater coverage for a road trip."""

    # Download repeater data
    api = RepeaterBookAPI()
    usa = pycountry.countries.get(alpha_2="US")
    states = {"California", "Nevada", "Arizona", "Utah"}

    print("Downloading repeater data...")
    repeaters = await api.download(
        query=ExportQuery(countries={usa}, state_ids=states)
    )

    # Initialize database
    rb = RepeaterBook()
    rb.populate(repeaters)

    # Define route (San Francisco to Las Vegas to Phoenix)
    route = [
        LatLon(lat=37.7749, lon=-122.4194),  # San Francisco
        LatLon(lat=39.5296, lon=-119.8138),  # Reno
        LatLon(lat=36.1699, lon=-115.1398),  # Las Vegas
        LatLon(lat=33.4484, lon=-112.0740),  # Phoenix
    ]

    # Create planner
    planner = TravelPlanner(rb)

    # Find repeaters along route
    print("\nFinding repeaters along route...")
    results = planner.find_along_route(
        waypoints=route,
        search_distance=50,
        preferred_band=Bands.M_2,
        dmr_only=False
    )

    # Generate and save report
    report = planner.generate_report(results)
    print(report)

    with open('travel_plan.txt', 'w') as f:
        f.write(report)

    print("\nReport saved to travel_plan.txt")

if __name__ == '__main__':
    asyncio.run(plan_road_trip())
```

## Example 6: Emergency Communications Planning

Identify repeaters with emergency capabilities.

```python
import asyncio
from repeaterbook import RepeaterBook, Repeater
from repeaterbook.services import RepeaterBookAPI
from repeaterbook.models import ExportQuery, Status, Use
from repeaterbook.queries import square, filter_radius
from repeaterbook.utils import LatLon, Radius
import pycountry

async def emergency_planning():
    """Identify emergency communication resources."""

    # Download state data
    api = RepeaterBookAPI()
    usa = pycountry.countries.get(alpha_2="US")
    repeaters = await api.download(
        query=ExportQuery(countries={usa}, state_ids={"Florida"})
    )

    # Initialize database
    rb = RepeaterBook()
    rb.populate(repeaters)

    # Find emergency-capable repeaters (ARES/RACES/SKYWARN)
    emergency_repeaters = rb.query(
        Repeater.operational_status == Status.ON_AIR,
        (Repeater.ares == True) | (Repeater.races == True) | (Repeater.skywarn == True),
        Repeater.use_membership.in_([Use.OPEN, Use.PRIVATE])
    )

    print(f"Found {len(emergency_repeaters)} emergency-capable repeaters\n")

    # Group by county/location
    by_location = {}
    for rep in emergency_repeaters:
        location = rep.location_nearest_city
        if location not in by_location:
            by_location[location] = []
        by_location[location].append(rep)

    # Generate report
    print("=" * 80)
    print("EMERGENCY COMMUNICATIONS RESOURCES")
    print("=" * 80)

    for location, reps in sorted(by_location.items()):
        print(f"\n{location}:")
        for rep in sorted(reps, key=lambda r: r.frequency):
            print(f"  {rep.callsign:10s} {rep.frequency:8.4f} MHz", end="")
            if rep.pl_ctcss_uplink:
                print(f"  Tone: {rep.pl_ctcss_uplink:6.1f}", end="")
            print(f"  Use: {rep.use_membership.value}")
            if rep.notes:
                print(f"    Notes: {rep.notes}")

    # Find repeaters near major cities
    print("\n" + "=" * 80)
    print("COVERAGE NEAR MAJOR CITIES")
    print("=" * 80)

    cities = {
        "Miami": LatLon(lat=25.7617, lon=-80.1918),
        "Tampa": LatLon(lat=27.9506, lon=-82.4572),
        "Orlando": LatLon(lat=28.5383, lon=-81.3792),
        "Jacksonville": LatLon(lat=30.3322, lon=-81.6557),
    }

    for city_name, city_loc in cities.items():
        radius = Radius(origin=city_loc, distance=25)
        candidates = rb.query(
            square(radius),
            Repeater.operational_status == Status.ON_AIR,
            (Repeater.ares == True) | (Repeater.races == True) | (Repeater.skywarn == True)
        )
        nearby = filter_radius(candidates, radius)

        print(f"\n{city_name}: {len(nearby)} emergency repeaters within 25km")

if __name__ == '__main__':
    asyncio.run(emergency_planning())
```

## Example 7: Network Analysis

Analyze repeater networks (Brandmeister, DMR-MARC, etc.).

```python
import asyncio
from collections import Counter
from repeaterbook import RepeaterBook, Repeater
from repeaterbook.services import RepeaterBookAPI
from repeaterbook.models import ExportQuery
import pycountry

async def analyze_networks():
    """Analyze DMR network distribution."""

    # Download data
    api = RepeaterBookAPI()
    usa = pycountry.countries.get(alpha_2="US")
    repeaters = await api.download(query=ExportQuery(countries={usa}))

    rb = RepeaterBook()
    rb.populate(repeaters)

    # Get DMR repeaters
    dmr_repeaters = rb.query(Repeater.dmr_capable == True)

    # Count by network
    networks = Counter(r.network for r in dmr_repeaters if r.network)

    print("=" * 80)
    print("DMR NETWORK DISTRIBUTION")
    print("=" * 80)
    print(f"\nTotal DMR Repeaters: {len(dmr_repeaters)}")
    print(f"\nTop 10 Networks:")

    for network, count in networks.most_common(10):
        percentage = (count / len(dmr_repeaters)) * 100
        print(f"  {network:30s} {count:5d} ({percentage:5.1f}%)")

    # Find most popular color codes
    color_codes = Counter(r.dmr_color_code for r in dmr_repeaters if r.dmr_color_code)

    print(f"\nColor Code Distribution:")
    for cc, count in sorted(color_codes.items()):
        percentage = (count / len(dmr_repeaters)) * 100
        bar = "█" * int(percentage)
        print(f"  CC{cc:2d}: {bar} {count:4d} ({percentage:5.1f}%)")

if __name__ == '__main__':
    asyncio.run(analyze_networks())
```

## Next Steps

- [Getting Started](getting-started.md) - Tutorial for beginners
- [Usage Guide](usage.md) - Comprehensive usage examples
- [Architecture](architecture.md) - Understanding the internals
- [API Reference](api.md) - Complete API documentation
- [FAQ](faq.md) - Common questions and troubleshooting
