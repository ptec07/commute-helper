from datetime import time

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.db.base import Base
from app.models.commute_profile import CommuteProfile
from app.models.commute_stop import CommuteStop
from app.services.profile_store import add_stop, create_profile, get_profile, list_profiles


def make_session() -> Session:
    engine = create_engine('sqlite:///:memory:', future=True)
    TestingSessionLocal = sessionmaker(
        bind=engine,
        autoflush=False,
        autocommit=False,
        expire_on_commit=False,
        future=True,
    )
    Base.metadata.create_all(engine)
    return TestingSessionLocal()


def test_create_profile_persists_profile_in_database():
    session = make_session()
    profile = CommuteProfile(
        name='회사 가기',
        origin_label='집',
        destination_label='회사',
        target_arrival_time=time(9, 0),
        preferred_mode='balanced',
        walking_tolerance_min=10,
    )

    stored = create_profile(session, profile)
    session.expunge_all()

    reloaded = get_profile(session, stored.id)

    assert reloaded is not None
    assert reloaded.name == '회사 가기'
    assert list_profiles(session)[0].id == stored.id


def test_add_stop_persists_stop_in_database():
    session = make_session()
    profile = create_profile(
        session,
        CommuteProfile(
            name='회사 가기',
            origin_label='집',
            destination_label='회사',
            target_arrival_time=time(9, 0),
        ),
    )

    stored_stop = add_stop(
        session,
        profile.id,
        CommuteStop(
            type='subway_station',
            external_id='station-100',
            name='상계역',
            line_name='4호선',
            direction='오이도방향',
            sort_order=1,
        ),
    )
    session.expunge_all()

    reloaded = get_profile(session, profile.id)

    assert stored_stop.commute_profile_id == profile.id
    assert reloaded is not None
    assert len(reloaded.stops) == 1
    assert reloaded.stops[0].name == '상계역'
