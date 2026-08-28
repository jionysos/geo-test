# 테크니컬 진단

크롤러의 눈 기준으로 확인한다 — "코드에 있다"가 아니라 "자바스크립트 없이 받은
HTML/헤더에 있다"가 기준이다. 항목은 **필수/권장/참고** 3단으로 나눈다. 참고 항목
(llms.txt)은 없다고 감점하지 않는다 — 있으면 가산, 없으면 "아직 없음"으로만 기록.

## 필수 (하나라도 ❌면 다른 진단보다 이것부터 알린다)

```bash
# HTTP 상태코드 — 200이 아니면 다른 진단 의미 없음
curl -s -o /dev/null -w '%{http_code}\n' https://example.com

# noindex 사고 감지 (본문 메타 + 헤더 둘 다 확인)
curl -sL https://example.com | grep -oiE '<meta[^>]*robots[^>]*>'
curl -sIL https://example.com | grep -i 'x-robots-tag'

# robots.txt — AI 크롤러를 포함해 실수로 전체 차단하고 있지 않은지
curl -sL https://example.com/robots.txt

# SSR 본문 노출 — 자바스크립트 없이 본문이 실제로 오는가
curl -sL https://example.com | grep -c '<h1'
curl -sL https://example.com/대표-상세-페이지-경로 | grep -c '<p'
```

| 항목 | 상태 | 근거 |
|---|---|---|
| HTTP 200 | | |
| noindex 없음(메타+헤더) | | |
| robots.txt AI 크롤러 미차단 | | |
| SSR 본문 노출 | | |

## 권장

```bash
# sitemap 존재·규모
curl -sL https://example.com/sitemap.xml | head -20

# 메타 3종 + canonical
curl -sL https://example.com | grep -oiE '<title[^>]*>.*</title>|<meta[^>]*description[^>]*>|<link[^>]*canonical[^>]*>'

# 구조화 데이터 존재 (Organization / Product / Article)
curl -sL https://example.com | grep -oE 'application/ld\+json' | wc -l
curl -sL https://example.com | grep -oE '"@type"\s*:\s*"[A-Za-z]+"'

# AI 크롤러 접근 정책이 명시적인가 (무정책=우연에 맡기는 것)
curl -sL https://example.com/robots.txt | grep -iE 'GPTBot|ClaudeBot|PerplexityBot|Google-Extended|CCBot'

# 404가 실제로 404인가 (캐시 베이크 사고 점검)
curl -s -o /dev/null -w '%{http_code}\n' https://example.com/존재하지-않는-경로-xyz123
```

| 항목 | 상태 | 근거 |
|---|---|---|
| sitemap.xml 존재·규모 적정 | | |
| title(50~60자)·description(150~160자)·canonical | | |
| 구조화 데이터(Organization/Product/Article) | | |
| 브랜드명 표기 일관성 (페이지마다 동일 표기인가) | | |
| AI 크롤러 정책 명시(학습/색인/실시간fetch 구분) | | |
| 인용 가능한 근거 요소(작성자·기준일·데이터 출처가 문단에 있는가) | | |
| 404가 실제 404 | | |

브랜드명 표기 일관성은 사이트 내 3~5개 주요 페이지(홈/제품/소개/블로그 대표글)에서
브랜드명이 등장하는 방식을 grep해서 비교한다:

```bash
for url in https://example.com https://example.com/about https://example.com/products; do
  echo "== $url =="; curl -sL "$url" | grep -oiE '브랜드명패턴' | sort -u
done
```

## 참고 (필수 아님, 있으면 가산)

```bash
curl -sL https://example.com/llms.txt
```

없으면 "llms.txt 없음 — 도입 시 AI에게 사이트 안내서 역할"로만 기록하고 점수에서
빼지 않는다.

## 보고 형식

```
| 구분 | 항목 | 상태 | 근거 |
|---|---|---|---|
| 필수 | HTTP 200 | ✅ | |
| 필수 | noindex 없음 | ❌ | X-Robots-Tag: noindex 헤더 발견 — 최우선 수정 |
| 권장 | 구조화 데이터 | ⚠️ | Organization만 있음, Product 없음 |
| 참고 | llms.txt | ❌(참고) | 아직 없음, 필수 아님 |
```

필수 항목 ❌는 3단계 보고에서 최상단에, 다른 모든 개선 제안보다 먼저 알린다 —
noindex 사고는 다른 최적화를 전부 무효화한다.
