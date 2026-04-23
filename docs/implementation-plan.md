# 출근도우미 MVP Implementation Plan

> **For Hermes:** Use subagent-driven-development skill to implement this plan task-by-task.

**Goal:** 서울 직장인을 위한 모바일 우선 웹앱을 만들어, 저장된 통근 프로필 기준으로 실시간 버스/지하철 정보를 모아 현재 출발 추천을 제공한다.

**Architecture:** FastAPI 백엔드가 서울 공공데이터 API(XML/JSON)를 정규화·캐시·추천 계산하고, React 프론트엔드가 통근 프로필 설정과 실시간 대시보드를 제공한다. MVP 범위는 서울 한정, 프로필/정류장/역 등록, 실시간 조회, 룰베이스 추천까지로 제한한다.

**Tech Stack:** FastAPI, SQLAlchemy, Pydantic, pytest, httpx, PostgreSQL(or SQLite for dev), React + Vite, TypeScript, Vitest, React Testing Library, TanStack Query, Tailwind CSS

---

## Ground Rules

- Always follow strict TDD: write the failing test first, run it to verify failure, then implement the minimum code to pass.
- Keep each commit small and scoped to one task.
- Do not add auth, maps, push notifications, or nationwide support in MVP.
- Normalize all external provider responses before exposing them to the frontend.
- If any public API response shape is unclear, save sample payloads in tests/fixtures before implementing parsing logic.

---

## Suggested Repository Layout

```text
commute-helper/
  backend/
    app/
      api/routes/
      core/
      db/
      models/
      schemas/
      services/
      services/providers/
    tests/
      api/
      services/
      fixtures/
  frontend/
    src/
      components/
      pages/
      lib/
      hooks/
      test/
```

---

### Task 1: Scaffold the repository and toolchain

**Objective:** Create backend/frontend skeletons with test runners configured before feature work starts.

**Files:**
- Create: `commute-helper/backend/pyproject.toml`
- Create: `commute-helper/backend/app/main.py`
- Create: `commute-helper/backend/tests/test_smoke.py`
- Create: `commute-helper/frontend/package.json`
- Create: `commute-helper/frontend/vite.config.ts`
- Create: `commute-helper/frontend/src/test/smoke.test.tsx`
- Create: `commute-helper/README.md`

**Step 1: Write failing backend smoke test**

```python
from fastapi.testclient import TestClient
from app.main import app


def test_health_endpoint_returns_ok():
    client = TestClient(app)
    response = client.get('/health')
    assert response.status_code == 200
    assert response.json() == {'status': 'ok'}
```

**Step 2: Run test to verify failure**

Run: `cd commute-helper/backend && pytest tests/test_smoke.py::test_health_endpoint_returns_ok -v`
Expected: FAIL — `ModuleNotFoundError` or missing `/health` route.

**Step 3: Write minimal backend implementation**

```python
from fastapi import FastAPI

app = FastAPI()


@app.get('/health')
def health() -> dict[str, str]:
    return {'status': 'ok'}
```

**Step 4: Write failing frontend smoke test**

```tsx
import { render, screen } from '@testing-library/react'
import { App } from '../App'

test('renders service name', () => {
  render(<App />)
  expect(screen.getByText('출근도우미')).toBeInTheDocument()
})
```

**Step 5: Run frontend test to verify failure**

Run: `cd commute-helper/frontend && npm test -- --runInBand smoke.test.tsx`
Expected: FAIL — missing `App` component or missing text.

**Step 6: Write minimal frontend implementation**

```tsx
export function App() {
  return <main>출근도우미</main>
}
```

**Step 7: Verify tests pass**

Run:
- `cd commute-helper/backend && pytest tests/test_smoke.py -v`
- `cd commute-helper/frontend && npm test -- --runInBand smoke.test.tsx`
Expected: PASS

**Step 8: Commit**

```bash
git add commute-helper
git commit -m "chore: scaffold commute helper backend and frontend"
```

---

### Task 2: Add backend settings and database session bootstrap

**Objective:** Create application settings and database session plumbing used by later models and routes.

**Files:**
- Create: `commute-helper/backend/app/core/settings.py`
- Create: `commute-helper/backend/app/db/session.py`
- Create: `commute-helper/backend/app/db/base.py`
- Test: `commute-helper/backend/tests/test_settings.py`

**Step 1: Write failing test**

```python
from app.core.settings import get_settings


def test_default_settings_use_sqlite_for_dev():
    settings = get_settings()
    assert settings.app_name == '출근도우미'
    assert settings.database_url.startswith('sqlite')
```

**Step 2: Run test to verify failure**

Run: `cd commute-helper/backend && pytest tests/test_settings.py::test_default_settings_use_sqlite_for_dev -v`
Expected: FAIL — settings module missing.

**Step 3: Write minimal implementation**

```python
from functools import lru_cache
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = '출근도우미'
    database_url: str = 'sqlite:///./commute_helper.db'


@lru_cache
def get_settings() -> Settings:
    return Settings()
```

**Step 4: Verify pass**

Run: `cd commute-helper/backend && pytest tests/test_settings.py::test_default_settings_use_sqlite_for_dev -v`
Expected: PASS

