# 출근도우미

서울 직장인을 위한 통근 출발 판단 MVP 프로젝트입니다. 저장한 통근 프로필을 기준으로 정류장/역을 선택하고, 실시간 버스·지하철 데이터를 이용해 출발 추천을 보여줍니다.

## 프로젝트 구조

- `backend/`: FastAPI 백엔드
- `frontend/`: React + Vite 프론트엔드
- `docs/`: 설계 문서와 구현 계획

## 현재 구현 범위

- 통근 프로필 생성
- 정류장/역 검색 및 선택
- 대시보드 추천 메시지 표시
- 서울 버스/지하철 fixture 기반 provider 파서
- 백엔드/프론트 테스트 스위트

## 백엔드 실행

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install -e .[dev]
cp .env.example .env
uvicorn app.main:app --reload
```

기본 환경변수:

```bash
PUBLIC_DATA_SERVICE_KEY=your_data_go_kr_service_key
DATABASE_URL=sqlite:///./commute_helper.db
```

## 프론트엔드 실행

```bash
cd frontend
npm install
cp .env.example .env
npm run dev
```

기본 환경변수:

```bash
VITE_API_BASE_URL=http://localhost:8000
```

## 테스트 명령

백엔드:

```bash
cd backend
source .venv/bin/activate
pytest tests/ -q
```

프론트엔드:

```bash
cd frontend
npm test -- --run
npm run build
```

## 수동 확인 체크리스트

1. 홈에서 `통근 프로필 만들기` 버튼이 보인다.
2. 프로필 이름을 저장하면 정류장/역 선택 화면으로 이동한다.
3. `상계역` 검색 결과를 선택할 수 있다.
4. `선택 완료`를 누르면 대시보드로 이동한다.
5. 추천 메시지와 버스/지하철 카드가 렌더링된다.

## 현재 한계

- 실제 공공 API 호출 대신 fixture 기반 provider parsing을 우선 연결했다.
- 검색 인덱스는 `backend/tests/fixtures/station_index.json`의 소규모 샘플 데이터다.
- 기본 DB는 로컬 SQLite 파일(`backend/commute_helper.db`)이라 마이그레이션/운영 DB 분리는 아직 미구현이다.

## 참고 문서

- 구현 계획: `docs/implementation-plan.md`
