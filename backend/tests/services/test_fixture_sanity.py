from pathlib import Path


def test_provider_fixture_files_exist():
    fixtures = [
        'seoul_bus_arrival.xml',
        'seoul_bus_position.json',
        'seoul_subway_arrival.xml',
        'seoul_citydata.xml',
    ]
    root = Path('tests/fixtures')
    for name in fixtures:
        assert (root / name).exists(), name
