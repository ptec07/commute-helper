from __future__ import annotations

from pathlib import Path

from app.schemas.dashboard import DashboardResponse
from app.schemas.profile import CommuteProfileRead
from app.services.providers.seoul_bus_arrival import SeoulBusArrivalProvider
from app.services.providers.seoul_bus_position import SeoulBusPositionProvider
from app.services.providers.seoul_subway_arrival import SeoulSubwayArrivalProvider
from app.services.recommendation_service import recommend_mode

FIXTURES = Path(__file__).resolve().parents[2] / 'tests' / 'fixtures'


def build_dashboard(profile) -> DashboardResponse:
    bus_provider = SeoulBusArrivalProvider(service_key='dummy')
    position_provider = SeoulBusPositionProvider(service_key='dummy')
    subway_provider = SeoulSubwayArrivalProvider(service_key='dummy')

    all_bus = bus_provider.parse((FIXTURES / 'seoul_bus_arrival.xml').read_text(encoding='utf-8'))
    all_bus_positions = position_provider.parse((FIXTURES / 'seoul_bus_position.json').read_text(encoding='utf-8'))
    all_subway = subway_provider.parse((FIXTURES / 'seoul_subway_arrival.xml').read_text(encoding='utf-8'))

    selected_bus_names = {stop.name for stop in profile.stops if stop.type == 'bus_stop'}
    selected_subway_names = {stop.name for stop in profile.stops if stop.type == 'subway_station'}
    has_selected_stops = bool(profile.stops)

    if selected_bus_names:
        bus = [item for item in all_bus if item.stop_name in selected_bus_names]
        selected_route_ids = {item.route_id for item in bus}
        bus_positions = [item for item in all_bus_positions if item.route_id in selected_route_ids]
    elif has_selected_stops:
        bus = []
        bus_positions = []
    else:
        bus = all_bus
        bus_positions = all_bus_positions

    if selected_subway_names:
        subway = [item for item in all_subway if item.station_name in selected_subway_names]
    elif has_selected_stops:
        subway = []
    else:
        subway = all_subway

    recommendation = recommend_mode(
        bus=bus,
        subway=subway,
        preferred_mode=profile.preferred_mode,
        target_arrival_time=profile.target_arrival_time.isoformat(),
    )

    return DashboardResponse(
        profile=CommuteProfileRead.model_validate(profile),
        bus=bus,
        bus_positions=bus_positions,
        subway=subway,
        recommendation=recommendation,
    )
