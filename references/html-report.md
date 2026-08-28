# HTML 리포트 생성

`templates/report.md`(마크다운)를 다 채운 뒤, 같은 내용을 **한 장짜리 정적
HTML 파일**로도 만들어 `templates/report.html`에 저장한다. 외부 CDN·JS 라이브러리
없이 순수 HTML+인라인 CSS(+정적 SVG)만 쓴다 — 인터넷 연결 없이 로컬에서 열어도
그대로 보여야 한다. 이건 "대시보드"(실시간·다회차 모니터링)가 아니라 **한 번
찍은 스냅샷을 보기 좋게 렌더링하는 것**일 뿐이라 무료 범위 안에 든다.

## 레이아웃 — 세로로 줄줄 쌓지 않는다, 좌우 2단으로 나눈다

기술 진단(사이트가 크롤러에게 어떻게 보이는가)과 GEO 실측(AI 답변에서 실제로
어떻게 나오는가)은 서로 다른 질문에 대한 답이다. 하나의 세로 스크롤에 순서대로
쌓지 말고, **왼쪽에 테크니컬, 오른쪽에 GEO 가시성(질문·응답 결과)** 을 나란히
놓는다. 헤더/한계배너와, 양쪽을 종합하는 섹션(테크니컬 문제↔AI 답변 연결·우선
개선과제·재측정방법·부록)만 전체 폭으로 위/아래에 둔다:

```
┌─────────────────────────────────────────────┐
│ 헤더 + 한계 배너 (전체 폭)                     │
├───────────────────────┬───────────────────────┤
│ 왼쪽: 테크니컬          │ 오른쪽: GEO 가시성      │
│ - 사이트 기술 점수      │ - 핵심 지표 (+ 산식)     │
│   (게이지+필수/권장/참고)│ - 질문별 결과(O/X+응답) │
│                        │ - 발견된 브랜드(파이차트) │
│                        │ - 자주 인용된 도메인      │
├───────────────────────┴───────────────────────┤
│ 사이트 문제 ↔ 실제 AI 답변 연결 (전체 폭, 종합)  │
│ 우선 개선 과제 / 재측정 방법 / 부록 (전체 폭)     │
└─────────────────────────────────────────────┘
```

CSS: `.split{display:grid;grid-template-columns:1fr 1fr;gap:20px}`,
`@media(max-width:760px){.split{grid-template-columns:1fr}}`로 좁은 화면에선
세로로 자연스럽게 접히게 한다.

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

**`.gauge-grade`엔 등급만 적는다 — "필수 항목 전부 통과" 같은 부연은 붙이지
않는다.** 아래 필수/권장/참고 표가 색으로 이미 다 보여주는 내용을 문장으로
반복할 필요가 없다. 등급 하나로 충분하다: "양호", "보완 필요" 같은 단어만.

## 필수/권장/참고 — 표 3개로 나누고, 색으로도 확실히 구분한다

소제목만으로는 구분이 약하다. **테두리 색 + 칩 배지**까지 같이 써서 필수와
권장이 눈에 확 띄게 다르게 보이도록 한다 — 필수는 강조색(파랑), 권장은 중립,
참고는 더 흐리게:

```html
<div class="tier-block required">
  <span class="tier-chip required">필수</span>
  <table>...HTTP 200, noindex 없음 등 4개...</table>
</div>

<div class="tier-block recommended">
  <span class="tier-chip recommended">권장</span>
  <table>...sitemap, AI 크롤러별 정책 등...</table>
</div>

<div class="tier-block optional">
  <span class="tier-chip optional">참고 · 점수 미포함</span>
  <table>...llms.txt...</table>
</div>
```

CSS (아래 전체 골격에 포함돼 있음):

```css
.tier-block{border-left:3px solid var(--line);padding-left:14px;margin-bottom:18px}
.tier-block:last-child{margin-bottom:0}
.tier-block.required{border-left-color:var(--accent)}
.tier-block.recommended{border-left-color:#5a6577}
.tier-block.optional{border-left-color:#333d4a;opacity:.85}
.tier-chip{display:inline-block;font-size:.72rem;font-weight:700;text-transform:uppercase;
  letter-spacing:.05em;padding:3px 9px;border-radius:5px;margin-bottom:10px}
.tier-chip.required{background:#16264a;color:var(--accent)}
.tier-chip.recommended{background:#232b36;color:#aab4c2}
.tier-chip.optional{background:#1a1f26;color:#6b7684}
```

