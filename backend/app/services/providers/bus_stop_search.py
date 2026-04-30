from __future__ import annotations

import xml.etree.ElementTree as ET
from typing import Any

import httpx


class SeoulBusStopSearchProvider:
    endpoint = 'http://ws.bus.go.kr/api/rest/stationinfo/getStationByName'

    def __init__(self, service_key: str, request_timeout: float = 3.0):
        self.service_key = service_key
        self.request_timeout = request_timeout

    def fetch(self, query: str) -> list[dict[str, str]]:
        if not self.service_key:
            raise OSError('Seoul bus stop search key is not configured')
        try:
            response = httpx.get(
                self.endpoint,
                params={'serviceKey': self.service_key, 'stSrch': query},
                timeout=self.request_timeout,
            )
            response.raise_for_status()
        except httpx.HTTPError as exc:
            raise OSError('Seoul bus stop search request failed') from exc
        return self.parse(response.text)

    def parse(self, payload: str) -> list[dict[str, str]]:
        try:
            root = ET.fromstring(payload)
        except ET.ParseError as exc:
            raise OSError('Failed to parse Seoul bus stop search payload') from exc

        header_code = (root.findtext('.//headerCd') or '').strip()
        if header_code and header_code != '0':
            header_msg = (root.findtext('.//headerMsg') or '').strip()
            raise OSError(f'Seoul bus stop search failed: {header_code} {header_msg}')

        stops = []
        for item in root.findall('.//itemList'):
            stop_id = (item.findtext('stId') or '').strip()
            name = (item.findtext('stNm') or '').strip()
            ars_id = (item.findtext('arsId') or '').strip()
            if not stop_id or not name:
                continue
            label = f'서울버스정류장 {ars_id}' if ars_id and ars_id != '0' else '서울버스정류장'
            stops.append(
                {
                    'externalId': stop_id,
                    'name': name,
                    'lineName': label,
                    'kind': 'bus_stop',
                    'direction': '',
                }
            )
        return stops


class GyeonggiBusStopSearchProvider:
    endpoint = 'https://apis.data.go.kr/6410000/busstationservice/v2/getBusStationListv2'
    legacy_gbis_endpoint = 'http://openapi.gbis.go.kr/ws/rest/busstationservice'

    def __init__(self, service_key: str, request_timeout: float = 3.0):
        self.service_key = service_key
        self.request_timeout = request_timeout

    def fetch(self, query: str) -> list[dict[str, str]]:
        if not self.service_key:
            raise OSError('Gyeonggi bus stop search key is not configured')

        last_error: Exception | None = None
        for endpoint in [self.endpoint, self.legacy_gbis_endpoint]:
            try:
                response = httpx.get(
                    endpoint,
                    params={
                        'serviceKey': self.service_key,
                        'keyword': query,
                    },
                    timeout=self.request_timeout,
                )
                response.raise_for_status()
                return self.parse(response.text)
            except (httpx.HTTPError, OSError) as exc:
                last_error = exc
                continue
        raise OSError('Gyeonggi bus stop search request failed') from last_error

    def parse(self, payload: str) -> list[dict[str, str]]:
        try:
            root = ET.fromstring(payload)
        except ET.ParseError as exc:
            raise OSError('Failed to parse Gyeonggi bus stop search payload') from exc

        result_code = (root.findtext('.//resultCode') or '').strip()
        if result_code and result_code not in {'0', '00'}:
            result_msg = (root.findtext('.//resultMessage') or '').strip()
            raise OSError(f'Gyeonggi bus stop search failed: {result_code} {result_msg}')

        stops = []
        for item in root.findall('.//busStationList') + root.findall('.//item'):
            stop_id = _first_text(item, ['stationId', 'stationID', 'STATION_ID', 'id'])
            name = _first_text(item, ['stationName', 'stationNm', 'STATION_NM', 'name'])
            if not stop_id or not name:
                continue
            stops.append(
                {
                    'externalId': stop_id,
                    'name': name,
                    'lineName': '경기버스정류장',
                    'kind': 'bus_stop',
                    'direction': '',
                }
            )
        return stops


def _first_text(item: ET.Element, names: list[str]) -> str:
    for name in names:
        value = item.findtext(name)
        if value and value.strip():
            return value.strip()
    return ''


def deduplicate_stops(stops: list[dict[str, str]]) -> list[dict[str, str]]:
    seen: set[tuple[str, str]] = set()
    unique = []
    for stop in stops:
        key = (stop.get('kind', ''), stop.get('externalId', ''))
        if key in seen:
            continue
        seen.add(key)
        unique.append(stop)
    return unique
