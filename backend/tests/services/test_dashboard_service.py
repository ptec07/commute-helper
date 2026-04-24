from datetime import time

from app.models.commute_profile import CommuteProfile
from app.models.commute_stop import CommuteStop
from app.services.dashboard_service import build_dashboard
from app.services.profile_store import add_stop, create_profile


def test_dashboard_uses_selected_stop_types_to_filter_results():
    profile = create_profile(
        CommuteProfile(
            name='회사 가기',
            origin_label='집',
            destination_label='회사',
            target_arrival_time=time(hour=9),
        )
    )
    add_stop(
        profile.id,
        CommuteStop(
            type='subway_station',
            external_id='1004000409',
            name='상계역',
            line_name='4호선',
            direction='오이도방향',
            sort_order=1,
        ),
    )

    dashboard = build_dashboard(profile)

    assert dashboard.bus == []
    assert dashboard.bus_positions == []
    assert len(dashboard.subway) == 1
    assert dashboard.subway[0].station_name == '상계역'
