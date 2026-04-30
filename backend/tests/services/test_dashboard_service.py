from datetime import time
from types import SimpleNamespace

from app.db.session import SessionLocal
from app.models.commute_profile import CommuteProfile
from app.models.commute_stop import CommuteStop
from app.services.dashboard_service import build_dashboard
from app.services.profile_store import add_stop, create_profile, get_profile


def test_dashboard_uses_selected_stop_types_to_filter_results():
    session = SessionLocal()
    try:
        profile = create_profile(
            session,
            CommuteProfile(
                name='회사 가기',
                origin_label='집',
                destination_label='회사',
                target_arrival_time=time(hour=9),
            ),
        )
        add_stop(
            session,
            profile.id,
            CommuteStop(
                type='subway_station',
                external_id='1004000409',
                name='상계역',
                line_name='4호선',
                direction='오이도방향',
                sort_order=1,
            ),
        )

        dashboard = build_dashboard(get_profile(session, profile.id))
    finally:
        session.close()

    assert dashboard.bus == []
    assert dashboard.bus_positions == []
    assert len(dashboard.subway) == 1
    assert dashboard.subway[0].station_name == '상계역'


def test_live_dashboard_skips_unused_bus_position_fetches(monkeypatch):
    from app.services import dashboard_service
    from app.schemas.provider_models import BusArrival

    position_fetches = []

    class FakeBusArrivalProvider:
        def __init__(self, **kwargs):
            pass

        def fetch(self, stop_id):
            return [
                BusArrival(
                    route_id='route-1',
                    route_name='1001',
                    stop_id=stop_id,
                    stop_name='고양공영차고지',
                    arrival_in_sec=60,
                    arrival_message='1분 후',
                    is_last_bus=False,
                )
            ]

    class FakeBusPositionProvider:
        def __init__(self, **kwargs):
            pass

        def fetch(self, route_id):
            position_fetches.append(route_id)
            return []

    class FakeSubwayArrivalProvider:
        def __init__(self, **kwargs):
            pass

        def fetch(self, station_name):
            return []

    profile = SimpleNamespace(
        stops=[SimpleNamespace(type='bus_stop', external_id='219000644', name='고양공영차고지')]
    )

    monkeypatch.setattr(
        dashboard_service,
        'get_settings',
        lambda: SimpleNamespace(
            public_data_service_key='public',
            seoul_open_api_key='',
            allow_insecure_seoul_transit_http=False,
        ),
    )
    monkeypatch.setattr(dashboard_service, 'SeoulBusArrivalProvider', FakeBusArrivalProvider)
    monkeypatch.setattr(dashboard_service, 'SeoulBusPositionProvider', FakeBusPositionProvider)
    monkeypatch.setattr(dashboard_service, 'SeoulSubwayArrivalProvider', FakeSubwayArrivalProvider)

    bus, bus_positions, subway = dashboard_service._load_public_data_dashboard_data(profile)

    assert len(bus) == 1
    assert bus_positions == []
    assert subway == []
    assert position_fetches == []