**Step 5: Add SQLAlchemy session/base setup**

Create `app/db/base.py` and `app/db/session.py` with `DeclarativeBase`, engine, and `sessionmaker` using `get_settings().database_url`.

**Step 6: Run focused test plus smoke suite**

Run: `cd commute-helper/backend && pytest tests/test_settings.py tests/test_smoke.py -v`
Expected: PASS

**Step 7: Commit**

```bash
git add commute-helper/backend/app commute-helper/backend/tests
git commit -m "chore: add backend settings and db bootstrap"
```

---

### Task 3: Model the commute profile entity

**Objective:** Add the primary database model and schema for a commute profile.

**Files:**
- Create: `commute-helper/backend/app/models/commute_profile.py`
- Create: `commute-helper/backend/app/schemas/profile.py`
- Modify: `commute-helper/backend/app/db/base.py`
- Test: `commute-helper/backend/tests/models/test_commute_profile.py`

**Step 1: Write failing test**

```python
from app.models.commute_profile import CommuteProfile


def test_commute_profile_defaults_balanced_mode():
    profile = CommuteProfile(
        name='회사 가기',
        origin_label='집',
        destination_label='회사',
        target_arrival_time='09:00:00',
    )
    assert profile.preferred_mode == 'balanced'
```

**Step 2: Run test to verify failure**

Run: `cd commute-helper/backend && pytest tests/models/test_commute_profile.py::test_commute_profile_defaults_balanced_mode -v`
Expected: FAIL — model missing.

**Step 3: Write minimal implementation**

Implement SQLAlchemy model with fields:
- `id`
- `name`
- `origin_label`
- `destination_label`
- `target_arrival_time`
- `preferred_mode='balanced'`
- `walking_tolerance_min=10`
- timestamps

Create matching Pydantic create/read schemas.

**Step 4: Verify pass**

Run: `cd commute-helper/backend && pytest tests/models/test_commute_profile.py::test_commute_profile_defaults_balanced_mode -v`
Expected: PASS

**Step 5: Run broader backend suite**

Run: `cd commute-helper/backend && pytest tests/ -q`
Expected: PASS

**Step 6: Commit**

```bash
git add commute-helper/backend/app commute-helper/backend/tests
git commit -m "feat: add commute profile model"
```

---

### Task 4: Model commute stops for bus stops and subway stations

**Objective:** Represent saved bus stops and subway stations linked to a profile.

**Files:**
- Create: `commute-helper/backend/app/models/commute_stop.py`
- Modify: `commute-helper/backend/app/models/commute_profile.py`
- Modify: `commute-helper/backend/app/schemas/profile.py`
- Test: `commute-helper/backend/tests/models/test_commute_stop.py`

**Step 1: Write failing test**

```python
from app.models.commute_stop import CommuteStop


def test_commute_stop_requires_supported_type():
    stop = CommuteStop(type='tram_stop', external_id='x', name='x', sort_order=1)
    assert stop.validate_type() == 'tram_stop'
```

**Step 2: Run test to verify failure**

Run: `cd commute-helper/backend && pytest tests/models/test_commute_stop.py::test_commute_stop_requires_supported_type -v`
Expected: FAIL — missing model or validator.

**Step 3: Implement minimal code**

Implement `CommuteStop` model with allowed `type` values `bus_stop` and `subway_station`; make invalid values raise `ValueError`.

**Step 4: Replace the test with the actual expected behavior if needed**

Use the final passing test shape:

```python
import pytest
from app.models.commute_stop import CommuteStop


def test_commute_stop_rejects_unsupported_type():
    with pytest.raises(ValueError):
        CommuteStop(type='tram_stop', external_id='x', name='x', sort_order=1)
```

**Step 5: Verify red then green**

Run twice:
- Before implementation: FAIL for missing validation
- After implementation: PASS

**Step 6: Run related tests**

Run: `cd commute-helper/backend && pytest tests/models/test_commute_profile.py tests/models/test_commute_stop.py -v`
Expected: PASS

**Step 7: Commit**

```bash
git add commute-helper/backend/app commute-helper/backend/tests/models
git commit -m "feat: add commute stop model"
```

---

### Task 5: Add provider-normalized schemas

**Objective:** Define the internal normalized response shapes for bus arrival, bus position, subway arrival, and recommendation output.

**Files:**
- Create: `commute-helper/backend/app/schemas/provider_models.py`
- Create: `commute-helper/backend/app/schemas/dashboard.py`
- Create: `commute-helper/backend/tests/schemas/test_provider_models.py`

**Step 1: Write failing test**

```python
from app.schemas.provider_models import BusArrival


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
```

**Step 2: Run test to verify failure**

Run: `cd commute-helper/backend && pytest tests/schemas/test_provider_models.py::test_bus_arrival_computes_display_minutes -v`
Expected: FAIL — schema missing.

**Step 3: Write minimal implementation**

Create Pydantic models:
- `BusArrival`
- `BusPosition`
- `SubwayArrival`
- `RecommendationResult`
- dashboard response wrapper schemas

Add a computed property for display minutes.

**Step 4: Verify pass**

