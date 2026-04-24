from app.schemas.provider_models import BusArrival, SubwayArrival
from app.services.recommendation_service import recommend_mode


def test_recommends_bus_when_bus_arrives_meaningfully_sooner():
    bus = [
        BusArrival(
            route_id='r1',
            route_name='146',
            stop_id='s1',
            stop_name='정류장',
            arrival_in_sec=240,
            arrival_message='4분 후',
            is_last_bus=False,
        )
    ]
    subway = [
        SubwayArrival(
            station_id='st1',
            station_name='상계역',
            line_name='4호선',
            direction='오이도',
            arrival_in_sec=600,
            train_type='일반',
        )
    ]

    result = recommend_mode(bus=bus, subway=subway, preferred_mode='balanced', target_arrival_time='09:00')

    assert result.mode == 'bus'
    assert '버스' in result.message


def test_uses_preference_when_scores_are_close():
    bus = [
        BusArrival(
            route_id='r1',
            route_name='146',
            stop_id='s1',
            stop_name='정류장',
            arrival_in_sec=300,
            arrival_message='5분 후',
            is_last_bus=False,
        )
    ]
    subway = [
        SubwayArrival(
            station_id='st1',
            station_name='상계역',
            line_name='4호선',
            direction='오이도',
            arrival_in_sec=300,
            train_type='일반',
        )
    ]

    result = recommend_mode(bus=bus, subway=subway, preferred_mode='subway', target_arrival_time='09:00')

    assert result.mode == 'subway'
    assert '지하철' in result.message