이렇게 하면 소제목 텍스트만 있을 때보다 "여기서부터 필수, 여기서부터 권장"이
스캔하듯 봐도 바로 들어온다.

## 핵심 지표 아래 산식

표 바로 아래에 `.note`(작고 흐린 텍스트)로 한 줄 붙인다:

```html
<p class="note">언급률 = 언급된 답변 수 / 전체 질문 수 · 추천률 = 추천된 답변 수
/ 추천이 성립할 수 있는 질문 수 · 인용률 = 도메인이 출처로 표시된 답변 수 /
출처 URL이 있는 답변 수</p>
```

## 질문별 결과 — O/X 표 + 등장 브랜드 배지 + AI 응답 원문(접기)

"자사가 빠진 질문"처럼 따로 뽑아 요약하지 않는다 — 이 표 하나로 다 보인다.
O/X는 색으로도 구분한다(`.ox-good`=초록 O, `.ox-bad`=회색 X, 회색인 이유는
"실패"가 아니라 "여기선 없었다"는 중립적 사실이라서 빨간색을 안 쓴다):

```html
<table><thead><tr><th>ID</th><th>질문</th><th>언급</th><th>추천</th><th>인용</th><th>등장 브랜드</th></tr></thead>
<tbody>
<tr>
  <td>Q1</td><td>강아지 종합영양제 선택 기준</td>
  <td class="ox-bad">X</td><td class="ox-bad">X</td><td class="ox-bad">X</td>
  <td>—</td>
</tr>
<tr>
  <td>Q2</td><td>국내 종합영양제 추천</td>
  <td class="ox-bad">X</td><td class="ox-bad">X</td><td class="ox-bad">X</td>
  <td><span class="tag">한아름펫</span><span class="tag">라이프펫</span></td>
</tr>
</tbody></table>

<details><summary>Q1 응답 전문 보기</summary>
<p>(붙여넣은 원문 그대로 — 요약하지 말고 판정에 쓴 만큼 남긴다)</p>
</details>
<details><summary>Q2 응답 전문 보기</summary>
<p>...</p>
</details>
```

각 질문 표 아래에 `<details>`를 질문 개수만큼 나열한다(질문당 하나). CSS는
아래 전체 골격에 `.ox-good`/`.ox-bad`/`.tag`/`details`로 이미 포함돼 있다.
`<details>`는 JS 없이 브라우저 기본 기능으로 접고 펼쳐진다 — 이 스킬의
"외부 JS 없음" 원칙에 안 걸린다.

## 답변에 등장한 브랜드 — 도넛 파이차트

표만 나열하지 않고 `conic-gradient`로 그린 순수 CSS 도넛 차트를 옆에 붙인다.
JS도 이미지도 필요 없다. 브랜드별 등장 횟수를 전체 합으로 나눠 누적 퍼센트
구간을 계산해서 `conic-gradient`에 넣는다:

```
브랜드 A 40%, B 30%, C 30% → conic-gradient(
  colorA 0% 40%, colorB 40% 70%, colorC 70% 100%)
```

```html
<div class="pie-wrap">
  <div class="pie" style="background:conic-gradient(
    #6ea0ff 0% 33.3%, #f39c12 33.3% 50%, #9b59b6 50% 66.7%,
    #1abc9c 66.7% 83.3%, #e91e8c 83.3% 100%)">
    <div class="pie-hole"></div>
  </div>
  <ul class="legend">
    <li><span class="dot" style="background:#6ea0ff"></span>라이프펫 — 2</li>
    <li><span class="dot" style="background:#f39c12"></span>한아름펫/페티널 — 1</li>
    <li><span class="dot" style="background:#9b59b6"></span>펫생각 — 1</li>
    <li><span class="dot" style="background:#1abc9c"></span>인트라젠 — 1</li>
    <li><span class="dot" style="background:#e91e8c"></span>베터 — 1</li>
  </ul>
</div>
```