Run: `cd commute-helper/backend && pytest tests/schemas/test_provider_models.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add commute-helper/backend/app/schemas commute-helper/backend/tests/schemas
git commit -m "feat: add normalized provider schemas"
```

---

### Task 6: Add sample fixtures for public provider payloads

**Objective:** Capture representative API payloads before writing parsers.

**Files:**
- Create: `commute-helper/backend/tests/fixtures/seoul_bus_arrival.xml`
- Create: `commute-helper/backend/tests/fixtures/seoul_bus_position.json`
- Create: `commute-helper/backend/tests/fixtures/seoul_subway_arrival.xml`
- Create: `commute-helper/backend/tests/fixtures/seoul_citydata.xml`
- Create: `commute-helper/backend/tests/services/test_fixture_sanity.py`

**Step 1: Write failing test**

```python
from pathlib import Path


def test_provider_fixture_files_exist():
    fixtures = [
        'seoul_bus_arrival.xml',
        'seoul_bus_position.json',
        'seoul_subway_arrival.xml',
    ]
    root = Path('tests/fixtures')
    for name in fixtures:
        assert (root / name).exists(), name
```

**Step 2: Run test to verify failure**

Run: `cd commute-helper/backend && pytest tests/services/test_fixture_sanity.py::test_provider_fixture_files_exist -v`
Expected: FAIL — fixture files missing.

**Step 3: Add the fixture files**

Save minimal but realistic payloads copied from docs or manually curated examples. Strip secrets. Keep one success case per provider.

**Step 4: Verify pass**

Run: `cd commute-helper/backend && pytest tests/services/test_fixture_sanity.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add commute-helper/backend/tests/fixtures commute-helper/backend/tests/services
git commit -m "test: add provider payload fixtures"
```

---

### Task 7: Parse and normalize Seoul bus arrival responses

**Objective:** Convert raw Seoul bus arrival XML into internal `BusArrival` objects.

**Files:**
- Create: `commute-helper/backend/app/services/providers/seoul_bus_arrival.py`
- Test: `commute-helper/backend/tests/services/test_seoul_bus_arrival.py`

**Step 1: Write failing test**

```python
from pathlib import Path
from app.services.providers.seoul_bus_arrival import SeoulBusArrivalProvider


def test_parses_bus_arrival_fixture_into_normalized_objects():
    xml_text = Path('tests/fixtures/seoul_bus_arrival.xml').read_text(encoding='utf-8')
    provider = SeoulBusArrivalProvider(service_key='dummy')

    arrivals = provider.parse(xml_text)

    assert arrivals[0].route_name == '146'
    assert arrivals[0].arrival_in_sec == 240
```

**Step 2: Run test to verify failure**

Run: `cd commute-helper/backend && pytest tests/services/test_seoul_bus_arrival.py::test_parses_bus_arrival_fixture_into_normalized_objects -v`
Expected: FAIL — provider missing.

**Step 3: Implement minimal parser**

Required methods:
- `build_params(stop_id: str, route_id: str | None = None) -> dict`
- `parse(xml_text: str) -> list[BusArrival]`
- `normalize(...)` if you split parse and normalize

**Step 4: Verify pass**

Run: `cd commute-helper/backend && pytest tests/services/test_seoul_bus_arrival.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add commute-helper/backend/app/services/providers commute-helper/backend/tests/services
git commit -m "feat: add Seoul bus arrival provider"
```

---

### Task 8: Parse and normalize Seoul bus position responses

**Objective:** Convert raw Seoul bus position payloads into internal `BusPosition` objects.

**Files:**
- Create: `commute-helper/backend/app/services/providers/seoul_bus_position.py`
- Test: `commute-helper/backend/tests/services/test_seoul_bus_position.py`

**Step 1: Write failing test**

```python
from pathlib import Path
from app.services.providers.seoul_bus_position import SeoulBusPositionProvider


def test_parses_bus_position_fixture_into_normalized_objects():
    payload = Path('tests/fixtures/seoul_bus_position.json').read_text(encoding='utf-8')
    provider = SeoulBusPositionProvider(service_key='dummy')

    positions = provider.parse(payload)

    assert positions[0].station_count_from_target == 2
```

**Step 2: Run test to verify failure**

Run: `cd commute-helper/backend && pytest tests/services/test_seoul_bus_position.py::test_parses_bus_position_fixture_into_normalized_objects -v`
Expected: FAIL — provider missing.

**Step 3: Implement minimal parser**

Normalize at least:
- `route_id`
- `vehicle_id`
- `station_count_from_target`
- `congestion_level`

**Step 4: Verify pass**

Run: `cd commute-helper/backend && pytest tests/services/test_seoul_bus_position.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add commute-helper/backend/app/services/providers commute-helper/backend/tests/services
git commit -m "feat: add Seoul bus position provider"
```

---

### Task 9: Parse and normalize Seoul subway arrival responses

**Objective:** Convert raw Seoul subway arrival XML into internal `SubwayArrival` objects.

**Files:**
- Create: `commute-helper/backend/app/services/providers/seoul_subway_arrival.py`
- Test: `commute-helper/backend/tests/services/test_seoul_subway_arrival.py`

**Step 1: Write failing test**

