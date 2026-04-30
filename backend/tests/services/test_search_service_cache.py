from app.services import search_service


class FakeSettings:
    use_live_public_data = True
    public_data_service_key = 'public'
    gyeonggi_bus_service_key = 'gyeonggi'


class CountingProvider:
    calls = 0

    def __init__(self, service_key):
        self.service_key = service_key

    def fetch(self, query):
        type(self).calls += 1
        return [
            {
                'externalId': f'{self.service_key}-{query}',
                'name': query,
                'lineName': self.service_key,
                'kind': 'bus_stop',
                'direction': '',
            }
        ]


def test_live_bus_stop_search_reuses_short_ttl_cache(monkeypatch):
    CountingProvider.calls = 0
    search_service.clear_live_bus_stop_search_cache()
    monkeypatch.setattr(search_service, 'get_settings', lambda: FakeSettings())
    monkeypatch.setattr(search_service, 'SeoulBusStopSearchProvider', CountingProvider)
    monkeypatch.setattr(search_service, 'GyeonggiBusStopSearchProvider', CountingProvider)

    first = search_service._search_live_bus_stops('1001')
    second = search_service._search_live_bus_stops('1001')

    assert first == second
    assert CountingProvider.calls == 2
