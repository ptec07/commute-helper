from __future__ import annotations

import json
from pathlib import Path
from typing import Any

SEARCH_INDEX_PATH = Path(__file__).resolve().parents[1] / 'data' / 'transit_search_index.json'
# Backward-compatible alias for existing tests/monkeypatches.
FIXTURE_PATH = SEARCH_INDEX_PATH


def _normalize_query(value: str) -> str:
    return value.strip().casefold()


def _search_terms(item: dict[str, Any]) -> list[str]:
    terms = [
        item.get('name', ''),
        item.get('lineName', ''),
        item.get('apiSearchName', ''),
        item.get('frCode', ''),
    ]
    terms.extend(item.get('aliases', []))
    return [_normalize_query(term) for term in terms if term]


def _match_score(item: dict[str, Any], query: str) -> int | None:
    terms = _search_terms(item)
    if query in terms:
        return 0
    if query.endswith('역') and query[:-1] in terms:
        return 1
    if not query.endswith('역') and f'{query}역' in terms:
        return 1
    if any(term.startswith(query) for term in terms):
        return 2
    if any(query in term for term in terms):
        return 3
    return None


def _public_item(item: dict[str, Any]) -> dict[str, str]:
    return {
        'externalId': str(item.get('externalId', '')),
        'name': str(item.get('name', '')),
        'lineName': str(item.get('lineName', '')),
        'kind': str(item.get('kind', '')),
        'direction': str(item.get('direction', '')),
    }


def _matching_items(items: list[dict[str, Any]], query: str) -> list[dict[str, str]]:
    matches = []
    for index, item in enumerate(items):
        score = _match_score(item, query)
        if score is not None:
            matches.append((score, index, item))
    return [_public_item(item) for score, index, item in sorted(matches, key=lambda row: (row[0], row[1]))]


def search_stops(query: str) -> dict[str, list[dict[str, str]]]:
    try:
        data = json.loads(SEARCH_INDEX_PATH.read_text(encoding='utf-8'))
    except OSError as exc:
        raise OSError('Search index unavailable') from exc
    query = _normalize_query(query)

    if not query:
        return {'busStops': [], 'subwayStations': []}

    return {
        'busStops': _matching_items(data.get('busStops', []), query),
        'subwayStations': _matching_items(data.get('subwayStations', []), query),
    }
