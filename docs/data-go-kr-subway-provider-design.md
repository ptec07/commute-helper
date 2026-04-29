# data.go.kr 지하철 Provider 설계안 (`15125683` 가정)

> **For Hermes:** 구현 시 `test-driven-development`와 `systematic-debugging` 스킬을 함께 사용한다.

**Goal:** 서울 열린데이터광장 전용 `SEOUL_OPEN_API_KEY` 의존도를 줄이고, `PUBLIC_DATA_SERVICE_KEY` 기반으로 지하철 실시간 도착정보를 가져오는 대체 provider 경로를 설계한다.

**Architecture:** `15125683`를 역 단건 조회 API가 아니라 **전체역 일괄 feed**로 가정하고, 새 batch provider가 전체 도착 데이터를 받아 앱 내부 `SubwayArrival` 스키마로 정규화한 뒤 현재 프로필에 선택된 역만 필터링한다. 기존 `SeoulSubwayArrivalProvider`는 당분간 유지하고, dashboard service에서 설정값에 따라 `swopenAPI` 또는 `data.go.kr batch` 경로를 선택하도록 점진 전환한다.

**Tech Stack:** FastAPI, Pydantic, httpx, pytest, XML parsing (`xml.etree.ElementTree`), existing dashboard service + provider schema layer

---

## 왜 `15125683` 기준으로 설계하나

조사 결과:

- `15058052`는 제목상 맞아 보이지만 설명/메타가 모호하고 오래되어 실제 교체 대상으로 삼기엔 명세 확신이 약하다.
- `15125683`는 공공데이터포털 메타에서 **"서울시 전체역 실시간 도착정보"**라고 명시되어 있어 batch feed 가정이 더 자연스럽다.
- 현재 앱은 지하철 stop 수가 매우 적은 MVP라, 전체 feed를 받아서 선택된 역만 필터링해도 구조적으로 단순하다.
- 버스와 동일한 `PUBLIC_DATA_SERVICE_KEY` 계열로 통일할 가능성이 있어 운영 설정이 단순해진다.

---

## 현재 코드 기준 문제점

### 현재 provider
- 파일: `backend/app/services/providers/seoul_subway_arrival.py`
- 입력: `station_name`
- 출력: `list[SubwayArrival]`
- 키: `SEOUL_OPEN_API_KEY` 우선, 없으면 `PUBLIC_DATA_SERVICE_KEY` fallback
- 엔드포인트: `swopenAPI.seoul.go.kr/api/subway/.../realtimeStationArrival/.../{station_name}`

### 문제
1. 현재 환경에서 `swopenAPI` 443 timeout 이슈가 있었다.
2. HTTP fallback을 넣어도 `PUBLIC_DATA_SERVICE_KEY`는 `swopenAPI`에서 유효하지 않았다.
3. 즉 지하철 live 성공이 `SEOUL_OPEN_API_KEY`에 묶여 있다.
4. README에는 fallback이 있는 것처럼 보이지만, 실제로는 **엔드포인트와 키 체계가 달라 fallback 성공 가능성이 낮다**.

---

## 목표 상태

### 새 데이터 흐름
1. `DataGoKrSeoulSubwayBatchProvider.fetch_all()` 호출
2. `15125683` XML payload 수신
3. 전체 row를 `SubwayArrival` 리스트로 정규화
4. `dashboard_service`가 현재 profile의 `subway_station` stop 기준으로 필터링
5. 필요한 역만 recommendation engine에 전달

### 기대 효과
- `SEOUL_OPEN_API_KEY` 없이도 지하철 live 경로를 만들 수 있다.
- 버스/지하철 둘 다 `PUBLIC_DATA_SERVICE_KEY` 기반으로 맞출 수 있다.
- 역 alias/정규화 처리를 provider 외부가 아니라 filtering 계층에서 통제할 수 있다.

---

## 설계 원칙

1. **기존 `SubwayArrival` 스키마는 유지**한다.
2. 기존 `SeoulSubwayArrivalProvider.fetch(station_name)`도 즉시 삭제하지 않는다.
3. 새 provider는 단건 조회가 아니라 **batch 조회 전용**으로 만든다.
4. dashboard service가 provider 차이를 흡수한다.
5. 실제 명세 확인 전까지는 fixture-first TDD로 parser와 filtering 레이어를 먼저 굳힌다.

---

## 제안 파일 구조

