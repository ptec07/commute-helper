from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
import threading
import time

from app.core.settings import get_settings
from app.schemas.dashboard import DashboardResponse
from app.schemas.profile import CommuteProfileRead
from app.services.providers.odsay_bus_arrival import ODsayBusArrivalProvider
from app.services.providers.odsay_bus_position import ODsayBusPositionProvider
from app.services.providers.odsay_subway_arrival import ODsaySubwayArrivalProvider
from app.services.providers.seoul_bus_arrival import SeoulBusArrivalProvider
from app.services.providers.seoul_bus_position import SeoulBusPositionProvider
from app.services.providers.seoul_subway_arrival import SeoulSubwayArrivalProvider
from app.services.recommendation_service import recommend_mode

FIXTURES = Path(__file__).resolve().parents[2] / 'tests' / 'fixtures'
LIVE_ARRIVAL_CACHE_TTL_SECONDS = 30
_live_arrival_cache: dict[tuple[str, str], tuple[float, list]] = {}
_live_arrival_cache_lock = threading.Lock()


def clear_live_arrival_cache():
    with _live_arrival_cache_lock:
        _live_arrival_cache.clear()


def _cached_fetch(kind: str, key: str, fetcher):
    cache_key = (kind, key)
    now = time.time()
    with _live_arrival_cache_lock:
        cached = _live_arrival_cache.get(cache_key)
        if cached and now - cached[0] <= LIVE_ARRIVAL_CACHE_TTL_SECONDS:
            return list(cached[1])

    value = list(fetcher())
    with _live_arrival_cache_lock:
        _live_arrival_cache[cache_key] = (time.time(), list(value))
    return value


def _fetch_many(fetch_jobs: list[tuple[str, str, object]]):
    if not fetch_jobs:
        return []
    if len(fetch_jobs) == 1:
        kind, key, fetcher = fetch_jobs[0]
        return _cached_fetch(kind, key, fetcher)

    results_by_index: dict[int, list] = {}
    max_workers = min(4, len(fetch_jobs))
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(_cached_fetch, kind, key, fetcher): index
            for index, (kind, key, fetcher) in enumerate(fetch_jobs)
        }
        for future in as_completed(futures):
            results_by_index[futures[future]] = future.result()

    results = []
    for index in range(len(fetch_jobs)):
        results.extend(results_by_index.get(index, []))
    return results


def _load_fixture_dashboard_data(profile):
    bus_provider = SeoulBusArrivalProvider(service_key='dummy')
    position_provider = SeoulBusPositionProvider(service_key='dummy')
    subway_provider = SeoulSubwayArrivalProvider(service_key='dummy')

    all_bus = bus_provider.parse((FIXTURES / 'seoul_bus_arrival.xml').read_text(encoding='utf-8'))
    all_bus_positions = position_provider.parse((FIXTURES / 'seoul_bus_position.json').read_text(encoding='utf-8'))
    all_subway = subway_provider.parse((FIXTURES / 'seoul_subway_arrival.xml').read_text(encoding='utf-8'))
    return _filter_dashboard_data(profile, all_bus, all_bus_positions, all_subway)


def _load_public_data_dashboard_data(profile):
    settings = get_settings()
    public_data_service_key = getattr(settings, 'public_data_service_key', '')
    seoul_open_api_key = getattr(settings, 'seoul_open_api_key', '')
    if not public_data_service_key and not seoul_open_api_key:
        raise OSError('Public transit live API keys are not configured')

    allow_insecure_http_fallback = getattr(settings, 'allow_insecure_seoul_transit_http', False)
    bus_provider = SeoulBusArrivalProvider(
        service_key=public_data_service_key,
        allow_insecure_http_fallback=allow_insecure_http_fallback,
    )
    position_provider = SeoulBusPositionProvider(
        service_key=public_data_service_key,
        allow_insecure_http_fallback=allow_insecure_http_fallback,
    )
    subway_key = seoul_open_api_key or public_data_service_key
    subway_provider = SeoulSubwayArrivalProvider(
        service_key=subway_key,
        allow_insecure_http_fallback=allow_insecure_http_fallback,
    )

    bus_stops = [stop for stop in profile.stops if stop.type == 'bus_stop']
    subway_stops = [stop for stop in profile.stops if stop.type == 'subway_station']

    bus = _fetch_many([('bus', stop.external_id, lambda stop=stop: bus_provider.fetch(stop.external_id)) for stop in bus_stops])
    bus_positions: list = []

    subway = _fetch_many([('subway', stop.name, lambda stop=stop: subway_provider.fetch(stop.name)) for stop in subway_stops])

    return _filter_dashboard_data(profile, bus, bus_positions, subway)


