# Design System — Commute Helper

## Product Context
- **What this is:** 서울 출근길의 버스/지하철 도착 정보를 보고 빠르게 출발 판단을 돕는 웹앱.
- **Who it's for:** 매일 아침 같은 출근길을 반복 확인하는 서울 직장인.
- **Project type:** 모바일 우선 웹앱.

## Aesthetic Direction
- **Direction:** Clean White Transit UI.
- **Mood:** 흰 배경, 짧은 문구, 산뜻한 파란색/초록색 포인트. 복잡한 지도앱보다 빠른 판단 카드에 집중한다.
- **Non-goals:** 긴 마케팅 문구, 과한 그래픽, 진한 배경, 보라색 그라데이션 CTA.

## Typography
- **Primary UI:** Pretendard, fallback to system sans-serif.
- **Numbers:** `font-variant-numeric: tabular-nums` for arrival minutes and times.
- **Tone:** 제목은 굵고 짧게, 설명은 1문장 이하로 유지한다.

## Color
- **Background:** `#ffffff`
- **Soft surface:** `#f8fafc`
- **Primary text:** `#172033`
- **Secondary text:** `#667085`
- **Muted text:** `#98a2b3`
- **Primary blue:** `#2563eb`, CTA and subway/recommendation emphasis.
- **Primary soft:** `#eff6ff`
- **Transit green:** `#16a34a`, bus/normal status.
- **Green soft:** `#ecfdf3`
- **Morning amber:** `#f59e0b`, short caution accents only.
- **Amber soft:** `#fffbeb`
- **Border:** `#e4e7ec`

## Layout
- **Approach:** Mobile-first centered app shell.
- **Max width:** `480px`.
- **Screen padding:** `20px` desktop/tablet, `16px` small mobile.
- **Cards:** white surface, subtle border, soft shadow, `20-22px` radius.
- **Spacing:** screen sections `22px`, card internals `16px`, compact UI groups `8-12px`.

## Components
- **AppShell:** shared white app frame, brand header, centered content.
- **Button:** blue primary button, full-width, 52px min height, 16px radius.
- **Card:** consistent section container.
- **Badge/Chip:** small status labels with soft blue/green/amber backgrounds.
- **MetricCard:** compact arrival summary, large tabular number.
- **EmptyState:** short message, never long explanations.

## Copy Rules
- Prefer one-line explanations.
- The first screen must answer: “무엇을 해주나?” and “무엇을 누르면 되나?”
- Dashboard order: profile, recommendation, arrival summary, details.

## Decisions Log
| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-04-30 | Use Clean White Transit UI | User requested white background, clean fresh colors, short copy, readable and unified layout. |
