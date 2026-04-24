from __future__ import annotations

from xml.etree import ElementTree as ET

from app.schemas.provider_models import BusArrival


class SeoulBusArrivalProvider:
    def __init__(self, service_key: str):
        self.service_key = service_key

    def build_params(self, stop_id: str, route_id: str | None = None) -> dict[str, str]:
        params = {'serviceKey': self.service_key, 'stId': stop_id}
        if route_id:
            params['busRouteId'] = route_id
        return params

    def parse(self, xml_text: str) -> list[BusArrival]:
        root = ET.fromstring(xml_text)
        items = root.findall('.//itemList')
        arrivals: list[BusArrival] = []
        for item in items:
            arrivals.append(
                BusArrival(
                    route_id=item.findtext('busRouteId', default=''),
                    route_name=item.findtext('rtNm', default=''),
                    stop_id=item.findtext('stId', default=''),
                    stop_name=item.findtext('stNm', default=''),
                    arrival_in_sec=int(item.findtext('arrmsgSec1', default='0')),
                    arrival_message=item.findtext('arrmsg1', default=''),
                    is_last_bus=item.findtext('isLast1', default='0') == '1',
                )
            )
        return arrivals
