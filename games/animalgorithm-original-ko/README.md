# Animal-gorithm Original KO

PLIX의 **Animal-gorithm**을 먼저 원형에 가깝게 한국어로 구현하기 위한 트랙입니다.

## 현재 원본에서 확인된 핵심

- 안내 연령: 12–100
- 인원: 3–6명
- 한 명의 Decider가 LEFT / RIGHT 양쪽의 비밀 카테고리를 정함
- Decider가 동물 카드를 양쪽에 배치함
- 다른 플레이어는 다음 카드가 어느 쪽으로 갈지 예측함
- 플레이어는 비밀 카테고리를 추측하거나 새 카드를 추가할 수 있음
- 누군가 비밀 카테고리를 맞힐 때까지 반복
- 다음 판에는 다른 사람이 Decider 역할을 맡음

## 원본 카드 자료

`plix-deck-animal-database.pdf` 기준:

- 이름이 있는 동물 카드: **46장**
- 빈 동물 카드: **10장**
- Category Idea 카드: **8장**
  - 포유류 / 포유류가 아님
  - 색이 화려함 / 화려하지 않음
  - 비늘이 있음 / 비늘이 없음
  - 날 수 있음 / 날 수 없음
  - 다리가 2개 / 그 외
  - 알을 낳음 / 알을 낳지 않음
  - 곤충을 먹음 / 곤충을 먹지 않음
  - 사용자 정의 / 그 반대

## 이미지 방향

원작 충실 한국어판의 프로토타입은 **PLIX 원본 동물 이미지를 그대로 사용**하고 한국어 이름과 안내만 덧붙이는 방향으로 진행합니다.

외부 배포/판매 단계에서는 원본 자산의 적용 라이선스를 다시 확인합니다.

## v0.3 프로토타입 보완

- 원본 Category Idea의 LEFT / RIGHT 구조를 그대로 보이게 재설계
- 직접 작성 카드 8장 추가
  - X / X가 아님 4장
  - LEFT / RIGHT 자유 작성형 4장
- 손글씨가 충분히 들어가도록 큰 빈칸 확보
- NEXT 영역을 포함한 분류판 추가
- 결정자가 숨겨야 할 정보와 비밀 유지 절차 명시
- 직접 질문 금지, 오답 부분 힌트 금지 등 실제 진행 주의사항 추가

## 중요한 구현 원칙

이 트랙에서는 동물 카드에 Feature 아이콘을 새로 붙이지 않습니다.
원본은 동물 카드와 카테고리 비교 자체가 게임의 핵심이므로, 개선형 데이터 모델을 원본형에 강제로 적용하지 않습니다.

원본이 명시하지 않은 세부 운영 방식은 `docs/SOURCE_GAP_DECISIONS.md`에 별도로 기록합니다.

## 파일

- `docs/ORIGINAL_RULES_KO.md` — 상세 한국어 플레이 규칙
- `docs/SOURCE_GAP_DECISIONS.md` — 원본에 없는 세부사항과 프로젝트 기본값
- `docs/PAPER_PROTOTYPE_SPEC.md` — 종이 프로토타입 구성
- `docs/PLAYTEST_CHECKLIST_ORIGINAL_KO.md` — 원작판 플레이테스트
- `references/PLIX_SOURCE_NOTES.md` — 페이지별 출처 정리
- `data/animals.plix-ko.json` — 46종 동물명 한국어 매핑
- `data/category_pairs.plix-ko.json` — 원본 Category Idea 8종