```python
from pathlib import Path
from app.services.providers.seoul_subway_arrival import SeoulSubwayArrivalProvider


def test_parses_subway_arrival_fixture_into_normalized_objects():
    xml_text = Path('tests/fixtures/seoul_subway_arrival.xml').read_text(encoding='utf-8')
    provider = SeoulSubwayArrivalProvider(service_key='dummy')

    arrivals = provider.parse(xml_text)

    assert arrivals[0].station_name == '상계역'
    assert arrivals[0].arrival_in_sec == 420
```

**Step 2: Run test to verify failure**

Run: `cd commute-helper/backend && pytest tests/services/test_seoul_subway_arrival.py::test_parses_subway_arrival_fixture_into_normalized_objects -v`
Expected: FAIL — provider missing.

**Step 3: Implement minimal parser**

Normalize at least:
- `station_id`
- `station_name`
- `line_name`
- `direction`
- `arrival_in_sec`
- `train_type`

**Step 4: Verify pass**

Run: `cd commute-helper/backend && pytest tests/services/test_seoul_subway_arrival.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add commute-helper/backend/app/services/providers commute-helper/backend/tests/services
git commit -m "feat: add Seoul subway arrival provider"
```

---

### Task 10: Add realtime cache model and repository helper

**Objective:** Cache external API responses for short TTLs so dashboard refreshes do not hammer providers.

**Files:**
- Create: `commute-helper/backend/app/models/realtime_cache.py`
- Create: `commute-helper/backend/app/services/cache_service.py`
- Modify: `commute-helper/backend/app/db/base.py`
- Test: `commute-helper/backend/tests/services/test_cache_service.py`

**Step 1: Write failing test**

```python
from datetime import datetime, timedelta
from app.services.cache_service import is_cache_valid


def test_cache_is_valid_before_expiry():
    now = datetime.utcnow()
    assert is_cache_valid(now + timedelta(seconds=30), now) is True
```

**Step 2: Run test to verify failure**

Run: `cd commute-helper/backend && pytest tests/services/test_cache_service.py::test_cache_is_valid_before_expiry -v`
Expected: FAIL — service missing.

**Step 3: Implement minimal code**

Add TTL-aware helper plus model fields:
- `source`
- `cache_key`
- `payload`
- `fetched_at`
- `expires_at`

**Step 4: Verify pass**

Run: `cd commute-helper/backend && pytest tests/services/test_cache_service.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add commute-helper/backend/app/models commute-helper/backend/app/services commute-helper/backend/tests/services
git commit -m "feat: add realtime cache service"
```

---

### Task 11: Build recommendation service with simple scoring

**Objective:** Implement the initial rules that choose bus, subway, or neutral recommendation.

**Files:**
- Create: `commute-helper/backend/app/services/recommendation_service.py`
- Create: `commute-helper/backend/tests/services/test_recommendation_service.py`

**Step 1: Write failing test**

```python
from app.schemas.provider_models import BusArrival, SubwayArrival
from app.services.recommendation_service import recommend_mode


def test_recommends_bus_when_bus_arrives_meaningfully_sooner():
    bus = [BusArrival(route_id='r1', route_name='146', stop_id='s1', stop_name='정류장', arrival_in_sec=240, arrival_message='4분 후', is_last_bus=False)]
    subway = [SubwayArrival(station_id='st1', station_name='상계역', line_name='4호선', direction='오이도', arrival_in_sec=600, train_type='일반')]

    result = recommend_mode(bus=bus, subway=subway, preferred_mode='balanced', target_arrival_time='09:00')

    assert result.mode == 'bus'
    assert '버스' in result.message
```

**Step 2: Run test to verify failure**

Run: `cd commute-helper/backend && pytest tests/services/test_recommendation_service.py::test_recommends_bus_when_bus_arrives_meaningfully_sooner -v`
Expected: FAIL — service missing.

**Step 3: Implement minimal recommendation logic**

Minimum rules:
- compare earliest bus vs earliest subway arrival
- apply small bonus for preferred mode
- return message, reason, and `leave_by`

**Step 4: Add one more failing test for preference tiebreaker**

```python
def test_uses_preference_when_scores_are_close():
    ...
```

Verify failure, then implement the tiebreaker.

**Step 5: Verify pass and run broader service tests**

Run: `cd commute-helper/backend && pytest tests/services/test_recommendation_service.py tests/services/test_seoul_*.py -v`
Expected: PASS

**Step 6: Commit**

```bash
git add commute-helper/backend/app/services commute-helper/backend/tests/services
git commit -m "feat: add recommendation service"
```

---

### Task 12: Add commute profile create/list API

**Objective:** Expose CRUD-lite endpoints for commute profiles.

**Files:**
- Create: `commute-helper/backend/app/api/routes/profiles.py`
- Modify: `commute-helper/backend/app/main.py`
- Test: `commute-helper/backend/tests/api/test_profiles_api.py`

**Step 1: Write failing test**

```python
from fastapi.testclient import TestClient
from app.main import app


def test_create_profile_returns_created_profile():
    client = TestClient(app)
    response = client.post('/api/commute-profiles', json={
        'name': '회사 가기',
        'originLabel': '집',
        'destinationLabel': '회사',
        'targetArrivalTime': '09:00',
        'preferredMode': 'balanced',
        'walkingToleranceMin': 10,
    })

    assert response.status_code == 201
    assert response.json()['name'] == '회사 가기'
```

