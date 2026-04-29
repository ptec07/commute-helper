from __future__ import annotations

import re

from app.schemas.provider_models import BusArrival
from app.services.providers.odsay_client import ODsayClient


class ODsayBusArrivalProvider:
    def __init__(self, api_key: str):
        self.client = ODsayClient(api_key)

    def fetch(self, stop_name: str, stop_local_id: str | None = None) -> list[BusArrival]:
        station = self._resolve_station(stop_name, stop_local_id)
        payload = self.client.get('busStationInfo', stationID=station['stationID'])
        result = payload.get('result', {})
        stop_id = str(result.get('localStationID') or station.get('localStationID') or result.get('stationID') or '')
        stop_name = str(result.get('stationName') or station.get('stationName') or stop_name)

        arrivals: list[BusArrival] = []
        for lane in result.get('lane', []):
            interval_min = self._parse_interval_minutes(lane.get('busInterval', ''))
            arrivals.append(
                BusArrival(
                    route_id=str(lane.get('busLocalBlID') or lane.get('busID') or ''),
                    route_name=str(lane.get('busNo') or ''),
                    stop_id=stop_id,
                    stop_name=stop_name,
                    arrival_in_sec=interval_min * 60,
                    arrival_message=f'약 {interval_min}분 간격 운행',
                    is_last_bus=False,
                )
            )
        return sorted(arrivals, key=lambda item: item.arrival_in_sec)

    def _resolve_station(self, stop_name: str, stop_local_id: str | None) -> dict:
        payload = self.client.get('searchStation', stationName=stop_name, stationClass='1', displayCnt=20)
        stations = payload.get('result', {}).get('station', [])
        if not stations:
            raise OSError(f'ODsay bus stop not found: {stop_name}')

        exact_name_matches = [station for station in stations if station.get('stationName') == stop_name]
        candidates = exact_name_matches or stations
        if stop_local_id:
            for station in candidates:
                ids = {
                    str(station.get('localStationID') or ''),
                    str(station.get('arsID') or ''),
                    str(station.get('stationID') or ''),
                }
                if stop_local_id in ids:
                    return station
        return candidates[0]

    @staticmethod
    def _parse_interval_minutes(value: str) -> int:
        match = re.search(r'\d+', str(value))
        return int(match.group()) if match else 0