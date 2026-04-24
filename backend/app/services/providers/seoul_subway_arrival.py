from __future__ import annotations

from urllib.parse import quote
from xml.etree import ElementTree as ET

import httpx

from app.schemas.provider_models import SubwayArrival


class SeoulSubwayArrivalProvider:
    endpoint_template = 'https://swopenAPI.seoul.go.kr/api/subway/{service_key}/xml/realtimeStationArrival/0/5/{station_name}'

    def __init__(self, service_key: str):
        self.service_key = service_key

    def build_params(self, station_name: str) -> dict[str, str]:
        return {'serviceKey': self.service_key, 'statnNm': station_name}

    def build_url(self, station_name: str) -> str:
        return self.endpoint_template.format(service_key=self.service_key, station_name=quote(station_name))

    def fetch(self, station_name: str) -> list[SubwayArrival]:
        try:
            response = httpx.get(self.build_url(station_name), timeout=10.0)
            response.raise_for_status()
            if not response.text.lstrip().startswith('<'):
                raise OSError('Seoul subway API returned a non-XML payload')
            return self.parse(response.text)
        except httpx.HTTPError as exc:
            raise OSError('Failed to fetch live Seoul subway arrivals') from exc
        except ET.ParseError as exc:
            raise OSError('Failed to parse live Seoul subway arrivals') from exc
        except ValueError as exc:
            raise OSError('Failed to normalize live Seoul subway arrivals') from exc

    def parse(self, xml_text: str) -> list[SubwayArrival]:
        root = ET.fromstring(xml_text)
        rows = root.findall('.//row')
        arrivals: list[SubwayArrival] = []
        for row in rows:
            arrivals.append(
                SubwayArrival(
                    station_id=row.findtext('statnId', default=''),
                    station_name=row.findtext('statnNm', default=''),
                    line_name=row.findtext('trainLineNm', default=''),
                    direction=row.findtext('subwayHeading', default=''),
                    arrival_in_sec=int(row.findtext('barvlDt', default='0')),
                    train_type=row.findtext('btrainSttus', default=''),
                )
            )
        return arrivals