### 신규 파일
- `backend/app/services/providers/data_go_kr_seoul_subway_batch.py`
- `backend/tests/fixtures/data_go_kr_seoul_subway_batch.xml`
- `backend/tests/services/test_data_go_kr_seoul_subway_batch.py`

### 수정 파일
- `backend/app/core/settings.py`
- `backend/app/services/dashboard_service.py`
- `backend/tests/services/test_live_public_data.py`
- `backend/.env.example`
- `README.md`

---

## 설정 설계

`backend/app/core/settings.py`에 아래 필드를 추가한다.

```python
class Settings(BaseSettings):
    ...
    subway_live_source: str = 'swopenapi'  # 'swopenapi' | 'data_go_kr_batch'
```

### 의도
- 기본값은 현재 동작과 동일하게 `swopenapi`
- 실험/전환 시에만 `data_go_kr_batch`
- 기존 환경을 깨지 않는 점진 전환

### `.env.example`

```bash
SUBWAY_LIVE_SOURCE=swopenapi
```

---

## Provider 인터페이스 설계

### 신규 batch provider

```python
from app.schemas.provider_models import SubwayArrival


class DataGoKrSeoulSubwayBatchProvider:
    secure_endpoint = 'https://<15125683-actual-endpoint>'
    insecure_endpoint = 'http://<15125683-actual-endpoint>'

    def __init__(self, service_key: str, allow_insecure_http_fallback: bool = False):
        self.service_key = service_key
        self.allow_insecure_http_fallback = allow_insecure_http_fallback

    def build_params(self) -> dict[str, str]:
        return {'serviceKey': self.service_key}

    def fetch_all(self) -> list[SubwayArrival]:
        ...

    def parse(self, xml_text: str) -> list[SubwayArrival]:
        ...
```

### 주의
- 실제 endpoint path/param 이름은 Swagger 확인 후 확정한다.
- 지금 단계에서는 **설계상 `fetch_all()`** 이 핵심이다.
- `station_name`을 받지 않는 이유는 데이터셋 설명이 일괄형이기 때문이다.

---

## Dashboard service 변경 설계

### 현재 구조
`_load_live_dashboard_data(profile)` 안에서 각 stop마다 `subway_provider.fetch(stop.name)`를 호출한다.

### 변경 후 구조

```python
def _load_live_dashboard_data(profile):
    settings = get_settings()
    ...

    if settings.subway_live_source == 'data_go_kr_batch':
        subway_provider = DataGoKrSeoulSubwayBatchProvider(
            service_key=settings.public_data_service_key,
            allow_insecure_http_fallback=allow_insecure_http_fallback,
        )
        all_subway = subway_provider.fetch_all()
        subway = _filter_subway_for_profile(profile, all_subway)
    else:
        subway_provider = SeoulSubwayArrivalProvider(
            service_key=settings.seoul_open_api_key or settings.public_data_service_key,
            allow_insecure_http_fallback=allow_insecure_http_fallback,
        )
        subway = []
        for stop in subway_stops:
            subway.extend(subway_provider.fetch(stop.name))
```

### 핵심 포인트
- 버스는 기존 방식 유지
- 지하철만 source strategy를 분기
- dashboard service가 provider 차이를 흡수

---

## Filtering 설계

### 왜 별도 함수가 필요한가
`15125683`가 전체역 feed면, 현재 `profile.stops`와 매칭하는 규칙이 중요하다.

### 신규 helper 제안

```python
def _filter_subway_for_profile(profile, all_subway):
    selected_station_ids = {stop.external_id for stop in profile.stops if stop.type == 'subway_station'}
    selected_station_names = {stop.name for stop in profile.stops if stop.type == 'subway_station'}

    return [
        item for item in all_subway
        if item.station_id in selected_station_ids or item.station_name in selected_station_names
    ]
```

### 매칭 우선순위
1. `station_id`
2. `station_name`

### 이유
- 역명 alias 문제를 줄이려면 가능한 한 `external_id` 우선이 안전하다.
- fixture/초기 구현에서는 이름 fallback을 남겨서 데이터셋 field 차이를 흡수한다.

---

## Parser 설계

`SubwayArrival` 스키마는 그대로 유지:

```python
class SubwayArrival(BaseModel):
    station_id: str
    station_name: str
    line_name: str
    direction: str
    arrival_in_sec: int
    train_type: str
```

