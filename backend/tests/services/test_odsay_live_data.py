from datetime import datetime, time

import httpx

from app.models.commute_profile import CommuteProfile
from app.models.commute_stop import CommuteStop
from app.schemas.provider_models import BusArrival, SubwayArrival
from app.services.dashboard_service import build_dashboard
from app.services.providers.odsay_bus_arrival import ODsayBusArrivalProvider
from app.services.providers.odsay_bus_position import ODsayBusPositionProvider
from app.services.providers.odsay_subway_arrival import ODsaySubwayArrivalProvider


class DummyResponse:
    def __init__(self, payload: dict):
        self._payload = payload
        self.text = ''

    def raise_for_status(self) -> None:
        return None

    def json(self) -> dict:
        return self._payload


def test_odsay_bus_arrival_provider_fetches_station_routes_as_arrivals(monkeypatch):
    calls = []

    def fake_get(url: str, *, params: dict[str, str], timeout: float):
        calls.append((url, params))
        if url.endswith('/searchStation'):
            return DummyResponse(
                {
                    'result': {
                        'station': [
                            {
                                'stationClass': 1,
                                'stationName': '상계주공7단지',
                                'stationID': 107475,
                                'localStationID': '200000123',
                                'arsID': '12345',
                            }
                        ]
                    }
                }
            )
        if url.endswith('/busStationInfo'):
            return DummyResponse(
                {
                    'result': {
                        'stationName': '상계주공7단지',
                        'localStationID': '200000123',
                        'lane': [
                            {
                                'busNo': '146',
                                'busLocalBlID': '100100118',
                                'busInterval': '8',
                                'busFirstTime': '04:30',
                                'busLastTime': '23:50',
                            }
                        ],
                    }
                }
            )
        raise AssertionError(f'unexpected url: {url}')

    monkeypatch.setattr(httpx, 'get', fake_get)

    provider = ODsayBusArrivalProvider(api_key='odsay-live-key')
    arrivals = provider.fetch(stop_name='상계주공7단지', stop_local_id='200000123')

    assert calls[0][0] == 'https://api.odsay.com/v1/api/searchStation'
    assert calls[1][0] == 'https://api.odsay.com/v1/api/busStationInfo'
    assert arrivals == [
        BusArrival(
            route_id='100100118',
            route_name='146',
            stop_id='200000123',
            stop_name='상계주공7단지',
            arrival_in_sec=480,
            arrival_message='약 8분 간격 운행',
            is_last_bus=False,
        )
    ]


def test_odsay_subway_arrival_provider_returns_next_departure(monkeypatch):
    calls = []

    def fake_get(url: str, *, params: dict[str, str], timeout: float):
        calls.append((url, params))
        if url.endswith('/searchStation'):
            return DummyResponse(
                {
                    'result': {
                        'station': [
                            {
                                'stationClass': 2,
                                'stationName': '상계역',
                                'stationID': 130,
                                'laneName': '4호선',
                            }
                        ]
                    }
                }
            )
        if url.endswith('/searchSubwaySchedule'):
            return DummyResponse(
                {
                    'result': {
                        'stationName': '상계역',
                        'stationID': 130,
                        'laneName': '4호선',
                        'weekdaySchedule': {
                            'up': [
                                {
                                    'subwayClass': 0,
                                    'departureTime': '08:17',
                                    'endStationName': '오이도',
                                },
                                {
                                    'subwayClass': 1,
                                    'departureTime': '08:25',
                                    'endStationName': '오이도',
                                },
                            ],
                            'down': [],
                        },
                        'saturdaySchedule': {'up': [], 'down': []},
                        'holidaySchedule': {'up': [], 'down': []},
                    }
                }
            )
        raise AssertionError(f'unexpected url: {url}')

    monkeypatch.setattr(httpx, 'get', fake_get)

    provider = ODsaySubwayArrivalProvider(
        api_key='odsay-live-key',
        now_provider=lambda: datetime(2026, 4, 27, 8, 10, 0),
    )
    arrivals = provider.fetch(station_name='상계역', line_name='4호선')

    assert calls[0][0] == 'https://api.odsay.com/v1/api/searchStation'
    assert calls[1][0] == 'https://api.odsay.com/v1/api/searchSubwaySchedule'
    assert arrivals == [
        SubwayArrival(
            station_id='130',
            station_name='상계역',
            line_name='4호선',
            direction='오이도',
            arrival_in_sec=420,
            train_type='general',
        ),
        SubwayArrival(
            station_id='130',
            station_name='상계역',
            line_name='4호선',
            direction='오이도',
            arrival_in_sec=900,
            train_type='express',
        ),
    ]


def test_dashboard_uses_odsay_live_data_when_configured(monkeypatch):
    profile = CommuteProfile(
        id='profile-odsay-live-1',
        name='회사 가기',
        origin_label='집',
        destination_label='회사',
        target_arrival_time=time(hour=9),
        preferred_mode='balanced',
        walking_tolerance_min=10,
        created_at=datetime(2026, 4, 24, 9, 0, 0),
        updated_at=datetime(2026, 4, 24, 9, 0, 0),
    )
    profile.stops = [
        CommuteStop(
            id='stop-bus-1',
            type='bus_stop',
            external_id='200000123',
            name='상계주공7단지',
            sort_order=1,
        ),
        CommuteStop(
            id='stop-subway-1',
            type='subway_station',
            external_id='1004000409',
            name='상계역',
            line_name='4호선',
            direction='오이도방향',
            sort_order=2,
        ),
    ]

    monkeypatch.setattr(
        'app.services.dashboard_service.get_settings',
        lambda: type(
            'Settings',
            (),
            {
                'use_live_public_data': True,
                'odsay_api_key': 'odsay-live-key',
            },
        )(),
    )

    monkeypatch.setattr(
        ODsayBusArrivalProvider,
        'fetch',
        lambda self, stop_name, stop_local_id=None: [
            BusArrival(
                route_id='100100118',
                route_name='146',
                stop_id='200000123',
                stop_name='상계주공7단지',
                arrival_in_sec=240,
                arrival_message='4분 후 도착',
                is_last_bus=False,
            )
        ],
    )
    monkeypatch.setattr(ODsayBusPositionProvider, 'fetch', lambda self, route_id: [])
    monkeypatch.setattr(
        ODsaySubwayArrivalProvider,
        'fetch',
        lambda self, station_name, line_name=None: [
            SubwayArrival(
                station_id='130',
                station_name='상계역',
                line_name='4호선',
                direction='오이도',
                arrival_in_sec=420,
                train_type='general',
            )
        ],
    )

    dashboard = build_dashboard(profile)

    assert dashboard.bus
    assert dashboard.bus_positions == []
    assert dashboard.subway
    assert dashboard.profile.stops[0].external_id == '200000123'
