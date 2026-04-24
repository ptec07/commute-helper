from app.schemas.provider_models import BusArrival, BusPosition, RecommendationResult, SubwayArrival


def test_bus_arrival_computes_display_minutes():
    item = BusArrival(
        route_id='100',
        route_name='146',
        stop_id='200',
        stop_name='상계주공7단지',
        arrival_in_sec=240,
        arrival_message='4분 후 도착',
        is_last_bus=False,
    )

    assert item.arrival_in_min == 4


def test_recommendation_result_keeps_mode_and_message():
    result = RecommendationResult(
        mode='bus',
        message='지금 출발하면 버스가 더 유리합니다.',
        reason='버스 도착이 더 빠릅니다.',
        leave_by='08:17',
    )

    assert result.mode == 'bus'
    assert '버스' in result.message


def test_subway_and_bus_position_shapes_are_constructible():
    subway = SubwayArrival(
        station_id='station-100',
        station_name='상계역',
        line_name='4호선',
        direction='오이도방향',
        arrival_in_sec=420,
        train_type='일반',
    )
    position = BusPosition(
        route_id='route-146',
        vehicle_id='bus-1',
        station_count_from_target=2,
        congestion_level='medium',
    )

    assert subway.arrival_in_min == 7
    assert position.station_count_from_target == 2
