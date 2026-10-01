# Animal-gorithm Original KO

PLIX의 **Animal-gorithm**을 원작의 핵심 플레이 구조를 유지하면서 한국어로 구현하는 트랙입니다.

## 현재 기준

최신 실행 규칙은:

`ORIGINAL_KO_CURRENT.md`

를 우선합니다.

원본에서 확인된 핵심:

- 안내 연령: 12–100
- 인원: 3–6명
- Decider가 LEFT / RIGHT 비밀 카테고리를 정함
- 동물 카드를 LEFT / RIGHT로 분류
- 다른 플레이어는 다음 카드가 어느 쪽인지 예측
- 비밀 카테고리를 추측하거나 새 카드를 추가
- 정답까지 반복
- 다음 판에는 다른 사람이 Decider

## 원본 카드 자료

- 이름 있는 동물 카드 46장
- 빈 동물 카드 10장
- Category Idea 카드 8장

## 현재 제작 방향

- 동물 이미지: PLIX 원본 활용
- 동물 이름: 한국어 대형 + 영문 원명 소형 병기 (`PROJECT DEFAULT`)
- Category Idea: 한국어판 자체 제작
- 직접 작성 Category 카드: 큰 빈칸 제공
- 플레이 영역: LEFT / NEXT / RIGHT
- 상세 규칙 및 비밀정보 관리 주의사항 제공

## 인쇄 프로토타입 생성

`docs/PAPER_PROTOTYPE_SPEC.md`가 현재 인쇄 기준이다.

PLIX 동물 카드 PDF를 로컬에 준비한 뒤:

```bash
pip install reportlab pymupdf pillow
python scripts/build-print-prototype.py \
  --deck-pdf /path/to/plix-deck-animal-database.pdf \
  --out ./output/Animalgorithm_Original_KO_Print_Prototype.pdf
```

생성물에는 46종 동물 카드, 빈 카드 10장, Category Idea, 직접 작성 카드, LEFT/NEXT/RIGHT 영역, 상세 규칙, 플레이테스트 기록지가 포함된다.

PLIX 원본 이미지가 포함된 생성 PDF는 원본 자산 라이선스 범위를 최종 확인하기 전까지 저장소에 상시 커밋하지 않는다.

## 폴더 역할

- `data/` — 동물명, Category 데이터와 스키마
- `docs/` — 프로토타입 명세, Source Gap, 플레이테스트
- `references/` — PLIX 출처 및 라이선스 메모
- `scripts/` — 데이터 무결성 검사 및 인쇄 프로토타입 생성

과거 버전은 별도 `v0.x` 파일로 누적하지 않고 Git 이력으로 확인합니다.
