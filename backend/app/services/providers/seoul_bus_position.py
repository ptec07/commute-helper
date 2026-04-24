from __future__ import annotations

import json

from app.schemas.provider_models import BusPosition

CONGESTION_MAP = {
    '1': 'low',
    '2': 'moderate',
    '3': 'medium',
    '4': 'high',
}


class SeoulBusPositionProvider:
    def __init__(self, service_key: str):
        self.service_key = service_key

    def build_params(self, route_id: str) -> dict[str, str]:
        return {'serviceKey': self.service_key, 'busRouteId': route_id}

    def parse(self, payload: str) -> list[BusPosition]:
        data = json.loads(payload)
        items = data.get('msgBody', {}).get('itemList', [])
        positions: list[BusPosition] = []
        for item in items:
            congestion_raw = str(item.get('congetion', ''))
            positions.append(
                BusPosition(
                    route_id=str(item.get('busRouteId', '')),
                    vehicle_id=str(item.get('vehId', '')),
                    station_count_from_target=int(item.get('sectOrd', 0)),
                    congestion_level=CONGESTION_MAP.get(congestion_raw, None),
                )
            )
        return positions