def _load_odsay_dashboard_data(profile):
    settings = get_settings()
    odsay_api_key = getattr(settings, 'odsay_api_key', '')
    if not odsay_api_key:
        raise OSError('ODsay API key is not configured')
    bus_provider = ODsayBusArrivalProvider(api_key=odsay_api_key)
    position_provider = ODsayBusPositionProvider(api_key=odsay_api_key)
    subway_provider = ODsaySubwayArrivalProvider(api_key=odsay_api_key)

    bus_stops = [stop for stop in profile.stops if stop.type == 'bus_stop']
    subway_stops = [stop for stop in profile.stops if stop.type == 'subway_station']

    bus = _fetch_many([('odsay-bus', stop.name, lambda stop=stop: bus_provider.fetch(stop.name, stop.external_id)) for stop in bus_stops])
    bus_positions: list = []

    subway = _fetch_many([('odsay-subway', stop.name, lambda stop=stop: subway_provider.fetch(stop.name, stop.line_name)) for stop in subway_stops])

    return _filter_dashboard_data(profile, bus, bus_positions, subway)


def _load_live_dashboard_data(profile):
    try:
        return _load_public_data_dashboard_data(profile)
    except OSError:
        return _load_odsay_dashboard_data(profile)


def _normalize_station_name(name: str) -> str:
    normalized = name.strip()
    if normalized.endswith('역') and len(normalized) > 1:
        return normalized[:-1]
    return normalized


def _filter_dashboard_data(profile, all_bus, all_bus_positions, all_subway):
    selected_bus_names = {stop.name for stop in profile.stops if stop.type == 'bus_stop'}
    selected_bus_ids = {stop.external_id for stop in profile.stops if stop.type == 'bus_stop'}
    selected_subway_names = {stop.name for stop in profile.stops if stop.type == 'subway_station'}
    selected_subway_aliases = {_normalize_station_name(name) for name in selected_subway_names}
    has_selected_stops = bool(profile.stops)

    if selected_bus_names or selected_bus_ids:
        bus = [
            item
            for item in all_bus
            if item.stop_name in selected_bus_names or item.stop_id in selected_bus_ids
        ]
        selected_route_ids = {item.route_id for item in bus}
        bus_positions = [item for item in all_bus_positions if item.route_id in selected_route_ids]
    elif has_selected_stops:
        bus = []
        bus_positions = []
    else:
        bus = all_bus
        bus_positions = all_bus_positions

    if selected_subway_names:
        subway = [
            item
            for item in all_subway
            if item.station_name in selected_subway_names
            or _normalize_station_name(item.station_name) in selected_subway_aliases
        ]
    elif has_selected_stops:
        subway = []
    else:
        subway = all_subway

    return bus, bus_positions, subway


def build_dashboard(profile) -> DashboardResponse:
    settings = get_settings()
    if settings.use_live_public_data and profile.stops:
        try:
            bus, bus_positions, subway = _load_live_dashboard_data(profile)
        except OSError:
            bus, bus_positions, subway = _load_fixture_dashboard_data(profile)
    else:
        bus, bus_positions, subway = _load_fixture_dashboard_data(profile)

    recommendation = recommend_mode(
        bus=bus,
        subway=subway,
        preferred_mode=profile.preferred_mode,
        target_arrival_time=profile.target_arrival_time.isoformat(),
    )

    return DashboardResponse(
        profile=CommuteProfileRead.model_validate(profile),
        bus=bus,
        bus_positions=bus_positions,
        subway=subway,
        recommendation=recommendation,
    )
