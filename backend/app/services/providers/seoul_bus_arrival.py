from __future__ import annotations

from xml.etree import ElementTree as ET

import httpx

from app.schemas.provider_models import BusArrival


class SeoulBusArrivalProvider:
    endpoint = 'https://ws.bus.go.kr/api/rest/arrive/getLowArrInfoByStId'

    def __init__(self, service_key: str):
        self.service_key = service_key

    def build_params(self, stop_id: str, route_id: str | None = None) -> dict[str, str]:
        params = {'serviceKey': self.service_key, 'stId': stop_id}
        if route_id:
            params['busRouteId'] = route_id
        return params

    def fetch(self, stop_id: str, route_id: str | None = None) -> list[BusArrival]:
        try:
            response = httpx.get(self.endpoint, params=self.build_params(stop_id, route_id), timeout=10.0)
            response.raise_for_status()
            if not response.text.lstrip().startswith('<'):
                raise OSError('Seoul bus arrival API returned a non-XML payload')
            return self.parse(response.text)
        except httpx.HTTPError as exc:
            raise OSError('Failed to fetch live Seoul bus arrivals') from exc
        except ET.ParseError as exc:
            raise OSError('Failed to parse live Seoul bus arrivals') from exc
        except ValueError as exc:
            raise OSError('Failed to normalize live Seoul bus arrivals') from exc

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
