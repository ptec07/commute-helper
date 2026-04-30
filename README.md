# 출근도우미

서울 직장인을 위한 통근 출발 판단 MVP 프로젝트입니다. 저장한 통근 프로필을 기준으로 정류장/역을 선택하고, 실시간 버스·지하철 데이터를 이용해 출발 추천을 보여줍니다.

## 프로젝트 구조

- `backend/`: FastAPI 백엔드
- `frontend/`: React + Vite 프론트엔드
- `docs/`: 설계 문서와 구현 계획

## 배포 URL

- Frontend: https://commute-helper.vercel.app
- Backend: https://commute-helper-backend.onrender.com
- Health: https://commute-helper-backend.onrender.com/health

## 현재 구현 범위

- 통근 프로필 생성
- 정류장/역 검색 및 선택
- 대시보드 추천 메시지 표시
- 서울 버스/지하철 fixture 기반 provider 파서
- 서울 공공데이터 live provider 연동
- public-data primary → ODsay backup → fixture fallback 순서의 live 대시보드
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
ODSAY_API_KEY=your_odsay_api_key
PUBLIC_DATA_SERVICE_KEY=your_data_go_kr_service_key
SEOUL_OPEN_API_KEY=your_s..._key
USE_LIVE_PUBLIC_DATA=false
ALLOW_INSECURE_SEOUL_TRANSIT_HTTP=false
FRONTEND_ORIGIN=http://localhost:5173,http://127.0.0.1:5173
DATABASE_URL=sqlite:///./commute_helper.db
```

- `USE_LIVE_PUBLIC_DATA=true`이면 선택한 버스 정류장/지하철역 기준으로 live provider를 호출합니다.
- live provider 우선순위는 `public-data primary` → `ODsay backup` → fixture fallback입니다.
- 서울버스 공공데이터는 일부 환경에서 HTTPS가 타임아웃될 수 있어, 로컬 진단/개발에서는 `ALLOW_INSECURE_SEOUL_TRANSIT_HTTP=true`로 HTTP fallback을 명시적으로 허용할 수 있습니다.
- 서울버스 XML의 `headerCd=4` / `결과가 없습니다.`는 실패가 아니라 빈 결과로 처리합니다.
- `ODSAY_API_KEY`가 설정되어 있으면 공공데이터 live 호출 실패 시 backup provider로 사용합니다.
- `FRONTEND_ORIGIN`은 배포 후 Vercel 도메인을 쉼표로 추가해 브라우저 CORS를 허용합니다.

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

- 검색 인덱스는 `backend/tests/fixtures/station_index.json`의 소규모 샘플 데이터다.
- 기본 DB는 로컬 SQLite 파일(`backend/commute_helper.db`)이라 마이그레이션/운영 DB 분리는 아직 미구현이다.
- 운영 배포에서 데이터를 유지하려면 Render PostgreSQL 같은 영구 DB의 URL을 `DATABASE_URL`에 설정한다. 유료 리소스 생성이 필요할 수 있으므로 현재 배포는 SQLite 기반 MVP 데모로 둔다.

## 참고 문서

- 구현 계획: `docs/implementation-plan.md`
