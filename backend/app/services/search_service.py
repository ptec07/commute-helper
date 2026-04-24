from __future__ import annotations

import json
from pathlib import Path

FIXTURE_PATH = Path(__file__).resolve().parents[2] / 'tests' / 'fixtures' / 'station_index.json'


def search_stops(query: str) -> dict[str, list[dict[str, str]]]:
    data = json.loads(FIXTURE_PATH.read_text(encoding='utf-8'))
    query = query.strip()

    if not query:
        return {'busStops': [], 'subwayStations': []}

    def matches(item: dict[str, str]) -> bool:
        return query in item['name'] or query.lower() in item['name'].lower()

    return {
        'busStops': [item for item in data.get('busStops', []) if matches(item)],
        'subwayStations': [item for item in data.get('subwayStations', []) if matches(item)],
    }