색 팔레트는 고정 5색(`#6ea0ff #f39c12 #9b59b6 #1abc9c #e91e8c`)을 순서대로
쓰고, 브랜드가 5개보다 많으면 나머지는 "기타"로 묶어서 색 하나를 더 배정한다
(무한정 늘리지 않는다). 브랜드가 1개뿐이면 파이차트 의미가 없으니 표만 쓴다.

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
  .wrap{max-width:1040px;margin:0 auto}
  h1{font-size:1.6rem;margin-bottom:4px} .sub{color:var(--muted);margin-bottom:24px}
  .banner{background:#2a1f10;border:1px solid #5a3d10;color:#f1c40f;
          padding:12px 16px;border-radius:8px;margin-bottom:24px;font-size:.92rem}
  .split{display:grid;grid-template-columns:1fr 1fr;gap:20px;align-items:start}
  @media(max-width:760px){.split{grid-template-columns:1fr}}
  .card{background:var(--card);border:1px solid var(--line);border-radius:12px;
        padding:20px;margin-bottom:20px}
  .gauge{display:flex;flex-direction:column;align-items:center;text-align:center;margin-bottom:12px}
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
  .tier-block{border-left:3px solid var(--line);padding-left:14px;margin-bottom:18px}
  .tier-block:last-child{margin-bottom:0}
  .tier-block.required{border-left-color:var(--accent)}
  .tier-block.recommended{border-left-color:#5a6577}
  .tier-block.optional{border-left-color:#333d4a;opacity:.85}
  .tier-chip{display:inline-block;font-size:.72rem;font-weight:700;text-transform:uppercase;
    letter-spacing:.05em;padding:3px 9px;border-radius:5px;margin-bottom:10px}
  .tier-chip.required{background:#16264a;color:var(--accent)}
  .tier-chip.recommended{background:#232b36;color:#aab4c2}
  .tier-chip.optional{background:#1a1f26;color:#6b7684}
  .note{color:var(--muted);font-size:.85rem;margin-top:10px}
  .ox-good{color:var(--good);font-weight:700} .ox-bad{color:var(--muted);font-weight:700}
  .tag{display:inline-block;background:#232b36;color:#aab4c2;font-size:.78rem;
    padding:2px 8px;border-radius:999px;margin:0 4px 4px 0}
  details{margin-bottom:8px;border:1px solid var(--line);border-radius:8px;padding:8px 12px}
  summary{cursor:pointer;color:var(--accent);font-size:.9rem}
  details p{margin:8px 0 2px;font-size:.88rem;color:var(--text);white-space:pre-wrap}
  .pie-wrap{display:flex;align-items:center;gap:24px;flex-wrap:wrap}
  .pie{width:150px;height:150px;border-radius:50%;position:relative;flex-shrink:0}
  .pie-hole{position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);
    width:82px;height:82px;border-radius:50%;background:var(--card)}
  .legend{list-style:none;margin:0;padding:0;font-size:.88rem}
  .legend li{margin-bottom:6px}
  .dot{display:inline-block;width:10px;height:10px;border-radius:50%;margin-right:8px}
  ul{margin:0;padding-left:20px}
</style>
</head>
<body>
<div class="wrap">
  <h1>{브랜드명} GEO 스냅샷</h1>
  <div class="sub">측정일자: {날짜} · 질문 5개 · 단일 시점</div>
  <div class="banner">⚠ 질문 5개, 단일 시점, 반복 측정 없음의 스냅샷입니다. 추세가 아니라 현재 한 장의 사진으로 읽어주세요.</div>

  <div class="split">
    <div>
      <div class="card"><h2>사이트 기술 점수</h2>(게이지 + 필수/권장/참고 3표 삽입)</div>
    </div>
    <div>
      <div class="card"><h2>핵심 지표</h2>(표 삽입 + 산식 .note)</div>
      <div class="card"><h2>질문별 결과</h2>(O/X표 + 등장브랜드 배지 + 질문별 details 삽입)</div>
      <div class="card"><h2>답변에서 발견된 브랜드</h2>(파이차트+범례 삽입, 브랜드 1개뿐이면 표만)</div>
      <!-- 경쟁사가 강한 질문 / 자주 인용된 도메인 등 GEO 관련 카드도 이 오른쪽 열에 계속 추가 -->
    </div>
  </div>

  <!-- 아래부터는 전체 폭 — 좌우를 종합하는 내용 -->
  <div class="card"><h2>사이트 문제 ↔ 실제 AI 답변 연결</h2>(내용 삽입)</div>
  <div class="card"><h2>우선 개선 과제</h2>(내용 삽입)</div>
  <div class="card"><h2>재측정 방법</h2>(내용 삽입)</div>
  <div class="card"><h2>부록 · 측정 질문 5개</h2>(표 삽입)</div>
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
