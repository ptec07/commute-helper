from pathlib import Path

from app.services.providers.seoul_subway_arrival import SeoulSubwayArrivalProvider


def test_parses_subway_arrival_fixture_into_normalized_objects():
    xml_text = Path('tests/fixtures/seoul_subway_arrival.xml').read_text(encoding='utf-8')
    provider = SeoulSubwayArrivalProvider(service_key='dummy')

    arrivals = provider.parse(xml_text)

    assert arrivals[0].station_name == '상계역'
    assert arrivals[0].arrival_in_sec == 420
    assert arrivals[0].line_name == '4호선 오이도방면'
