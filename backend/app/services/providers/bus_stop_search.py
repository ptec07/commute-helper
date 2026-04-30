from __future__ import annotations

import re
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
    route_list_endpoint = 'https://apis.data.go.kr/6410000/busrouteservice/v2/getBusRouteListv2'
    route_station_endpoint = 'https://apis.data.go.kr/6410000/busrouteservice/v2/getBusRouteStationListv2'

    def __init__(self, service_key: str, request_timeout: float = 3.0, max_route_fallbacks: int = 3):
        self.service_key = service_key
        self.request_timeout = request_timeout
        self.max_route_fallbacks = max_route_fallbacks

    def fetch(self, query: str) -> list[dict[str, str]]:
        if not self.service_key:
            raise OSError('Gyeonggi bus stop search key is not configured')

        station_error: Exception | None = None
        try:
            response = httpx.get(
                self.endpoint,
                params={
                    'serviceKey': self.service_key,
                    'keyword': query,
                },
                timeout=self.request_timeout,
            )
            response.raise_for_status()
            return self.parse(response.text)
        except (httpx.HTTPError, OSError) as exc:
            station_error = exc

        if not _looks_like_route_query(query):
            raise OSError('Gyeonggi route fallback only supports route-like queries') from station_error

        try:
            route_stations = self._fetch_route_station_fallback(query)
        except (httpx.HTTPError, OSError) as exc:
            raise OSError('Gyeonggi bus stop search request failed') from exc
        if route_stations:
            return route_stations
        raise OSError('Gyeonggi bus stop search request failed') from station_error

    def _fetch_route_station_fallback(self, query: str) -> list[dict[str, str]]:
        route_response = httpx.get(
            self.route_list_endpoint,
            params={'serviceKey': self.service_key, 'keyword': query, 'format': 'xml'},
            timeout=self.request_timeout,
        )
        route_response.raise_for_status()
        routes = self.parse_routes(route_response.text)

        results: list[dict[str, str]] = []
        for route in routes[: self.max_route_fallbacks]:
            route_id = route.get('routeId', '')
            route_name = route.get('routeName', '')
            if not route_id:
                continue
            station_response = httpx.get(
                self.route_station_endpoint,
                params={'serviceKey': self.service_key, 'routeId': route_id, 'format': 'xml'},
                timeout=self.request_timeout,
            )
            station_response.raise_for_status()
            results.extend(self.parse_route_stations(station_response.text, route_name=route_name))
        return deduplicate_stops(results)

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

    def parse_routes(self, payload: str) -> list[dict[str, str]]:
        try:
            root = ET.fromstring(payload)
        except ET.ParseError as exc:
            raise OSError('Failed to parse Gyeonggi bus route search payload') from exc

        result_code = (root.findtext('.//resultCode') or '').strip()
        if result_code and result_code not in {'0', '00'}:
            result_msg = (root.findtext('.//resultMessage') or '').strip()
            raise OSError(f'Gyeonggi bus route search failed: {result_code} {result_msg}')

        routes = []
        for item in root.findall('.//busRouteList') + root.findall('.//item'):
            route_id = _first_text(item, ['routeId', 'routeID', 'ROUTE_ID', 'id'])
            route_name = _first_text(item, ['routeName', 'routeNm', 'ROUTE_NM', 'name'])
            if route_id:
                routes.append({'routeId': route_id, 'routeName': route_name})
        return routes

    def parse_route_stations(self, payload: str, route_name: str = '') -> list[dict[str, str]]:
        try:
            root = ET.fromstring(payload)
        except ET.ParseError as exc:
            raise OSError('Failed to parse Gyeonggi bus route station payload') from exc

        result_code = (root.findtext('.//resultCode') or '').strip()
        if result_code and result_code not in {'0', '00'}:
            result_msg = (root.findtext('.//resultMessage') or '').strip()
            raise OSError(f'Gyeonggi bus route station search failed: {result_code} {result_msg}')

        stops = []
        direction = f'{route_name}번 노선' if route_name else ''
        for item in root.findall('.//busRouteStationList') + root.findall('.//item'):
            stop_id = _first_text(item, ['stationId', 'stationID', 'STATION_ID', 'id'])
            name = _first_text(item, ['stationName', 'stationNm', 'STATION_NM', 'name'])
            mobile_no = _first_text(item, ['mobileNo', 'mobileNo1', 'MOBILE_NO'])
            if not stop_id or not name:
                continue
            label = f'경기버스정류장 {mobile_no.strip()}' if mobile_no and mobile_no.strip() else '경기버스정류장'
            stops.append(
                {
                    'externalId': stop_id,
                    'name': name,
                    'lineName': label,
                    'kind': 'bus_stop',
                    'direction': direction,
                }
            )
        return stops


def _looks_like_route_query(query: str) -> bool:
    normalized = query.strip().casefold().replace(' ', '')
    if not normalized:
        return False
    return bool(re.fullmatch(r'(?:[a-z가-힣]{0,3}\d{1,4}[a-z가-힣]{0,3}|[a-z]\d{1,4})', normalized))


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