### batch XML → 내부 스키마 매핑 원칙
실제 명세를 확인하기 전까지는 아래 원칙으로 parser를 만든다.

| 내부 필드 | 기대 원천 필드 후보 |
|---|---|
| `station_id` | `statnId`, `subwayStationId`, 유사 필드 |
| `station_name` | `statnNm`, `stationNm` |
| `line_name` | `trainLineNm`, `subwayNm`, `lineNm` |
| `direction` | `subwayHeading`, `updnLine`, `dir` |
| `arrival_in_sec` | `barvlDt`, 또는 도착예정시각 기반 계산 |
| `train_type` | `btrainSttus`, `trainType` |

### 가장 중요한 위험
`15125683`가 `barvlDt` 같은 초 단위 값을 안 주고, 생성시각 + 상태 문자열만 줄 수도 있다.
그 경우에는 두 단계로 가야 한다.

1. 1차: `arrival_in_sec`를 계산 가능한 경우만 채움
2. 2차: 계산 규칙이 불명확한 row는 제외하거나 `0` 처리 후 추천 로직 보호

초기 구현은 YAGNI 기준으로 **계산 가능한 필드만 사용**한다.

---

## 오류 처리 설계

새 provider도 기존 provider와 같은 계약을 유지한다.

### 규칙
- HTTP 오류 → `OSError('Failed to fetch live Seoul subway arrivals')`
- XML parse 오류 → `OSError('Failed to parse live Seoul subway arrivals')`
- 숫자 정규화/필드 매핑 오류 → `OSError('Failed to normalize live Seoul subway arrivals')`

이렇게 해야 `build_dashboard()`의 fallback 흐름을 건드리지 않아도 된다.

---

## 캐싱 설계

초기 MVP에서는 in-process 캐시만 고려한다.

### 이유
- 전체역 feed는 stop별 호출보다 payload가 클 수 있다.
- 한 요청마다 full fetch하면 낭비가 크다.

### 최소 제안
provider 내부가 아니라 service 레벨에 **짧은 TTL 캐시(예: 15~30초)** 를 두는 방향을 나중 단계로 남긴다.

하지만 1차 구현에서는 과도한 최적화 없이:
- 먼저 parser/필터링 정확성
- 그 다음 응답 크기/호출 빈도 관찰

순서로 간다.

---

## TDD 구현 순서

### Task 1: batch fixture 정의
**Objective:** `15125683` 가정 payload를 테스트 fixture로 고정한다.

**Files:**
- Create: `backend/tests/fixtures/data_go_kr_seoul_subway_batch.xml`
- Test: `backend/tests/services/test_data_go_kr_seoul_subway_batch.py`

**Test first:**
- fixture 안에 최소 2개 역 row 포함
- 그중 하나는 `상계역`
- parser 결과가 `station_id`, `station_name`, `arrival_in_sec`를 올바르게 채우는지 검증

---

### Task 2: batch provider parser 추가
**Objective:** XML payload를 `list[SubwayArrival]`로 바꾼다.

**Files:**
- Create: `backend/app/services/providers/data_go_kr_seoul_subway_batch.py`
- Test: `backend/tests/services/test_data_go_kr_seoul_subway_batch.py`

**Focused test cases:**
1. 정상 XML parse
2. non-XML payload 보호
3. 숫자 변환 실패 보호
4. 빈 row면 빈 리스트 반환

---

### Task 3: live fetch wrapper 추가
**Objective:** `fetch_all()`이 secure/insecure fallback 포함해 XML을 가져오게 한다.

**Files:**
- Modify: `backend/app/services/providers/data_go_kr_seoul_subway_batch.py`
- Test: `backend/tests/services/test_data_go_kr_seoul_subway_batch.py`

**Focused test cases:**
1. HTTPS 요청 URL/params 확인
2. `allow_insecure_http_fallback=True`일 때 HTTP 재시도
3. HTTP error → controlled `OSError`

---

### Task 4: dashboard source strategy 추가
**Objective:** `SUBWAY_LIVE_SOURCE`에 따라 `swopenapi` 또는 `data_go_kr_batch`를 고르게 한다.

**Files:**
- Modify: `backend/app/core/settings.py`
- Modify: `backend/app/services/dashboard_service.py`
- Test: `backend/tests/services/test_live_public_data.py`

**Focused test cases:**
1. `swopenapi`면 기존 provider 사용
2. `data_go_kr_batch`면 새 provider 사용
3. 새 provider 실패 시 fixture fallback 유지

