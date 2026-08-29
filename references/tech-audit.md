# GEO 테크니컬 진단

이 진단은 **AI 검색 시스템이 사이트에 접근하고, 공개 페이지를 발견하고, 내용을
해석하기 좋은 기술 상태인지** 확인한다. 실제 AI 답변의 언급·추천·인용을 보장하는
점수가 아니다. 실제 가시성은 사용자가 가져온 AI 답변으로 별도 측정한다.

결과는 다음 네 영역으로 나눈다.

1. AI 접근 상태 — 치명적 차단 여부
2. 사이트 기술 완성도 — 적용 가능한 항목 기준 100점
3. 콘텐츠 신뢰성 — 점수와 분리한 정성 판정
4. 참고 — 점수 미포함 관찰 항목

## 검사 범위

홈만 보고 사이트 전체를 판정하지 않는다. 최소한 홈·소개·대표 제품/서비스·대표
콘텐츠 등 공개 핵심 페이지 3~5개를 검사한다. 쇼핑몰이면 제품 상세, 미디어면 글
상세처럼 사이트 목적에 맞는 대표 페이지를 포함한다.

- `curl -L`로 리디렉션 후 최종 응답과 원본 HTML·헤더를 확인한다.
- 필요하면 브라우저 렌더링 결과도 확인한다. `<h1>`이나 `<p>` 개수만으로 본문
  노출을 판정하지 않는다.
- 로그인·장바구니·주문·관리 페이지는 공개 노출 대상에서 제외한다. 이런 페이지의
  noindex·접근 제한은 감점 사유가 아니다.
- 검색 노출용 크롤러와 모델 학습용 크롤러를 구분한다. 학습용 크롤러 차단은
  운영 정책이므로 감점하지 않는다.

## 1. AI 접근 상태

점수 평균으로 치명적 차단을 가리지 않는다. 네 항목을 먼저 판정한다.

| 항목 | 통과 | 일부 제한 | 노출 차단 |
|---|---|---|---|
| 공개 페이지 응답 | 핵심 페이지의 최종 URL이 200 | 일부 핵심 페이지만 4xx·5xx·리디렉션 오류 | 홈 또는 대부분의 핵심 페이지가 접근 불가 |
| 색인 허용 | 노출 대상 페이지에 noindex 없음 | 일부 핵심 페이지만 noindex | 홈 또는 대부분의 핵심 페이지가 noindex |
| 검색용 크롤러 접근 | 목표 모델의 검색용 크롤러가 robots.txt·WAF에서 접근 가능 | 일부 크롤러나 일부 경로만 제한 | 목표 검색용 크롤러가 사이트 전체에서 차단 |
| 핵심 콘텐츠 가독성 | 브랜드·제품·서비스·본문이 원본 HTML 또는 검증된 렌더링 결과에 존재 | 일부 핵심 정보가 렌더링 후에만 보이거나 검증 불완전 | 핵심 페이지가 빈 셸이며 목표 크롤러가 내용을 읽는다는 근거 없음 |

전체 판정:

- 네 항목 모두 통과: **접근 가능**
- 하나 이상 일부 제한이고 노출 차단은 없음: **일부 제한**
- 하나 이상 노출 차단: **노출 차단**

검색용 크롤러의 예:

- ChatGPT 검색: `OAI-SearchBot`
- Perplexity 검색: `PerplexityBot`
- Google 검색 및 Google 기반 검색 노출: `Googlebot`
- Bing 검색 기반 노출: `bingbot`

`GPTBot`, `Google-Extended` 등 학습·모델 개선 목적의 봇은 접근 상태와 기술 점수에서
제외한다. robots.txt에 봇 이름을 **명시했는지**가 아니라, 목표 검색용 크롤러가
실제로 차단되는지를 본다. 별도 규칙이 없다는 이유만으로 경고하지 않는다.

기본 확인 예시:

```bash
# 리디렉션 후 최종 상태·URL
curl -sL -o /dev/null -w '%{http_code} %{url_effective}\n' https://example.com

# 원본 HTML의 robots 지시와 응답 헤더
curl -sL https://example.com | grep -oiE "<meta[^>]+name=['\"]robots['\"][^>]*>"
curl -sIL https://example.com | grep -i '^x-robots-tag:'

# robots.txt 원문. 규칙은 user-agent 그룹과 경로를 함께 해석한다.
curl -sL https://example.com/robots.txt

# 검색용 user-agent로 실제 응답 확인. WAF 차단은 robots.txt와 별개다.
curl -sL -A 'OAI-SearchBot' -o /dev/null -w '%{http_code}\n' https://example.com
curl -sL -A 'PerplexityBot' -o /dev/null -w '%{http_code}\n' https://example.com

# 원본 HTML을 저장해 눈으로 핵심 텍스트·링크·메타를 확인한다.
curl -sL https://example.com
```

주의:

- 최초 URL의 301·308은 정상일 수 있다. 반드시 최종 URL과 최종 상태를 본다.
- robots.txt 차단은 크롤링 제어이고 noindex는 색인 제어다. 둘을 같은 의미로
  해석하지 않는다.
- User-Agent 문자열만 바꾼 curl은 실제 봇 IP 검증을 완전히 재현하지 못한다.
  WAF/CDN이 공식 봇 IP를 검증하는 경우에는 사이트 로그나 해당 서비스 설정을
  확인해야 하며, 확인할 수 없으면 통과가 아니라 **확인 제한**으로 근거를 남긴다.

## 2. 사이트 기술 완성도 (100점)

### 평가 항목과 배점

| 영역 | 배점 | 세부 항목 |
|---|---:|---|
| 크롤링·색인 | 25 | 최종 응답 5, 공개 페이지 색인 지시 10, 검색용 크롤러 접근 10 |
| 콘텐츠 발견 | 20 | sitemap 유효성 10, 핵심 URL 포함 5, 내부 링크 발견 가능성 5 |
| URL 정리 | 15 | canonical 정확성 4, 리디렉션·호스트·프로토콜 일관성 4, 404·410·soft 404 처리 4, 다국어 사이트 hreflang 3 |
| 페이지 정보 | 15 | 고유하고 설명적인 title 8, 고유하고 정확한 description 7 |
| 구조화 데이터 | 15 | 페이지 유형에 맞는 타입 5, 문법·필수 속성 유효성 5, 화면 내용과 일치 5 |
| 기술 전달 | 10 | 핵심 콘텐츠 가독성 5, HTTPS·핵심 리소스·WAF 전달 안정성 5 |
| 합계 | 100 | |

각 세부 항목은 다음처럼 계산한다.

- ✅ 충족: 배점 100%
- ⚠️ 일부 충족·일부 페이지만 문제·확인 제한: 배점 50%
- ❌ 미충족: 0점
- 해당 없음: 분모에서 제외하고 적용 가능한 항목의 점수를 100점으로 환산

```text
기술 점수 = round(획득 점수 합 / 적용 가능한 배점 합 × 100)
```

### 점수 상한

아래 문제가 있으면 다른 항목이 좋아도 높은 등급으로 보이지 않게 상한을 적용한다.

| 문제 | 점수 상한 |
|---|---:|
| AI 접근 상태가 노출 차단 | 49점 |
| AI 접근 상태가 일부 제한 | 69점 |
| AI 접근 상태가 접근 가능 | 상한 없음 |

상한 적용 전 원점수도 내부 계산에 남기되, 리포트에는 최종 점수와 상한 적용 사유를
함께 쓴다. 예: `49/100 — 원점수 82점이지만 홈 noindex로 상한 적용`.

### 등급

| 점수 | 등급 |
|---|---|
| 90~100 | 우수 |
| 70~89 | 양호 |
| 50~69 | 보완 필요 |
| 0~49 | 시급 |

이 등급은 업계 공인 벤치마크가 아니라, 이 스킬 안에서 동일 기준으로 재측정하기 위한
**내부 체크리스트 등급**이라고 명시한다.

### 세부 판정 규칙

#### sitemap

파일 존재만으로 통과시키지 않는다.