**Step 2: Run test to verify failure**

Run: `cd commute-helper/backend && pytest tests/api/test_profiles_api.py::test_create_profile_returns_created_profile -v`
Expected: FAIL — route missing.

**Step 3: Implement minimal route**

Add:
- `POST /api/commute-profiles`
- `GET /api/commute-profiles`

Use in-memory list only if needed to make the test pass quickly, then refactor to DB-backed in the same task before broad tests.

**Step 4: Verify pass**

Run: `cd commute-helper/backend && pytest tests/api/test_profiles_api.py -v`
Expected: PASS

**Step 5: Run full backend suite**

Run: `cd commute-helper/backend && pytest tests/ -q`
Expected: PASS

**Step 6: Commit**

```bash
git add commute-helper/backend/app commute-helper/backend/tests/api
git commit -m "feat: add commute profile api"
```

---

### Task 13: Add commute stop create API

**Objective:** Allow bus stops and subway stations to be linked to a profile.

**Files:**
- Modify: `commute-helper/backend/app/api/routes/profiles.py`
- Test: `commute-helper/backend/tests/api/test_profile_stops_api.py`

**Step 1: Write failing test**

```python
from fastapi.testclient import TestClient
from app.main import app


def test_add_stop_to_profile():
    client = TestClient(app)
    create = client.post('/api/commute-profiles', json={
        'name': '회사 가기',
        'originLabel': '집',
        'destinationLabel': '회사',
        'targetArrivalTime': '09:00',
        'preferredMode': 'balanced',
        'walkingToleranceMin': 10,
    }).json()

    response = client.post(f"/api/commute-profiles/{create['id']}/stops", json={
        'type': 'subway_station',
        'externalId': 'station-100',
        'name': '상계역',
        'lineName': '4호선',
        'direction': '오이도방향',
        'sortOrder': 1,
    })

    assert response.status_code == 201
    assert response.json()['name'] == '상계역'
```

**Step 2: Run test to verify failure**

Run: `cd commute-helper/backend && pytest tests/api/test_profile_stops_api.py::test_add_stop_to_profile -v`
Expected: FAIL — route missing.

**Step 3: Implement minimal route**

Add `POST /api/commute-profiles/{id}/stops` with validation.

**Step 4: Verify pass**

Run: `cd commute-helper/backend && pytest tests/api/test_profile_stops_api.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add commute-helper/backend/app/api commute-helper/backend/tests/api
git commit -m "feat: add commute stop api"
```

---

### Task 14: Build dashboard aggregation service

**Objective:** Fetch saved stops, collect realtime provider data, and produce one dashboard response.

**Files:**
- Create: `commute-helper/backend/app/services/dashboard_service.py`
- Create: `commute-helper/backend/tests/services/test_dashboard_service.py`

**Step 1: Write failing test**

```python
from app.services.dashboard_service import build_dashboard


def test_dashboard_combines_bus_subway_and_recommendation(fake_profile, fake_bus_provider, fake_subway_provider):
    dashboard = build_dashboard(
        profile=fake_profile,
        bus_provider=fake_bus_provider,
        subway_provider=fake_subway_provider,
        position_provider=None,
    )

    assert dashboard.recommendation.mode in {'bus', 'subway', 'balanced'}
    assert dashboard.profile.name == '회사 가기'
```

**Step 2: Run test to verify failure**

Run: `cd commute-helper/backend && pytest tests/services/test_dashboard_service.py::test_dashboard_combines_bus_subway_and_recommendation -v`
Expected: FAIL — service missing.

**Step 3: Implement minimal service**

Inject providers rather than importing them directly; aggregate earliest arrivals and recommendation.

**Step 4: Verify pass**

Run: `cd commute-helper/backend && pytest tests/services/test_dashboard_service.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add commute-helper/backend/app/services commute-helper/backend/tests/services
git commit -m "feat: add dashboard aggregation service"
```

---

### Task 15: Add dashboard API route

**Objective:** Expose the unified dashboard payload to the frontend.

**Files:**
- Create: `commute-helper/backend/app/api/routes/dashboard.py`
- Modify: `commute-helper/backend/app/main.py`
- Test: `commute-helper/backend/tests/api/test_dashboard_api.py`

**Step 1: Write failing test**

```python
from fastapi.testclient import TestClient
from app.main import app


def test_dashboard_endpoint_returns_recommendation(seed_profile):
    client = TestClient(app)
    response = client.get(f'/api/dashboard/{seed_profile}')
    assert response.status_code == 200
    assert 'recommendation' in response.json()
```

**Step 2: Run test to verify failure**

Run: `cd commute-helper/backend && pytest tests/api/test_dashboard_api.py::test_dashboard_endpoint_returns_recommendation -v`
Expected: FAIL — route missing.

**Step 3: Implement minimal route**

Wire `GET /api/dashboard/{commute_profile_id}` to the dashboard service.

**Step 4: Verify pass**

Run: `cd commute-helper/backend && pytest tests/api/test_dashboard_api.py -v`
Expected: PASS

