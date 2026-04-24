from __future__ import annotations

from xml.etree import ElementTree as ET

from app.schemas.provider_models import SubwayArrival


class SeoulSubwayArrivalProvider:
    def __init__(self, service_key: str):
        self.service_key = service_key

    def build_params(self, station_name: str) -> dict[str, str]:
        return {'serviceKey': self.service_key, 'statnNm': station_name}

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
