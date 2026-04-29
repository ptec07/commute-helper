from __future__ import annotations

from xml.etree import ElementTree as ET

import httpx

from app.core.settings import get_settings
from app.services.providers.seoul_bus_arrival import SeoulBusArrivalProvider
from app.services.providers.seoul_bus_position import SeoulBusPositionProvider
from app.services.providers.seoul_subway_arrival import SeoulSubwayArrivalProvider


BUS_STOP_ID = '100000001'
BUS_ROUTE_ID = '204000190'
SUBWAY_STATION_NAME = '상계역'


def summarize_xml(text: str) -> dict[str, str | int | None]:
    root = ET.fromstring(text)
    return {
        'root': root.tag,
        'headerCd': root.findtext('.//headerCd'),
        'headerMsg': root.findtext('.//headerMsg'),
        'code': root.findtext('.//code'),
        'message': root.findtext('.//message'),
        'rows': len(root.findall('.//itemList')) + len(root.findall('.//row')),
    }


def print_settings() -> None:
    get_settings.cache_clear()
    settings = get_settings()
    print('## loaded_settings')
    print(
        {
            'public_data_service_key_present': bool(settings.public_data_service_key),
            'public_data_service_key_len': len(settings.public_data_service_key),
            'seoul_open_api_key_present': bool(settings.seoul_open_api_key),
            'seoul_open_api_key_len': len(settings.seoul_open_api_key),
            'use_live_public_data': settings.use_live_public_data,
            'allow_insecure_seoul_transit_http': settings.allow_insecure_seoul_transit_http,
            'database_url': settings.database_url,
        }
    )
    print()


def run_provider_checks() -> None:
    settings = get_settings()
    checks = [
        (
            'bus_arrival_provider',
            lambda: SeoulBusArrivalProvider(
                settings.public_data_service_key,
                allow_insecure_http_fallback=settings.allow_insecure_seoul_transit_http,
            ).fetch(BUS_STOP_ID),
        ),
        (
            'bus_position_provider',
            lambda: SeoulBusPositionProvider(
                settings.public_data_service_key,
                allow_insecure_http_fallback=settings.allow_insecure_seoul_transit_http,
            ).fetch(BUS_ROUTE_ID),
        ),
        (
            'subway_provider',
            lambda: SeoulSubwayArrivalProvider(
                settings.seoul_open_api_key,
                allow_insecure_http_fallback=settings.allow_insecure_seoul_transit_http,
            ).fetch(SUBWAY_STATION_NAME),
        ),
    ]

    for name, fn in checks:
        print(f'## {name}')
        try:
            result = fn()
            print({'ok': True, 'count': len(result)})
            if result:
                first = result[0]
                payload = first.model_dump() if hasattr(first, 'model_dump') else first.__dict__
                preview_keys = list(payload)[:6]
                print({key: payload[key] for key in preview_keys})
        except Exception as exc:  # noqa: BLE001
            print({'ok': False, 'type': type(exc).__name__, 'message': str(exc)})
        print()


def run_upstream_checks() -> None:
    settings = get_settings()
    allow_insecure_http_fallback = getattr(settings, 'allow_insecure_seoul_transit_http', False)
    subway_provider = SeoulSubwayArrivalProvider(
        settings.seoul_open_api_key,
        allow_insecure_http_fallback=allow_insecure_http_fallback,
    )
    checks = [
        (
            'bus_arrival_http',
            'http://ws.bus.go.kr/api/rest/arrive/getLowArrInfoByStId',
            {'serviceKey': settings.public_data_service_key, 'stId': BUS_STOP_ID},
        ),
        (
            'bus_position_http',
            'http://ws.bus.go.kr/api/rest/buspos/getLowBusPosByRtid',
            {'serviceKey': settings.public_data_service_key, 'busRouteId': BUS_ROUTE_ID},
        ),
        (
            'subway_http',
            subway_provider.build_url(SUBWAY_STATION_NAME, insecure=True),
            None,
        ),
    ]

    for name, url, params in checks:
        print(f'## {name}')
        try:
            response = httpx.get(url, params=params, timeout=20.0)
            text = response.text.strip()
            print({'status': response.status_code, 'content_type': response.headers.get('content-type')})
            print(text[:260].replace('\n', ' '))
            if text.startswith('<'):
                print(summarize_xml(text))
        except Exception as exc:  # noqa: BLE001
            print({'ok': False, 'type': type(exc).__name__, 'message': str(exc)})
        print()


if __name__ == '__main__':
    print_settings()
    run_provider_checks()
    run_upstream_checks()