**Step 5: Run full backend suite**

Run: `cd commute-helper/backend && pytest tests/ -q`
Expected: PASS

**Step 6: Commit**

```bash
git add commute-helper/backend/app commute-helper/backend/tests/api
git commit -m "feat: add dashboard api"
```

---

### Task 16: Add stop search API backed by static fixture data

**Objective:** Support the frontend auto-complete flow without prematurely solving full station indexing.

**Files:**
- Create: `commute-helper/backend/app/services/search_service.py`
- Create: `commute-helper/backend/app/api/routes/search.py`
- Create: `commute-helper/backend/tests/fixtures/station_index.json`
- Create: `commute-helper/backend/tests/api/test_search_api.py`

**Step 1: Write failing test**

```python
from fastapi.testclient import TestClient
from app.main import app


def test_search_returns_matching_subway_station():
    client = TestClient(app)
    response = client.get('/api/search/stops?q=상계역')
    assert response.status_code == 200
    assert response.json()['subwayStations'][0]['name'] == '상계역'
```

**Step 2: Run test to verify failure**

Run: `cd commute-helper/backend && pytest tests/api/test_search_api.py::test_search_returns_matching_subway_station -v`
Expected: FAIL — route missing.

**Step 3: Implement minimal search service**

Load a small local JSON index for MVP development. Do not integrate another live API yet.

**Step 4: Verify pass**

Run: `cd commute-helper/backend && pytest tests/api/test_search_api.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add commute-helper/backend/app/services commute-helper/backend/app/api commute-helper/backend/tests
git commit -m "feat: add stop search api"
```

---

### Task 17: Create frontend API client and dashboard types

**Objective:** Give the frontend a typed client for profile, stop, search, and dashboard endpoints.

**Files:**
- Create: `commute-helper/frontend/src/lib/api.ts`
- Create: `commute-helper/frontend/src/lib/types.ts`
- Create: `commute-helper/frontend/src/test/api.test.ts`

**Step 1: Write failing test**

```tsx
import { buildDashboardUrl } from '../lib/api'

test('builds dashboard url from profile id', () => {
  expect(buildDashboardUrl('abc')).toBe('/api/dashboard/abc')
})
```

**Step 2: Run test to verify failure**

Run: `cd commute-helper/frontend && npm test -- --runInBand src/test/api.test.ts`
Expected: FAIL — helper missing.

**Step 3: Implement minimal client helpers**

Add typed fetch wrappers:
- `listProfiles`
- `createProfile`
- `addStop`
- `getDashboard`
- `searchStops`

**Step 4: Verify pass**

Run: `cd commute-helper/frontend && npm test -- --runInBand src/test/api.test.ts`
Expected: PASS

**Step 5: Commit**

```bash
git add commute-helper/frontend/src/lib commute-helper/frontend/src/test
git commit -m "feat: add frontend api client"
```

---

### Task 18: Build the profile creation form

**Objective:** Let users create a commute profile from the UI.

**Files:**
- Create: `commute-helper/frontend/src/components/ProfileForm.tsx`
- Create: `commute-helper/frontend/src/pages/NewProfilePage.tsx`
- Create: `commute-helper/frontend/src/test/ProfileForm.test.tsx`

**Step 1: Write failing test**

```tsx
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { ProfileForm } from '../components/ProfileForm'

test('submits commute profile values', async () => {
  const user = userEvent.setup()
  const onSubmit = vi.fn()
  render(<ProfileForm onSubmit={onSubmit} />)

  await user.type(screen.getByLabelText('프로필 이름'), '회사 가기')
  await user.click(screen.getByRole('button', { name: '저장' }))

  expect(onSubmit).toHaveBeenCalled()
})
```

**Step 2: Run test to verify failure**

Run: `cd commute-helper/frontend && npm test -- --runInBand src/test/ProfileForm.test.tsx`
Expected: FAIL — component missing.

**Step 3: Implement minimal form**

Include fields:
- 프로필 이름
- 출발지 라벨
- 도착지 라벨
- 목표 도착 시각
- 선호 수단
- 도보 허용 시간

**Step 4: Verify pass**

Run: `cd commute-helper/frontend && npm test -- --runInBand src/test/ProfileForm.test.tsx`
Expected: PASS

**Step 5: Commit**

```bash
git add commute-helper/frontend/src/components commute-helper/frontend/src/pages commute-helper/frontend/src/test
git commit -m "feat: add profile form"
```

---

### Task 19: Build the stop search and selection UI

**Objective:** Let users attach one bus stop and one subway station to a profile.

**Files:**
- Create: `commute-helper/frontend/src/components/StopSearchInput.tsx`
- Create: `commute-helper/frontend/src/components/SelectedStopsList.tsx`
- Create: `commute-helper/frontend/src/test/StopSearchInput.test.tsx`

**Step 1: Write failing test**

```tsx
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { StopSearchInput } from '../components/StopSearchInput'

test('shows matching station results', async () => {
  const user = userEvent.setup()
  const searchStops = vi.fn().mockResolvedValue({ busStops: [], subwayStations: [{ externalId: '1', name: '상계역', lineName: '4호선' }] })
  render(<StopSearchInput searchStops={searchStops} onSelect={vi.fn()} />)

  await user.type(screen.getByLabelText('정류장 또는 역 검색'), '상계역')
  expect(await screen.findByText('상계역')).toBeInTheDocument()
})
```

