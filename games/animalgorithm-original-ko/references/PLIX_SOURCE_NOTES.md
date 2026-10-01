# PLIX Source Notes

## 1. Game guide

Source: `plix_llm-algorithm_arcade_game_guides_v1.pdf`

Animal-gorithm은 PDF의 2페이지에 있다.

확인된 원본 구조:

1. Decider chooses secret categories for left and right sides.
2. Decider places cards on the left and right sides.
3. Players guess which side the next card goes.
4. Players guess the secret categories or add cards.
5. Repeat until a player correctly guesses the secret categories.
6. Play again with a different Decider.

Learn 영역은 플레이어가 LEFT의 공통점, RIGHT의 공통점, 두 쪽의 차이를 찾고 새 동물이 추가될 때마다 더 많은 정보를 얻는다고 설명한다.

원본 표시 연령은 12–100, 인원은 3–6명이다.

## 2. Animal card database

Source: `plix-deck-animal-database.pdf`

- pages 1–5: 각 8장, 총 40종
- page 6: 이름 있는 동물 6장 + 빈 카드 2장
- page 7: 빈 카드 8장
- page 8: Category Idea 8장

합계:
- named animals: 46
- blank animal cards: 10
- category idea cards: 8

## 3. Category Idea cards

Page 8의 쌍:

- Mammal / Not mammal
- Colorful / Not colorful
- Scaly / Not scaly
- Can fly / Cannot fly
- Has 2 legs / Other
- Lays eggs / Does not lay eggs
- Eats bugs / Does not eat bugs
- ________ / Not ________

## 4. Fidelity boundary

이 폴더의 문서는 원본 구조 분석과 한국어 구현을 위한 출처 기록이다.
개선판의 Feature schema, True/False 표현, Query token 등의 설계는 이 원형 트랙의 출처 사실로 취급하지 않는다.
