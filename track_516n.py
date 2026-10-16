import math
import os
import time
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

import requests
from dotenv import load_dotenv

load_dotenv()


# ============================================================
# CONFIGURATION
# ============================================================

BASE_URL = "https://api.olhovivo.sptrans.com.br/v2.1"
TOKEN = os.getenv("SPTRANS_TOKEN")

LINE_NUMBER = "516N"
LINE_TYPE = 10
DIRECTION = 1  # Terminal Principal -> Terminal Secundário

ORIGIN = (-23.694201, -46.646470)
DESTINATION = (-23.684193, -46.633013)

TRIP_DISTANCE_METERS = 2300

RADIUS_METERS = 40
POLL_INTERVAL_SECONDS = 10
MAX_POSITION_AGE_SECONDS = 180

TOKEN = os.getenv("SPTRANS_TOKEN")

SAO_PAULO_TZ = ZoneInfo("America/Sao_Paulo")

# The selected vehicle is stored in memory, not in a database.
vehicle_prefix = None
start_time = None
last_position = None
last_position_time = None
distance_meters = 0.0


# ============================================================
# HELPERS
# ============================================================

def now_utc():
    return datetime.now(timezone.utc)


def parse_timestamp(value):
    """Parse the API's ISO 8601 UTC capture timestamp."""
    if not value:
        return now_utc()

    return datetime.fromisoformat(
        value.replace("Z", "+00:00")
    )


def format_local(dt):
    return dt.astimezone(SAO_PAULO_TZ).strftime(
        "%Y-%m-%d %H:%M:%S %Z"
    )


def distance_between(point_a, point_b):
    """Haversine distance in meters between two GPS coordinates."""
    lat1, lon1 = point_a
    lat2, lon2 = point_b

    radius_earth = 6_371_000

    lat1, lon1, lat2, lon2 = map(
        math.radians, [lat1, lon1, lat2, lon2]
    )

    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(lat1)
        * math.cos(lat2)
        * math.sin(dlon / 2) ** 2
    )

    return 2 * radius_earth * math.asin(
        math.sqrt(a)
    )


def get_json(session, endpoint, params=None):
    response = session.get(
        f"{BASE_URL}/{endpoint}",
        params=params,
        timeout=20,
    )
    response.raise_for_status()
    return response.json()


# ============================================================
# AUTHENTICATION AND LINE DISCOVERY
# ============================================================

def authenticate(session):
    if not TOKEN:
        raise RuntimeError(
            "SPTRANS_TOKEN is not set. "
            "Export your API token before running the script."
        )

    response = session.post(
        f"{BASE_URL}/Login/Autenticar",
        params={"token": TOKEN},
        timeout=20,
    )
    response.raise_for_status()

    if response.json() is not True:
        raise RuntimeError(
            "SPTrans authentication failed."
        )

    print("Authentication successful.")


def find_line_code(session):
    lines = get_json(
        session,
        "Linha/Buscar",
        params={"termosBusca": LINE_NUMBER},
    )

    matches = [
        line for line in lines
        if line.get("lt") == LINE_NUMBER
        and line.get("tl") == LINE_TYPE
        and line.get("sl") == DIRECTION
    ]

    if not matches:
        print("Lines returned by the API:")
        for line in lines:
            print(line)

        raise RuntimeError(
            "Could not identify 516N-10 in direction 1. "
            "Check the line-search results."
        )

    line = matches[0]

    print(f"Line: {line.get('lt')}-{line.get('tl')}")
    print(f"Direction: {line.get('sl')}")
    print(f"Line code (cl): {line.get('cl')}")
    print(f"Circular: {line.get('lc')}")
    print(f"Origin label: {line.get('tp')}")
    print(f"Destination label: {line.get('ts')}")

    return line["cl"]


# ============================================================
# VEHICLE POSITIONS
# ============================================================

def get_line_vehicles(session, line_code):
    data = get_json(
        session,
        "Posicao/Linha",
        params={"codigoLinha": line_code},
    )

    return data.get("vs", [])