**Step 2: Run test to verify failure**

Run: `cd commute-helper/frontend && npm test -- --runInBand src/test/StopSearchInput.test.tsx`
Expected: FAIL — component missing.

**Step 3: Implement minimal UI**

Use debounced search input, result list, and selection callback.

**Step 4: Verify pass**

Run: `cd commute-helper/frontend && npm test -- --runInBand src/test/StopSearchInput.test.tsx`
Expected: PASS

**Step 5: Commit**

```bash
git add commute-helper/frontend/src/components commute-helper/frontend/src/test
git commit -m "feat: add stop search input"
```

---

### Task 20: Build the recommendation dashboard UI

**Objective:** Render the backend dashboard payload into a mobile-friendly first screen.

**Files:**
- Create: `commute-helper/frontend/src/components/RecommendationCard.tsx`
- Create: `commute-helper/frontend/src/components/BusArrivalCard.tsx`
- Create: `commute-helper/frontend/src/components/SubwayArrivalCard.tsx`
- Create: `commute-helper/frontend/src/pages/DashboardPage.tsx`
- Create: `commute-helper/frontend/src/test/DashboardPage.test.tsx`

**Step 1: Write failing test**

```tsx
import { render, screen } from '@testing-library/react'
import { DashboardPage } from '../pages/DashboardPage'

test('renders recommendation message from dashboard payload', async () => {
  const getDashboard = vi.fn().mockResolvedValue({
    profile: { id: '1', name: '회사 가기', targetArrivalTime: '09:00' },
    bus: [],
    subway: [],
    recommendation: { mode: 'bus', message: '지금 출발하면 버스가 더 유리합니다.', reason: '버스가 빨리 옵니다.', leaveBy: '08:17' },
  })

  render(<DashboardPage profileId='1' getDashboard={getDashboard} />)
  expect(await screen.findByText('지금 출발하면 버스가 더 유리합니다.')).toBeInTheDocument()
})
```

**Step 2: Run test to verify failure**

Run: `cd commute-helper/frontend && npm test -- --runInBand src/test/DashboardPage.test.tsx`
Expected: FAIL — page missing.

**Step 3: Implement minimal UI**

Render:
- profile name
- target arrival time
- recommendation card
- bus list
- subway list

**Step 4: Verify pass**

Run: `cd commute-helper/frontend && npm test -- --runInBand src/test/DashboardPage.test.tsx`
Expected: PASS

**Step 5: Run all frontend tests**

Run: `cd commute-helper/frontend && npm test -- --runInBand`
Expected: PASS

**Step 6: Commit**

```bash
git add commute-helper/frontend/src/components commute-helper/frontend/src/pages commute-helper/frontend/src/test
git commit -m "feat: add dashboard ui"
```

---

### Task 21: Wire the app shell and happy-path navigation

**Objective:** Connect profile creation, stop selection, and dashboard viewing into one user flow.

**Files:**
- Modify: `commute-helper/frontend/src/App.tsx`
- Modify: `commute-helper/frontend/src/pages/NewProfilePage.tsx`
- Modify: `commute-helper/frontend/src/pages/DashboardPage.tsx`
- Create: `commute-helper/frontend/src/test/AppFlow.test.tsx`

**Step 1: Write failing test**

```tsx
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { App } from '../App'

test('allows user to move from profile setup to dashboard', async () => {
  const user = userEvent.setup()
  render(<App />)

  expect(screen.getByText('출근도우미')).toBeInTheDocument()
  await user.click(screen.getByRole('button', { name: '통근 프로필 만들기' }))
  expect(await screen.findByLabelText('프로필 이름')).toBeInTheDocument()
})
```

**Step 2: Run test to verify failure**

Run: `cd commute-helper/frontend && npm test -- --runInBand src/test/AppFlow.test.tsx`
Expected: FAIL — app flow missing.

**Step 3: Implement minimal navigation**

Simple local state routing is acceptable for MVP; do not add heavy routing unless already needed.

**Step 4: Verify pass**

Run: `cd commute-helper/frontend && npm test -- --runInBand src/test/AppFlow.test.tsx`
Expected: PASS

**Step 5: Run all frontend tests**

Run: `cd commute-helper/frontend && npm test -- --runInBand`
Expected: PASS

**Step 6: Commit**

```bash
git add commute-helper/frontend/src
git commit -m "feat: wire mvp app flow"
```

---

### Task 22: Add backend integration test for the full dashboard flow

**Objective:** Prove the API can create a profile, attach stops, and return a dashboard payload end-to-end.

**Files:**
- Create: `commute-helper/backend/tests/api/test_dashboard_flow_api.py`

**Step 1: Write failing test**