- XML이 유효하고 정상 응답하는가
- 공개·색인 대상인 절대 URL만 포함하는가
- 홈·소개·대표 제품/서비스·대표 콘텐츠가 포함되는가
- 3xx·4xx·5xx·noindex URL이나 비대표 중복 URL을 넣지 않았는가
- 50,000 URL 또는 비압축 50MB 제한을 넘으면 sitemap index로 나눴는가
- `lastmod`를 쓴다면 실제 수정일과 일치하는가

#### 내부 링크 발견 가능성

대표 페이지가 홈·카테고리·목록 페이지의 실제 `<a href>` 링크로 연결되는지 본다.
사이트맵에만 있고 내부 링크로 갈 수 없는 고립 페이지는 ⚠️ 또는 ❌다. 버튼의
JavaScript 이벤트만으로 이동하고 크롤러가 URL을 발견할 수 없으면 감점한다.

#### title·description

고정 글자 수를 합격 기준으로 쓰지 않는다. 다음을 본다.

- 비어 있지 않은가
- 페이지별로 고유한가
- 해당 페이지의 실제 내용을 정확히 설명하는가
- 키워드·브랜드명을 반복해서 채우지 않았는가

길이가 지나치게 길거나 짧아 정보 전달이 어려운 경우는 근거와 함께 ⚠️로 판단할 수
있지만, `title 50~60자`, `description 150~160자`를 공식 기준처럼 적용하지 않는다.

#### canonical·리디렉션

canonical은 모든 페이지에 무조건 있어야 하는 필수 태그로 취급하지 않는다. 중복·유사
URL이 있거나 사이트가 canonical을 제공할 때 다음을 검사한다.

- 절대 HTTPS URL인가
- 정상 응답하고 색인 가능한 대표 URL을 가리키는가
- sitemap·내부 링크·리디렉션의 대표 URL과 충돌하지 않는가
- canonical 페이지는 가능하면 self-canonical인가
- HTTP/www/non-www/후행 슬래시 등 중복 진입점이 하나의 대표 URL로 일관되게
  정리되는가

#### 구조화 데이터

`application/ld+json` 개수만 세지 않는다. 페이지에 적용되는 타입만 평가한다.

- 홈·회사 소개: `Organization` 또는 가장 구체적인 하위 타입
- 제품 상세: 실제 단일 제품을 설명할 때 `Product`
- 글 상세: `Article`, `BlogPosting`, `NewsArticle` 중 실제 성격에 맞는 타입

해당 페이지 유형이 사이트에 없으면 그 타입은 해당 없음이다. 구조화 데이터는
파싱 가능해야 하고 필수 속성을 충족해야 하며, 가격·재고·작성자·날짜 등 마크업된
정보가 사용자 화면의 내용과 일치해야 한다. 가능하면 Rich Results Test 또는
Schema.org Validator로 검증한다.

#### 404·410·soft 404

무작위로 만든 존재하지 않는 URL이 404 또는 410을 반환하는지 확인한다. 삭제된 URL에
명확한 대체 페이지가 있으면 관련 URL로의 301도 정상이다. 오류 안내 화면을 보여주면서
200을 반환하거나 모든 잘못된 URL을 홈으로 보내는 것은 soft 404로 감점한다.

#### 다국어·다지역 사이트

목표 국가·언어별로 별도 URL을 운영하는 경우에만 hreflang을 평가한다. 언어·지역
코드가 유효하고, 각 페이지가 자기 자신과 대응 언어 페이지를 상호 참조하며,
canonical이 같은 언어의 대표 URL을 가리키는지 확인한다. 단일 언어·단일 URL
사이트에는 해당 없음으로 처리한다.

#### HTTPS·전달 안정성

- 최종 URL이 HTTPS이고 인증서 오류가 없는가
- HTTP가 HTTPS 대표 URL로 일관되게 이동하는가
- 핵심 CSS·JS·이미지·API가 robots.txt나 인증 오류로 막혀 본문 이해를 방해하지 않는가
- 일반 브라우저와 목표 검색용 크롤러에 핵심 페이지가 2xx로 전달되는가

