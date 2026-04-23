from datetime import time

from app.models.commute_profile import CommuteProfile


def test_commute_profile_defaults_balanced_mode():
    profile = CommuteProfile(
        name='회사 가기',
        origin_label='집',
        destination_label='회사',
        target_arrival_time=time(hour=9),
    )

    assert profile.preferred_mode == 'balanced'
    assert profile.walking_tolerance_min == 10
