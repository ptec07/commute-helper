from __future__ import annotations

from xml.etree import ElementTree as ET

import httpx

from app.schemas.provider_models import BusArrival


class SeoulBusArrivalProvider:
    secure_endpoint = 'https://ws.bus.go.kr/api/rest/arrive/getLowArrInfoByStId'
    insecure_endpoint = 'http://ws.bus.go.kr/api/rest/arrive/getLowArrInfoByStId'

    def __init__(self, service_key: str, allow_insecure_http_fallback: bool = False, request_timeout: float = 3.0):
        self.service_key = service_key
        self.allow_insecure_http_fallback = allow_insecure_http_fallback
        self.request_timeout = request_timeout

    def build_params(self, stop_id: str, route_id: str | None = None) -> dict[str, str]:
        params = {'serviceKey': self.service_key, 'stId': stop_id}
        if route_id:
            params['busRouteId'] = route_id
        return params

    def fetch(self, stop_id: str, route_id: str | None = None) -> list[BusArrival]:
        try:
            response = httpx.get(self.secure_endpoint, params=self.build_params(stop_id, route_id), timeout=self.request_timeout)
            response.raise_for_status()
            if not response.text.lstrip().startswith('<'):
                raise OSError('Seoul bus arrival API returned a non-XML payload')
            return self.parse(response.text)
        except httpx.HTTPError as exc:
            if self.allow_insecure_http_fallback:
                return self._fetch_insecure(stop_id, route_id)
            raise OSError('Failed to fetch live Seoul bus arrivals') from exc
        except ET.ParseError as exc:
            raise OSError('Failed to parse live Seoul bus arrivals') from exc
        except ValueError as exc:
            raise OSError('Failed to normalize live Seoul bus arrivals') from exc

    def _fetch_insecure(self, stop_id: str, route_id: str | None = None) -> list[BusArrival]:
        try:
            response = httpx.get(self.insecure_endpoint, params=self.build_params(stop_id, route_id), timeout=self.request_timeout)
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
        self._raise_for_service_error(root)
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

    @staticmethod
    def _raise_for_service_error(root: ET.Element) -> None:
        header_code = (root.findtext('.//headerCd') or '').strip()
        if header_code == '4':
            return
        if header_code and header_code != '0':
            message = (root.findtext('.//headerMsg') or 'Failed to fetch live Seoul bus arrivals').strip()
            raise OSError(message)