## 3. 콘텐츠 신뢰성 (점수와 분리)

기술 문제와 콘텐츠 품질 문제를 한 점수에 섞지 않는다. 적용 가능한 항목을 확인해
**충분 / 일부 보완 / 부족**으로 판정한다.

| 페이지 유형 | 확인 항목 |
|---|---|
| 제품·서비스 | 제품명·제공 주체, 성분·사양, 가격·대상·주의사항, 수치·효능·판매 실적 주장의 기준일과 확인 가능한 근거 |
| 글·매거진 | 작성자 또는 책임 주체, 게시일·수정일, 참고 출처, 검수자가 실제로 필요한 전문 주제라면 검수 정보 |
| 회사·브랜드 | 운영 법인·브랜드·제품 관계, 소개, 연락 가능한 정보, 공식 프로필 연결 |
| 공통 | 핵심 주장이 문단 안에서 이해되고 출처·근거와 가까이 연결되는가 |

작성자·검수자·날짜를 모든 페이지에 일률적으로 요구하지 않는다. 페이지 성격과 주장
위험도에 따라 적용 여부를 정하고, 해당 없으면 감점하지 않는다.

## 4. 참고 (점수 미포함)

다음은 관찰만 하고 기술 점수나 콘텐츠 신뢰성 판정에 가산·감점하지 않는다.

- `/llms.txt` 존재와 내용
- `GPTBot`, `Google-Extended` 등 학습·모델 개선용 크롤러 허용 여부
- robots.txt에 AI 크롤러 정책을 명시적으로 적었는지 여부

llms.txt가 있으면 `llms.txt 확인됨`, 없으면 `llms.txt 없음`으로만 기록한다.
“AI 노출에 유리하다”, “사이트 안내서 역할을 한다”처럼 효과가 검증된 것처럼 표현하지
않는다.

## 보고 형식

```text
AI 접근 상태: 일부 제한 — 제품 상세 2개가 noindex
사이트 기술 점수: 69/100 (보완 필요) — 원점수 81점, 일부 제한 상한 적용

[AI 접근 상태]
공개 페이지 응답 / 색인 허용 / 검색용 크롤러 접근 / 핵심 콘텐츠 가독성

[사이트 기술 완성도]
크롤링·색인 / 콘텐츠 발견 / URL 정리 / 페이지 정보 / 구조화 데이터 / 기술 전달

[콘텐츠 신뢰성]
충분 / 일부 보완 / 부족 + 페이지 유형별 근거

[참고 · 점수 미포함]
llms.txt / 학습용 크롤러 정책
```

리포트에는 항상 다음을 함께 표시한다.

- AI 접근 상태와 근거
- 최종 기술 점수·등급·상한 적용 여부
- 세부 영역별 획득 점수
- 콘텐츠 신뢰성 판정과 적용 페이지
- 참고 항목은 점수 미포함이라는 설명
- 이 진단은 기술적 준비 상태이며 실제 AI 추천·인용 보장이 아니라는 한계

## 기준 문서

- OpenAI Crawlers: https://developers.openai.com/api/docs/bots
- Perplexity Crawlers: https://docs.perplexity.ai/docs/resources/perplexity-crawlers
- Google robots.txt: https://developers.google.com/search/docs/crawling-indexing/robots/intro
- Google JavaScript SEO: https://developers.google.com/search/docs/crawling-indexing/javascript/javascript-seo-basics
- Google sitemaps: https://developers.google.com/search/docs/crawling-indexing/sitemaps/build-sitemap
- Google title links: https://developers.google.com/search/docs/appearance/title-link
- Google snippets: https://developers.google.com/search/docs/appearance/snippet
- Google canonicalization: https://developers.google.com/search/docs/crawling-indexing/consolidate-duplicate-urls
- Google structured data guidelines: https://developers.google.com/search/docs/appearance/structured-data/sd-policies
- Google crawling errors: https://developers.google.com/search/docs/crawling-indexing/troubleshoot-crawling-errors
