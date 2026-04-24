from __future__ import annotations

import json
from xml.etree import ElementTree as ET

import httpx

from app.schemas.provider_models import BusPosition

CONGESTION_MAP = {
    '1': 'low',
    '2': 'moderate',
    '3': 'medium',
    '4': 'high',
}


class SeoulBusPositionProvider:
    endpoint = 'https://ws.bus.go.kr/api/rest/buspos/getLowBusPosByRtid'

    def __init__(self, service_key: str):
        self.service_key = service_key

    def build_params(self, route_id: str) -> dict[str, str]:
        return {'serviceKey': self.service_key, 'busRouteId': route_id}

    def fetch(self, route_id: str) -> list[BusPosition]:
        try:
            response = httpx.get(self.endpoint, params=self.build_params(route_id), timeout=10.0)
            response.raise_for_status()
            return self.parse(response.text)
        except httpx.HTTPError as exc:
            raise OSError('Failed to fetch live Seoul bus positions') from exc
        except (ET.ParseError, json.JSONDecodeError, ValueError) as exc:
            raise OSError('Failed to parse live Seoul bus positions') from exc

    def parse(self, payload: str) -> list[BusPosition]:
        payload = payload.strip()
        if payload.startswith('<'):
            return self._parse_xml(payload)
        return self._parse_json(payload)

    def _parse_json(self, payload: str) -> list[BusPosition]:
        data = json.loads(payload)
        items = data.get('msgBody', {}).get('itemList', [])
        return [self._to_bus_position(item) for item in items]

    def _parse_xml(self, payload: str) -> list[BusPosition]:
        root = ET.fromstring(payload)
        items = root.findall('.//itemList')
        return [
            self._to_bus_position(
                {
                    'busRouteId': item.findtext('busRouteId', default=''),
                    'vehId': item.findtext('vehId', default=''),
                    'sectOrd': item.findtext('sectOrd', default='0'),
                    'congetion': item.findtext('congetion', default=''),
                }
            )
            for item in items
        ]

    def _to_bus_position(self, item: dict) -> BusPosition:
        congestion_raw = str(item.get('congetion', ''))
        return BusPosition(
            route_id=str(item.get('busRouteId', '')),
            vehicle_id=str(item.get('vehId', '')),
            station_count_from_target=int(item.get('sectOrd', 0)),
            congestion_level=CONGESTION_MAP.get(congestion_raw, None),
        )
