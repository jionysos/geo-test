# geo-test

**브랜드가 ChatGPT 답변에 얼마나 나오고, 경쟁 브랜드와 비교해 얼마나 추천되는지
확인하는 무료 GEO 진단 스킬입니다.** Claude Code와 Codex에서 같은 `SKILL.md`를
사용합니다.

## 무엇을 확인하나요?

- 공개 핵심 페이지 3~5개를 표본으로 HTTP 응답, robots.txt, noindex, sitemap,
  내부 링크, 메타 정보, canonical, 구조화 데이터, HTML 본문 노출을 점검합니다.
- 사이트 접근 차단과 기술 완성도를 분리해 보여줍니다. 기술 점수는 실제 ChatGPT
  추천을 보장하는 점수가 아닙니다.
- 브랜드명이 없는 질문 5개를 만듭니다.
- 사용자가 ChatGPT에서 가져온 실제 답변으로 자사와 경쟁사의 언급·추천을 판정합니다.
- 회사·브랜드·제품은 확인된 소유관계 안에서 하나의 자사 생태계로 합쳐 봅니다.
- 사용자가 지정한 경쟁사와 답변에서 자동 발견한 경쟁사를 모두 비교합니다.
- 언급률, 추천률, 추천 SoV, 평균 추천순위를 계산하고 정적 HTML 리포트를 만듭니다.

## 왜 수동 측정인가요?

외부 AI API와 API 키를 요구하지 않기 위해서입니다. 질문 5개를 각각 새 ChatGPT
대화에서 실행한 뒤 질문과 답변 전체를 스킬 대화창에 붙여넣으면, 판정·집계·리포트는
스킬이 처리합니다. 파일을 직접 채우거나 출처 URL을 따로 찾을 필요는 없습니다.

## 설치

HTTPS 방식이라 GitHub SSH 키가 없어도 됩니다.

### Claude Code · 개인 스킬

```bash
mkdir -p ~/.claude/skills
git clone https://github.com/jionysos/geo-test.git ~/.claude/skills/geo-test
```

Claude Code에서 `/geo-test` 또는 자연어로 요청합니다.

### Codex · 개인 스킬

```bash
mkdir -p ~/.codex/skills
git clone https://github.com/jionysos/geo-test.git ~/.codex/skills/geo-test
```

Codex에서 `$geo-test` 또는 자연어로 요청합니다.

이미 설치한 경우에는 설치 폴더에서 `git pull`로 업데이트합니다.

## 사용 흐름

1. 확인할 회사·브랜드·제품 이름과 설명, 공식 홈페이지를 편하게 말합니다.
2. 경쟁사를 알면 이름만 알려줍니다. 몰라도 답변에서 발견된 경쟁사를 자동으로
   비교하므로 진행할 수 있습니다.
3. 사이트 기술 진단 결과와 개선 우선순위를 확인합니다. 로컬 코드는 승인 없이
   수정하지 않습니다.
4. 스킬이 채팅에 보여준 질문 5개를 각각 새 ChatGPT 대화에서 실행합니다.
5. 질문과 답변 전체를 스킬 대화창에 붙여넣습니다.
6. 스킬이 자사·지정 경쟁사·자동 발견 경쟁사를 같은 기준으로 판정하고 리포트를
   생성합니다.

## 계산 기준

- 언급률: Q1~Q5에서 자사가 언급된 답변 수 / 5
- 추천률: Q2~Q5에서 자사가 추천된 답변 수 / 4
- 추천 SoV: Q2~Q5 자사 추천 수 / 자사와 모든 비교 경쟁사의 전체 추천 수
- 평균 추천순위: 명시적 순위나 명확히 정렬된 추천 목록·표에서 확인된 자사 순위 평균

일반 설명문의 등장 순서는 추천순위로 추정하지 않습니다. 출처 칩에만 나온 이름도
브랜드 언급으로 세지 않습니다. 자세한 기준은 [scoring.md](./references/scoring.md)에
있습니다.

## 결과 파일

실행마다 현재 작업 폴더 아래에 별도 폴더를 만듭니다.

```text
geo-test-results/{brand}-{YYYYMMDD-HHMMSS}/
  brand-profile.md
  report-data.json
  report.md
  report.html
```

사용자가 바로 찾을 수 있도록 최종 HTML을 다운로드 폴더에도 복사합니다. 환경 권한상
다운로드 폴더를 쓸 수 없으면 실행 폴더의 정확한 경로를 안내합니다. 리포트 디자인만
바꿀 때는 기존 `report-data.json`으로 다시 렌더링하므로 처음부터 측정하지 않습니다.

## 의도적으로 포함하지 않은 기능

외부 AI API, 다른 AI 모델 측정, 자동 반복 실행, 스케줄러, 다중 실행 변동성 보정,
대시보드, 대량 질문 관리, 업종 벤치마크, 자동 CMS 배포, 텔레메트리, 사용자 데이터
수집, 영업 CTA는 포함하지 않습니다.

## 저장소 구조

```text
SKILL.md
references/
  tech-audit.md
  question-generation.md
  manual-measurement.md
  scoring.md
  report-data.md
  report-template.md
  html-report.md
scripts/
  build_report.py
tests/
  test_build_report.py
templates/
  brand_profile.md
  report.md
  report.html
```

## 라이선스

MIT
