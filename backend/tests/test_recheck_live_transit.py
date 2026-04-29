import httpx

from scripts import recheck_live_transit


class DummyResponse:
    def __init__(self, text: str):
        self.status_code = 200
        self.text = text
        self.headers = {'content-type': 'application/xml'}


def test_recheck_live_transit_uses_known_working_seoul_bus_probe_ids():
    assert recheck_live_transit.BUS_STOP_ID == '100000001'
    assert recheck_live_transit.BUS_ROUTE_ID == '204000190'


def test_run_upstream_checks_normalizes_subway_station_name(monkeypatch, capsys):
    captured = []

    monkeypatch.setattr(
        recheck_live_transit,
        'get_settings',
        lambda: type(
            'Settings',
            (),
            {
                'public_data_service_key': 'bus-live-key',
                'seoul_open_api_key': 'subway-live-key',
            },
        )(),
    )

    def fake_get(url: str, *, params=None, timeout: float):
        captured.append((url, params))
        return DummyResponse('<?xml version="1.0" encoding="UTF-8"?><RESULT><code>INFO-000</code><message>정상 처리되었습니다.</message></RESULT>')

    monkeypatch.setattr(httpx, 'get', fake_get)

    recheck_live_transit.run_upstream_checks()

    subway_url, subway_params = captured[-1]
    assert subway_params is None
    assert '%EC%83%81%EA%B3%84' in subway_url
    assert '%EC%97%AD' not in subway_url
