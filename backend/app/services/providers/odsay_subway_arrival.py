from __future__ import annotations

from datetime import datetime, time, timedelta

from app.schemas.provider_models import SubwayArrival
from app.services.providers.odsay_client import ODsayClient

TRAIN_TYPE_MAP = {
    0: 'general',
    1: 'express',
    2: 'special',
}


class ODsaySubwayArrivalProvider:
    def __init__(self, api_key: str, now_provider=None):
        self.client = ODsayClient(api_key)
        self.now_provider = now_provider or datetime.now

    def fetch(self, station_name: str, line_name: str | None = None) -> list[SubwayArrival]:
        station = self._resolve_station(station_name, line_name)
        payload = self.client.get('searchSubwaySchedule', stationID=station['stationID'])
        result = payload.get('result', {})
        now = self.now_provider()
        schedule = self._select_schedule(result, now)
        departures = self._upcoming_departures(schedule, now)

        arrivals: list[SubwayArrival] = []
        for departure in departures:
            departure_dt = self._departure_datetime(now, str(departure.get('departureTime') or ''))
            if departure_dt is None:
                continue
            arrivals.append(
                SubwayArrival(
                    station_id=str(result.get('stationID') or station.get('stationID') or ''),
                    station_name=str(result.get('stationName') or station.get('stationName') or station_name),
                    line_name=str(result.get('laneName') or station.get('laneName') or line_name or ''),
                    direction=str(departure.get('endStationName') or ''),
                    arrival_in_sec=max(0, int((departure_dt - now).total_seconds())),
                    train_type=TRAIN_TYPE_MAP.get(int(departure.get('subwayClass', 0)), 'general'),
                )
            )
        return arrivals

    def _resolve_station(self, station_name: str, line_name: str | None) -> dict:
        payload = self.client.get('searchStation', stationName=station_name, stationClass='2', displayCnt=20)
        stations = payload.get('result', {}).get('station', [])
        if not stations:
            raise OSError(f'ODsay subway station not found: {station_name}')

        exact_name_matches = [station for station in stations if station.get('stationName') == station_name]
        candidates = exact_name_matches or stations
        if line_name:
            for station in candidates:
                if station.get('laneName') == line_name:
                    return station
        return candidates[0]

    @staticmethod
    def _select_schedule(result: dict, now: datetime) -> dict:
        if now.weekday() == 5:
            return result.get('saturdaySchedule', {})
        if now.weekday() == 6:
            return result.get('holidaySchedule', {})
        return result.get('weekdaySchedule', {})

    def _upcoming_departures(self, schedule: dict, now: datetime) -> list[dict]:
        departures = list(schedule.get('up', [])) + list(schedule.get('down', []))
        upcoming = []
        for departure in departures:
            departure_dt = self._departure_datetime(now, str(departure.get('departureTime') or ''))
            if departure_dt is None or departure_dt < now:
                continue
            upcoming.append((departure_dt, departure))
        upcoming.sort(key=lambda item: item[0])
        return [departure for _, departure in upcoming]

    @staticmethod
    def _departure_datetime(now: datetime, departure_time: str) -> datetime | None:
        parts = departure_time.split(':')
        if len(parts) < 2:
            return None
        hour = int(parts[0])
        minute = int(parts[1])
        second = int(parts[2]) if len(parts) > 2 else 0
        day_offset, normalized_hour = divmod(hour, 24)
        departure_date = now.date() + timedelta(days=day_offset)
        return datetime.combine(departure_date, time(normalized_hour, minute, second))