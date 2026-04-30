from datetime import time
from types import SimpleNamespace
import time as time_module

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


def test_live_dashboard_reuses_short_lived_arrival_cache(monkeypatch):
    from app.services import dashboard_service
    from app.schemas.provider_models import BusArrival

    fetches = []

    class FakeBusArrivalProvider:
        def __init__(self, **kwargs):
            pass

        def fetch(self, stop_id):
            fetches.append(stop_id)
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
    monkeypatch.setattr(dashboard_service, 'SeoulSubwayArrivalProvider', FakeSubwayArrivalProvider)
    dashboard_service.clear_live_arrival_cache()

    first_bus, _, _ = dashboard_service._load_public_data_dashboard_data(profile)
    second_bus, _, _ = dashboard_service._load_public_data_dashboard_data(profile)

    assert len(first_bus) == 1
    assert len(second_bus) == 1
    assert fetches == ['219000644']


def test_live_dashboard_fetches_selected_stops_in_parallel(monkeypatch):
    from app.services import dashboard_service
    from app.schemas.provider_models import BusArrival

    class FakeBusArrivalProvider:
        def __init__(self, **kwargs):
            pass

        def fetch(self, stop_id):
            time_module.sleep(0.15)
            return [
                BusArrival(
                    route_id=f'route-{stop_id}',
                    route_name='1001',
                    stop_id=stop_id,
                    stop_name=f'정류장 {stop_id}',
                    arrival_in_sec=60,
                    arrival_message='1분 후',
                    is_last_bus=False,
                )
            ]

    class FakeSubwayArrivalProvider:
        def __init__(self, **kwargs):
            pass

        def fetch(self, station_name):
            time_module.sleep(0.15)
            return []

    profile = SimpleNamespace(
        stops=[
            SimpleNamespace(type='bus_stop', external_id='bus-1', name='정류장 bus-1'),
            SimpleNamespace(type='bus_stop', external_id='bus-2', name='정류장 bus-2'),
            SimpleNamespace(type='subway_station', external_id='subway-1', name='상계역'),
        ]
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
    monkeypatch.setattr(dashboard_service, 'SeoulSubwayArrivalProvider', FakeSubwayArrivalProvider)
    dashboard_service.clear_live_arrival_cache()

    started_at = time_module.perf_counter()
    bus, _, subway = dashboard_service._load_public_data_dashboard_data(profile)
    elapsed = time_module.perf_counter() - started_at

    assert len(bus) == 2
    assert subway == []
    assert elapsed < 0.35
