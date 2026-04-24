from __future__ import annotations

from app.schemas.provider_models import BusArrival, RecommendationResult, SubwayArrival


def _earliest_bus_seconds(items: list[BusArrival]) -> int | None:
    if not items:
        return None
    return min(item.arrival_in_sec for item in items)


def _earliest_subway_seconds(items: list[SubwayArrival]) -> int | None:
    if not items:
        return None
    return min(item.arrival_in_sec for item in items)


def recommend_mode(
    *,
    bus: list[BusArrival],
    subway: list[SubwayArrival],
    preferred_mode: str,
    target_arrival_time: str,
) -> RecommendationResult:
    bus_sec = _earliest_bus_seconds(bus)
    subway_sec = _earliest_subway_seconds(subway)

    if bus_sec is None and subway_sec is None:
        return RecommendationResult(
            mode='balanced',
            message='현재 추천 가능한 실시간 정보가 없습니다.',
            reason='버스와 지하철 정보가 모두 비어 있습니다.',
            leave_by=None,
        )

    bus_score = 100 - (bus_sec // 60) * 8 if bus_sec is not None else -999
    subway_score = 100 - (subway_sec // 60) * 8 if subway_sec is not None else -999

    if preferred_mode == 'bus':
        bus_score += 3
    elif preferred_mode == 'subway':
        subway_score += 3

    if bus_score > subway_score:
        return RecommendationResult(
            mode='bus',
            message='지금 출발하면 버스가 더 유리합니다.',
            reason='버스 도착이 더 빠릅니다.',
            leave_by=target_arrival_time,
        )

    return RecommendationResult(
        mode='subway',
        message='지금 출발하면 지하철이 더 유리합니다.',
        reason='지하철 도착이 더 안정적이거나 빠릅니다.',
        leave_by=target_arrival_time,
    )