---

### Task 5: profile 기반 filtering 강화
**Objective:** 전체역 feed에서 선택 역만 정확히 추린다.

**Files:**
- Modify: `backend/app/services/dashboard_service.py`
- Test: `backend/tests/services/test_live_public_data.py`

**Focused test cases:**
1. `external_id` 매칭 우선
2. 이름 fallback 매칭
3. 선택되지 않은 역은 제외

---

### Task 6: 문서화
**Objective:** 실제 운영자가 어떤 키/설정을 넣어야 하는지 혼동을 줄인다.

**Files:**
- Modify: `backend/.env.example`
- Modify: `README.md`
- Modify: `docs/README.md`

**문서 반영 내용:**
- `SUBWAY_LIVE_SOURCE=swopenapi|data_go_kr_batch`
- `data_go_kr_batch`는 `PUBLIC_DATA_SERVICE_KEY` 사용
- 현재 `15125683` Swagger 기준 확정 전까지는 experimental 경로임을 명시

---

## 테스트 전략

### 신규 테스트 파일
`backend/tests/services/test_data_go_kr_seoul_subway_batch.py`

포함할 테스트 예시:

```python
def test_batch_provider_parses_xml_fixture():
    ...


def test_batch_provider_fetches_live_xml(monkeypatch):
    ...


def test_batch_provider_retries_with_http_when_enabled(monkeypatch):
    ...


def test_batch_provider_raises_controlled_error_for_non_xml_payload(monkeypatch):
    ...
```

### 기존 테스트 확장
`backend/tests/services/test_live_public_data.py`

추가할 테스트 예시:

```python
def test_dashboard_uses_data_go_kr_subway_batch_when_configured(monkeypatch):
    ...


def test_dashboard_filters_batch_subway_rows_to_selected_station(monkeypatch):
    ...
```

### 검증 명령

```bash
cd /home/ptec07/.hermes/hermes-agent/workforce/commute-helper/backend
source .venv/bin/activate
pytest tests/services/test_data_go_kr_seoul_subway_batch.py -q
pytest tests/services/test_live_public_data.py -q
pytest tests/ -q
```

---

## 위험요소

### 1. 실제 15125683 명세 불확실
현재 가장 큰 리스크다. endpoint path/param/field 이름이 가정과 다를 수 있다.

**완화책:**
- 구현 전 Swagger/샘플 payload를 확보
- 확보 전까지는 fixture와 parser contract만 먼저 고정

### 2. `arrival_in_sec` 직접 계산 불가 가능성
전체역 feed가 초 단위 대신 상태 문자열/생성시각만 줄 수 있다.

**완화책:**
- 초기 parser는 계산 가능한 row만 수용
- recommendation engine에 빈 subway 리스트도 허용

### 3. payload 크기
전체역 일괄 데이터면 response가 커질 수 있다.

**완화책:**
- 초기는 단순 fetch
- 필요 시 TTL 캐시 추가

### 4. 역명 alias
선택 stop 이름과 live payload 이름이 다를 수 있다.

**완화책:**
- `external_id` 우선 매칭
- 이름 fallback은 보조로만 사용

---

## 추천 실행 순서

1. Swagger/샘플 payload 확보
2. fixture 작성
3. parser TDD 구현
4. fetch wrapper 구현
5. dashboard strategy 분기 추가
6. docs 정리

즉, **실제 endpoint 확인 전에는 provider 구현을 끝낸다고 가정하지 말고, parser와 strategy 설계만 먼저 굳히는 게 안전**하다.

---

## 구현 완료 기준

아래가 되면 설계 목표 달성으로 본다.

- `SUBWAY_LIVE_SOURCE=data_go_kr_batch`일 때 새 provider가 호출된다.
- batch payload에서 `상계역` 같은 선택 역만 필터링된다.
- 새 provider 실패 시에도 dashboard는 fixture fallback으로 200 응답한다.
- `README`와 `.env.example`가 키/설정 조건을 정확히 설명한다.
- backend 전체 테스트가 모두 통과한다.

---

## 최종 추천

바로 기존 provider를 갈아치우지 말고, **`swopenapi` 유지 + `data_go_kr_batch` 실험 경로 추가**가 가장 안전하다. 현재 프로젝트 상태와 민규의 범위 통제 선호를 고려하면, 이 설계가 리스크 대비 이득이 가장 크다.
