from __future__ import annotations

from app.schemas.provider_models import BusPosition


class ODsayBusPositionProvider:
    def __init__(self, api_key: str):
        self.api_key = api_key

    def fetch(self, route_id: str) -> list[BusPosition]:
        return []