def get_fresh_position(vehicle):
    lat = vehicle.get("py")
    lon = vehicle.get("px")

    if lat is None or lon is None:
        return None

    timestamp = parse_timestamp(vehicle.get("ta"))
    age_seconds = (now_utc() - timestamp).total_seconds()

    if age_seconds > MAX_POSITION_AGE_SECONDS:
        return None

    return {
        "prefix": str(vehicle["p"]),
        "point": (float(lat), float(lon)),
        "timestamp": timestamp,
    }


# ============================================================
# TRACKING
# ============================================================

def main():
    global vehicle_prefix
    global start_time
    global last_position
    global last_position_time
    global distance_meters

    session = requests.Session()

    authenticate(session)
    line_code = find_line_code(session)

    print("\nWaiting for a bus near the origin...")
    print(f"Origin: {ORIGIN}")
    print(f"Destination: {DESTINATION}")
    print(f"Detection radius: {RADIUS_METERS} m")
    print("Press Ctrl+C to stop.\n")

    # Phase 1: Wait for a bus to enter the origin radius.
    while vehicle_prefix is None:
        vehicles = get_line_vehicles(session, line_code)

        for vehicle in vehicles:
            position = get_fresh_position(vehicle)

            if position is None:
                continue

            distance = distance_between(
                position["point"], ORIGIN
            )

            if distance <= RADIUS_METERS:
                vehicle_prefix = position["prefix"]
                start_time = position["timestamp"]
                last_position = position["point"]
                last_position_time = start_time

                print("\nTRIP STARTED")
                print(f"Vehicle prefix: {vehicle_prefix}")
                print(f"Start time: {format_local(start_time)}")
                print(f"Distance from origin: {distance:.1f} m")
                break

        if vehicle_prefix is None:
            print(
                f"[{format_local(now_utc())}] "
                "No vehicle detected near origin."
            )
            time.sleep(POLL_INTERVAL_SECONDS)

    # Phase 2: Follow only the selected vehicle.
    while True:
        vehicles = get_line_vehicles(session, line_code)

        vehicle = next(
            (
                item for item in vehicles
                if str(item.get("p")) == vehicle_prefix
            ),
            None,
        )

        if vehicle is None:
            print(
                f"Vehicle {vehicle_prefix} is not currently "
                "visible in the API. Waiting..."
            )
            time.sleep(POLL_INTERVAL_SECONDS)
            continue

        position = get_fresh_position(vehicle)

        if position is None:
            print("Position is missing or too old. Waiting...")
            time.sleep(POLL_INTERVAL_SECONDS)
            continue

        current_point = position["point"]
        current_time = position["timestamp"]

        segment_distance = distance_between(
            last_position, current_point
        )

        elapsed_since_last = (
            current_time - start_time
        ).total_seconds()

        # Ignore repeated or out-of-order timestamps.
        if current_time > last_position_time:
            distance_meters += segment_distance
            last_position = current_point
            last_position_time = current_time

        distance_to_destination = distance_between(
            current_point, DESTINATION
        )

        elapsed_seconds = (
            current_time - start_time
        ).total_seconds()

        print(
            f"Vehicle {vehicle_prefix} | "
            f"position={current_point} | "
            f"destination_distance={distance_to_destination:.1f} m | "
            f"elapsed={elapsed_seconds / 60:.1f} min"
        )

        if distance_to_destination <= RADIUS_METERS:
            if elapsed_seconds <= 0:
                raise RuntimeError(
                    "Invalid timestamps; trip duration cannot "
                    "be calculated."
                )

            average_speed_kmh = (
                TRIP_DISTANCE_METERS / elapsed_seconds
            ) * 3.6

            print("\nTRIP COMPLETED")
            print(f"Vehicle prefix: {vehicle_prefix}")
            print(f"Start: {format_local(start_time)}")
            print(f"Arrival: {format_local(current_time)}")
            print(
                f"Elapsed time: "
                f"{elapsed_seconds / 60:.2f} minutes"
            )
            print(
                f"Estimated GPS distance: "
                f"{distance_meters / 1000:.3f} km"
            )
            print(
                f"Estimated average speed: "
                f"{average_speed_kmh:.2f} km/h"
            )
            break

        time.sleep(POLL_INTERVAL_SECONDS)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nTracking stopped by user.")
    except requests.RequestException as exc:
        print(f"\nAPI/network error: {exc}")
    except (RuntimeError, ValueError, KeyError) as exc:
        print(f"\nError: {exc}")