```python
from fastapi.testclient import TestClient
from app.main import app


def test_full_dashboard_flow_returns_recommendation():
    client = TestClient(app)
    profile = client.post('/api/commute-profiles', json={
        'name': '회사 가기',
        'originLabel': '집',
        'destinationLabel': '회사',
        'targetArrivalTime': '09:00',
        'preferredMode': 'balanced',
        'walkingToleranceMin': 10,
    }).json()

    client.post(f"/api/commute-profiles/{profile['id']}/stops", json={
        'type': 'subway_station', 'externalId': 'station-100', 'name': '상계역', 'lineName': '4호선', 'direction': '오이도방향', 'sortOrder': 1,
    })

    response = client.get(f"/api/dashboard/{profile['id']}")
    assert response.status_code == 200
    assert response.json()['profile']['name'] == '회사 가기'
    assert 'message' in response.json()['recommendation']
```

**Step 2: Run test to verify failure**

Run: `cd commute-helper/backend && pytest tests/api/test_dashboard_flow_api.py::test_full_dashboard_flow_returns_recommendation -v`
Expected: FAIL until the full stack is wired.

**Step 3: Implement whatever glue is still missing**

Do not broaden scope. Only add the minimal dependency wiring, seed data fallback, or fixture-backed provider stubs needed for MVP integration.

**Step 4: Verify pass**

Run: `cd commute-helper/backend && pytest tests/api/test_dashboard_flow_api.py -v`
Expected: PASS

**Step 5: Run full backend suite**

Run: `cd commute-helper/backend && pytest tests/ -q`
Expected: PASS

**Step 6: Commit**

```bash
git add commute-helper/backend/tests/api commute-helper/backend/app
git commit -m "test: cover full dashboard flow"
```

---

### Task 23: Add frontend end-to-end happy-path test with mocked backend

**Objective:** Prove the user can complete the MVP flow in the browser layer.

**Files:**
- Create: `commute-helper/frontend/src/test/MvpFlow.test.tsx`

**Step 1: Write failing test**

Create a single high-level test that:
1. opens the app,
2. creates a profile,
3. searches/selects a station,
4. loads the dashboard,
5. sees a recommendation message.

**Step 2: Run test to verify failure**

Run: `cd commute-helper/frontend && npm test -- --runInBand src/test/MvpFlow.test.tsx`
Expected: FAIL until wiring is complete.

**Step 3: Implement missing glue**

Only add the smallest state and callback wiring needed.

**Step 4: Verify pass**

Run: `cd commute-helper/frontend && npm test -- --runInBand src/test/MvpFlow.test.tsx`
Expected: PASS

**Step 5: Run full frontend suite**

Run: `cd commute-helper/frontend && npm test -- --runInBand`
Expected: PASS

**Step 6: Commit**

```bash
git add commute-helper/frontend/src/test commute-helper/frontend/src
git commit -m "test: cover frontend mvp flow"
```

---

### Task 24: Document local development, public-data setup, and verification steps

**Objective:** Make the MVP reproducible by documenting env vars, commands, and manual checks.

**Files:**
- Modify: `commute-helper/README.md`
- Create: `commute-helper/backend/.env.example`
- Create: `commute-helper/frontend/.env.example`

**Step 1: Write failing documentation check**

Add a simple backend test that asserts the README mentions `PUBLIC_DATA_SERVICE_KEY` and local startup commands.

```python
from pathlib import Path


def test_readme_mentions_public_data_key_and_start_commands():
    readme = Path('../README.md').read_text(encoding='utf-8')
    assert 'PUBLIC_DATA_SERVICE_KEY' in readme
    assert 'uvicorn app.main:app --reload' in readme
```

**Step 2: Run test to verify failure**

Run: `cd commute-helper/backend && pytest tests/test_docs.py::test_readme_mentions_public_data_key_and_start_commands -v`
Expected: FAIL — docs incomplete.

**Step 3: Write minimal documentation**

README should cover:
- project purpose
- backend setup
- frontend setup
- test commands
- env vars
- known MVP limitations
- manual verification checklist

**Step 4: Verify pass**

Run: `cd commute-helper/backend && pytest tests/test_docs.py -v`
Expected: PASS

**Step 5: Run final project test commands**

Run:
- `cd commute-helper/backend && pytest tests/ -q`
- `cd commute-helper/frontend && npm test -- --runInBand`
Expected: PASS

**Step 6: Commit**

```bash
git add commute-helper/README.md commute-helper/backend/.env.example commute-helper/frontend/.env.example commute-helper/backend/tests/test_docs.py
git commit -m "docs: add local setup and verification guide"
```

---

## Final Verification Checklist

Before calling the MVP complete:

- [ ] Backend smoke, model, schema, provider, service, and API tests pass
- [ ] Frontend component and happy-path tests pass
- [ ] Every provider parser was written test-first against fixtures
- [ ] Dashboard endpoint returns recommendation payload for a seeded profile
- [ ] Profile creation and stop selection work from the frontend
- [ ] README documents `PUBLIC_DATA_SERVICE_KEY` and startup/test commands
- [ ] Scope stayed inside MVP: no auth, no nationwide support, no advanced route engine

## Final Test Commands

```bash
cd commute-helper/backend && pytest tests/ -q
cd commute-helper/frontend && npm test -- --runInBand
```

## Recommended Next Step After MVP

After this plan is implemented and stable, the next iteration should add one of:
1. better stop/station index ingestion,
2. Redis-backed realtime cache,
3. scheduled leave-now notifications.
