# HTML 리포트 생성

`templates/report.md`(마크다운)를 다 채운 뒤, 같은 내용을 **한 장짜리 정적
HTML 파일**로도 만들어 `templates/report.html`에 저장한다. 외부 CDN·JS 라이브러리
없이 순수 HTML+인라인 CSS(+정적 SVG)만 쓴다 — 인터넷 연결 없이 로컬에서 열어도
그대로 보여야 한다. 이건 "대시보드"(실시간·다회차 모니터링)가 아니라 **한 번
찍은 스냅샷을 보기 좋게 렌더링하는 것**일 뿐이라 무료 범위 안에 든다.

## 구조 (report.md 섹션과 1:1 대응)

1. 헤더: 브랜드명 + "ChatGPT GEO 스냅샷" / "멀티모델 GEO 스냅샷" + 측정일자
2. 한계 배너 (눈에 띄는 색으로, 맨 위)
3. **기술 점수 게이지** (아래 SVG)
4. 핵심 지표 카드/표 (언급률·추천률·인용률·SoV)
5. 자사·경쟁사 비교표
6. 자사가 빠진 질문 / 경쟁사가 강한 질문
7. 자주 인용된 도메인
8. 테크니컬 문제 ↔ AI 답변 연결
9. 우선 개선 과제
10. 재측정 방법
11. 부록: 질문 5개

## 기술 점수 게이지 (SVG, 그대로 쓰고 각도만 계산해서 채운다)

점수(0~100)를 바늘 회전각으로 바꾸는 공식: **회전각(deg) = -90 + 점수 × 1.8**
(0점=-90°=왼쪽 수평, 50점=0°=정수직, 100점=90°=오른쪽 수평). 계산한 숫자를
`transform="rotate(...)"`에 그대로 넣는다.

```html
<div class="gauge">
  <svg viewBox="0 0 200 120" width="220" height="132">
    <!-- 시급 0-49 -->
    <path d="M 20 100 A 80 80 0 0 1 43.43 43.43" fill="none" stroke="#e74c3c" stroke-width="18"/>
    <!-- 보완필요 50-69 -->
    <path d="M 43.43 43.43 A 80 80 0 0 1 100 20" fill="none" stroke="#f39c12" stroke-width="18"/>
    <!-- 양호 70-89 -->
    <path d="M 100 20 A 80 80 0 0 1 156.57 43.43" fill="none" stroke="#f1c40f" stroke-width="18"/>
    <!-- 우수 90-100 -->
    <path d="M 156.57 43.43 A 80 80 0 0 1 180 100" fill="none" stroke="#2ecc71" stroke-width="18"/>
    <!-- 바늘: rotate()의 첫 숫자만 "-90 + 점수*1.8" 계산값으로 교체 -->
    <line x1="100" y1="100" x2="100" y2="30" stroke="#222" stroke-width="4"
          transform="rotate(0 100 100)"/>
    <circle cx="100" cy="100" r="8" fill="#222"/>
  </svg>
  <div class="gauge-score">68<span class="gauge-max">/100</span></div>
  <div class="gauge-grade">보완 필요</div>
</div>
```

예시(68점): 회전각 = -90 + 68×1.8 = 32.4 → `transform="rotate(32.4 100 100)"`.

바늘 색 구간과 등급 표는 항상 같이 붙인다 — 게이지만 덩그러니 있으면 숫자가
뭘 의미하는지 안 와닿는다. 게이지 아래에 "68점(보완 필요) — robots.txt만
걸림" 한 줄을 반드시 붙인다(tech-audit.md 보고 형식과 동일).

**게이지 아래 항목 표는 "구분"(필수/권장/참고) 없이 단일 표로 늘어놓지 않는다.**
"필수 항목 전부 통과" 같은 요약 문구는 권장·참고 항목이 실패해도 나올 수 있는데,
표에 구분이 안 보이면 사용자가 "분명 빨간 게 있는데 왜 통과라는 거지?"라고
헷갈린다(실제로 이 실수가 났었다). 표를 하나로 합치지 말고 **필수/권장/참고
소제목으로 나눠서 각각 따로 렌더링**한다:

```html
<h3 class="tier">필수</h3>
<table>...HTTP 200, noindex 없음 등 4개...</table>

<h3 class="tier">권장</h3>
<table>...sitemap, AI 크롤러별 정책 등...</table>

<h3 class="tier">참고 (점수 미포함)</h3>
<table>...llms.txt...</table>
```

`.tier` 클래스는 아래 전체 페이지 골격의 CSS에 이미 포함돼 있다. 이렇게 나누면
"필수는 다 초록인데 권장 칸에 빨간 게 있구나"가 표만 봐도 바로 보인다 — 요약
문구를 다시 안 읽어도 된다.

## 전체 페이지 골격 (인라인 CSS)

```html
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<title>{브랜드명} GEO 스냅샷 — {측정일자}</title>
<style>
  :root{--bg:#0b0f14;--card:#141a22;--line:#232b36;--text:#e8edf3;--muted:#8a96a6;
        --accent:#4f8cff;--good:#2ecc71;--warn:#f1c40f;--bad:#e74c3c}
  *{box-sizing:border-box}
  body{margin:0;padding:32px;background:var(--bg);color:var(--text);
       font-family:-apple-system,"Pretendard","Malgun Gothic",sans-serif;line-height:1.6}
  .wrap{max-width:860px;margin:0 auto}
  h1{font-size:1.6rem;margin-bottom:4px} .sub{color:var(--muted);margin-bottom:24px}
  .banner{background:#2a1f10;border:1px solid #5a3d10;color:#f1c40f;
          padding:12px 16px;border-radius:8px;margin-bottom:24px;font-size:.92rem}
  .card{background:var(--card);border:1px solid var(--line);border-radius:12px;
        padding:20px;margin-bottom:20px}
  .gauge{display:flex;flex-direction:column;align-items:center;text-align:center}
  .gauge-score{font-size:2rem;font-weight:700;margin-top:-8px}
  .gauge-max{font-size:1rem;color:var(--muted);font-weight:400}
  .gauge-grade{color:var(--muted)}
  table{width:100%;border-collapse:collapse;font-size:.92rem}
  th,td{text-align:left;padding:8px 10px;border-bottom:1px solid var(--line)}
  th{color:var(--muted);font-weight:600}
  .badge{display:inline-block;padding:2px 8px;border-radius:999px;font-size:.8rem}
  .b-good{background:#123a24;color:var(--good)} .b-warn{background:#3a2f0f;color:var(--warn)}
  .b-bad{background:#3a1414;color:var(--bad)}
  h2{font-size:1.05rem;margin:0 0 12px;color:var(--accent)}
  .tier{font-size:.85rem;color:var(--muted);text-transform:uppercase;
        letter-spacing:.05em;margin:16px 0 6px}
  .tier:first-child{margin-top:0}
  ul{margin:0;padding-left:20px}
</style>
</head>
<body>
<div class="wrap">
  <h1>{브랜드명} GEO 스냅샷</h1>
  <div class="sub">측정일자: {날짜} · 질문 5개 · 단일 시점</div>
  <div class="banner">⚠ 질문 5개, 단일 시점, 반복 측정 없음의 스냅샷입니다. 추세가 아니라 현재 한 장의 사진으로 읽어주세요.</div>

  <div class="card"><h2>사이트 기술 점수</h2>(게이지 삽입)</div>
  <div class="card"><h2>핵심 지표</h2>(표 삽입)</div>
  <div class="card"><h2>자사·경쟁사 비교</h2>(표 삽입)</div>
  <!-- 이하 report.md 나머지 섹션도 각각 .card 하나씩 -->
</div>
</body>
</html>
```

배지(`badge`) 클래스는 ✅→`b-good`, ⚠️→`b-warn`, ❌→`b-bad`로 매핑해서 표 안
상태 칸에 쓴다. 색상표는 라이트/다크 상관없이 이 다크 테마 하나로 고정한다 —
사용자 브라우저 설정에 맞출 필요 없는 정적 파일이라 단순하게 간다.

## 저장·안내

`templates/report.html`로 저장하고, 8단계 마지막에 "브라우저로 열어서
`templates/report.html`을 보시면 시각적으로 정리된 버전을 보실 수 있어요"라고
안내한다. 마크다운 리포트(`templates/report.md`)를 대체하는 게 아니라 같이
남긴다 — 마크다운은 재검증·diff용, HTML은 보여주기용으로 역할이 다르다.
