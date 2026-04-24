from pathlib import Path

from app.services.providers.seoul_bus_position import SeoulBusPositionProvider


def test_parses_bus_position_fixture_into_normalized_objects():
    payload = Path('tests/fixtures/seoul_bus_position.json').read_text(encoding='utf-8')
    provider = SeoulBusPositionProvider(service_key='dummy')

    positions = provider.parse(payload)

    assert positions[0].station_count_from_target == 2
    assert positions[0].congestion_level == 'medium'
