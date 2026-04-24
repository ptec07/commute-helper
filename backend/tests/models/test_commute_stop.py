from datetime import time

import pytest

from app.models.commute_profile import CommuteProfile
from app.models.commute_stop import CommuteStop


def make_profile() -> CommuteProfile:
    return CommuteProfile(
        name='회사 가기',
        origin_label='집',
        destination_label='회사',
        target_arrival_time=time(hour=9),
    )


def test_commute_stop_rejects_unsupported_type():
    with pytest.raises(ValueError):
        CommuteStop(type='tram_stop', external_id='x', name='잘못된 정류장', sort_order=1)


def test_commute_profile_holds_related_stops():
    profile = make_profile()
    stop = CommuteStop(
        type='subway_station',
        external_id='station-100',
        name='상계역',
        line_name='4호선',
        direction='오이도방향',
        sort_order=1,
    )

    profile.stops.append(stop)

    assert profile.stops[0].name == '상계역'
    assert stop.commute_profile is profile
