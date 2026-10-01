# AGENTS.md — LUCKYBRIDGE/boardgame

## 저장소 역할

이 저장소는 동물고리즘 프로젝트의 세부 구현, 데이터, 인쇄 자산, 테스트 결과,
코드와 변경 이력을 관리한다.

ChatGPT 프로젝트는 최신 기준과 원본 근거를 유지하고,
GitHub는 개발 산출물과 이력을 보존하는 역할을 맡는다.

## 프로젝트 트랙

### Original KO
PLIX 원작 충실 한국어판.
현재 최우선 개발 대상.

### AI Detective
Original KO 검증 후 개발하는 개선판.
Feature, Query Efficiency, 구조화 데이터, 자동 판정, 난이도, 협력 모드 등을 검토한다.

두 트랙의 규칙과 데이터를 자동으로 섞지 않는다.

## 저장소 내 현재 기준

- `PROJECT_SOURCE.md` — 프로젝트 전체 방향의 저장소 미러
- `games/animalgorithm-original-ko/ORIGINAL_KO_CURRENT.md` — Original KO 최신 실행 기준
- `games/animalgorithm-original-ko/references/PLIX_SOURCE_NOTES.md` — PLIX 원본 근거 요약

ChatGPT 프로젝트의 최신 기준과 저장소 미러가 충돌하면 최신 ChatGPT 프로젝트 기준을 우선하고,
저장소의 미러 문서를 함께 갱신한다.

## 판단 우선순위

1. PLIX 원본 자료
2. `PROJECT_SOURCE.md`
3. `games/animalgorithm-original-ko/ORIGINAL_KO_CURRENT.md`
4. 저장소의 최신 관련 구현/데이터
5. Legacy 개선판 문서

## 표기

- `SOURCE`: PLIX에서 직접 확인
- `PROJECT DEFAULT`: 원작에 없어 프로젝트가 정한 운영 기본값
- `PROPOSAL`: 아직 확정되지 않은 제안
- `IMPROVED`: AI Detective 개선판 전용
- `OPTIONAL EXPERIMENT`: Original KO에서 선택적으로 시험하는 비원작 요소

## 개발 규칙

- 원작과 개선판을 명확히 분리한다.
- 현재 기준 문서는 고정 파일명을 사용하고 Git 이력으로 변경을 추적한다.
- 같은 역할의 `v0.2`, `v0.3`, `v0.4` 파일을 작업 폴더에 누적하지 않는다.
- 과거 버전은 Git 이력, 브랜치, 태그로 보존한다.
- 출력 PDF, CSV, JSON, 테스트 로그는 파생 산출물이며 SSOT보다 우선하지 않는다.
- 데이터·규칙·출력물이 충돌하면 먼저 기준 문서를 수정하고 파생 산출물을 다시 만든다.
- 큰 변경은 원본 근거와 변경 이유를 문서 또는 PR에 남긴다.
- AI Detective 작업 전 Original KO 플레이테스트 결과를 검토한다.
- 라이선스 확인 전 원본 이미지/카드 디자인의 외부 배포 가능성을 단정하지 않는다.

## 현재 우선순위

1. Original KO 규칙 안정화
2. 원본 46종 카드 한국어화
3. Category Idea 및 직접 작성 카드
4. LEFT / NEXT / RIGHT 플레이 영역
5. 인쇄 프로토타입
6. 플레이테스트
7. 원작의 장단점 기록
8. AI Detective 개선판 재설계
