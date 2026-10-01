# 동물고리즘 – AI 탐정

이 폴더는 PLIX 원형을 바탕으로 **초등 AI 수업용으로 수정·개선하는 별도 Track B**입니다.

현재 최우선은 `../animalgorithm-original-ko/`의 Original KO 구현과 플레이테스트입니다.

## 현재 상태

AI Detective는 아직 현재 규칙을 확정하지 않습니다.
기존 v1.0 설계는 `legacy-v1.0/`에 보존합니다.

v1.0에서 검토했던 요소:

- 명시적 Feature 데이터
- True / False 분류
- Query Efficiency
- 규칙 자동 판정
- 난이도
- 협력/경쟁 모드
- 플레이테스트 지표

이 자료에는 현재 PLIX 원본 해석과 다른 부분이 있으므로 **Legacy 참고 자료**로만 사용합니다.

Original KO 검증이 끝난 뒤 다음을 다시 판단합니다.

1. LEFT / RIGHT 구조를 유지할지
2. 내부 Feature Rule을 어떻게 연결할지
3. Query 제한/점수/난이도를 도입할지
4. 초등 4~6학년 수업용 데이터 구조를 어떻게 확정할지

## 중요

- 이 트랙의 기능을 Original KO에 자동으로 적용하지 않습니다.
- 최신 프로젝트 방향은 저장소 루트 `PROJECT_SOURCE.md`를 우선합니다.
- 과거 v1.0 파일은 `legacy-v1.0/`에서 보존하며 현재 SSOT로 취급하지 않습니다.
