from pathlib import Path

from app.services.providers.seoul_bus_arrival import SeoulBusArrivalProvider


def test_parses_bus_arrival_fixture_into_normalized_objects():
    xml_text = Path('tests/fixtures/seoul_bus_arrival.xml').read_text(encoding='utf-8')
    provider = SeoulBusArrivalProvider(service_key='dummy')

    arrivals = provider.parse(xml_text)

    assert arrivals[0].route_name == '146'
    assert arrivals[0].arrival_in_sec == 240
    assert arrivals[0].stop_name == '상계주공7단지'
