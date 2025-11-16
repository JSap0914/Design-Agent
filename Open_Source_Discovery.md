# Open Source Discovery System for Design Agent

## 📋 목차
1. [개요](#1-개요)
2. [핵심 기능](#2-핵심-기능)
3. [워크플로우 통합](#3-워크플로우-통합)
4. [검색 전략](#4-검색-전략)
5. [사용자 상호작용](#5-사용자-상호작용)
6. [문서화 시스템](#6-문서화-시스템)
7. [구현 세부사항](#7-구현-세부사항)
8. [품질 기준](#8-품질-기준)

---

## 1. 개요

### 1.1 목적
디자인 에이전트가 사용자와 대화하는 과정에서 **실시간으로 관련 오픈소스 프로젝트, 라이브러리, 컴포넌트를 검색**하여 제안하고, 사용자 승인 후 문서에 자동으로 추가하는 시스템입니다.

### 1.2 핵심 가치
- ✅ **시간 절약**: 검증된 오픈소스 솔루션 활용으로 개발 시간 단축
- ✅ **품질 향상**: 커뮤니티에서 검증된 코드 사용
- ✅ **최신 트렌드**: 현재 가장 많이 사용되는 라이브러리 추천
- ✅ **맞춤형 추천**: 프로젝트 기술 스택에 맞는 솔루션만 제안

---

## 2. 핵심 기능

### 2.1 자동 검색 트리거

대화 중 특정 키워드나 컨텍스트에서 자동으로 오픈소스 검색:

```
사용자: "로그인 화면에 소셜 로그인 버튼을 추가해줘"
                    ↓
        [자동 검색 트리거 발동]
                    ↓
검색 키워드: "React social login library",
            "OAuth component library",
            "authentication UI components"
                    ↓
        [검색 결과 필터링 및 랭킹]
                    ↓
        [사용자에게 3가지 옵션 제시]
```

### 2.2 검색 카테고리

**UI 컴포넌트 라이브러리**
- React: Material-UI, Ant Design, Chakra UI, Radix UI, shadcn/ui
- Vue: Vuetify, Element Plus, Quasar
- Tailwind: DaisyUI, Flowbite, Headless UI

**디자인 시스템**
- IBM Carbon Design System
- Atlassian Design System
- Shopify Polaris
- Spectrum (Adobe)

**접근성 도구**
- react-aria (Adobe)
- Reach UI
- Radix Primitives
- Ariakit

**아이콘 라이브러리**
- Heroicons
- Lucide Icons
- Phosphor Icons
- Tabler Icons

**애니메이션 라이브러리**
- Framer Motion
- React Spring
- GSAP
- Lottie

**폼 관리**
- React Hook Form
- Formik
- TanStack Form
- Zod (validation)

**차트/데이터 시각화**
- Recharts
- Victory
- Chart.js
- D3.js

**날짜/시간**
- date-fns
- Day.js
- React DayPicker

---

## 3. 워크플로우 통합

### 3.1 기존 워크플로우에 추가

```
Phase 1: 화면 추출
         ↓
Phase 2: 디자인 옵션 생성
         ↓
Phase 3: ASCII UI 대화형 수정  ⭐ 오픈소스 검색 통합
    │
    ├─ 사용자: "버튼 스타일을 더 모던하게"
    │        ↓
    │   [검색] Tailwind UI 컴포넌트 라이브러리
    │        ↓
    │   [제안] "shadcn/ui, DaisyUI, Headless UI 중 선택"
    │        ↓
    │   사용자: "shadcn/ui 괜찮네요"
    │        ↓
    │   [문서 추가] Design_System_v0.9.md에 기록
    │
    ├─ 사용자: "아이콘이 필요해"
    │        ↓
    │   [검색] 오픈소스 아이콘 라이브러리
    │        ↓
    │   [제안] "Heroicons, Lucide, Phosphor 추천"
    │        ↓
    │   사용자: "Lucide로 할게요"
    │        ↓
    │   [문서 추가] Design_Guidelines_v0.9.md에 기록
    │
    └─ 사용자: "폼 검증 기능이..."
             ↓
        [검색] React 폼 라이브러리
             ↓
        [제안] "React Hook Form + Zod 조합 추천"
             ↓
        사용자: "좋아요!"
             ↓
        [문서 추가] Screen_Specifications_v0.9.md에 기록
         ↓
Phase 4: Design System 추출
         ↓
Phase 5: 코드 검증
         ↓
Phase 6: 문서 생성 (오픈소스 추천 포함)
```

### 3.2 실시간 검색 프로세스

```python
# 대화 중 키워드 감지
keywords_detected = analyze_user_message(user_input)
# 예: ["social login", "authentication", "OAuth"]

if keywords_detected:
    # 웹 검색 실행
    search_results = search_open_source(
        keywords=keywords_detected,
        tech_stack=project.tech_stack,  # React, TypeScript 등
        filters={
            "language": "TypeScript",
            "min_stars": 1000,
            "recent_update": "6_months",
            "has_typescript_support": True,
            "license": ["MIT", "Apache-2.0"]
        }
    )

    # 사용자에게 제안
    present_options_to_user(search_results[:3])

    # 사용자 선택 대기
    if user_approves:
        add_to_documentation(
            library=selected_library,
            category=category,
            rationale=decision_rationale
        )
```

---

## 4. 검색 전략

### 4.1 검색 소스

**GitHub**
- Stars 기준 정렬
- 최근 업데이트 확인 (6개월 이내)
- TypeScript 지원 여부
- 라이선스 확인 (MIT/Apache 2.0 우선)

**npm / yarn**
- Weekly downloads 기준
- 번들 크기 고려
- 의존성 수 확인
- 보안 취약점 여부

**웹 검색 (Google/Bing)**
- "best [technology] library 2025"
- "[use case] open source component"
- "React [feature] tutorial"
- Recent articles (1년 이내)

**큐레이션 사이트**
- awesome-react
- awesome-vue
- awesome-tailwindcss
- State of JS/CSS

### 4.2 랭킹 알고리즘

```python
def rank_open_source(library):
    score = 0

    # 1. 인기도 (40점)
    score += min(library.github_stars / 1000, 20)  # Max 20점
    score += min(library.npm_downloads / 10000, 20)  # Max 20점

    # 2. 최신성 (20점)
    months_since_update = library.last_update_months_ago
    if months_since_update < 3:
        score += 20
    elif months_since_update < 6:
        score += 15
    elif months_since_update < 12:
        score += 10
    else:
        score += 0

    # 3. 품질 (20점)
    if library.has_typescript:
        score += 10
    if library.has_tests:
        score += 5
    if library.has_documentation:
        score += 5

    # 4. 기술 스택 호환성 (20점)
    if library.matches_tech_stack:
        score += 20

    return score
```

### 4.3 필터링 기준

**필수 조건 (하나라도 미충족 시 제외)**
- ✅ MIT 또는 Apache 2.0 라이선스
- ✅ 지난 1년 이내 업데이트
- ✅ 최소 500+ GitHub Stars (또는 npm weekly downloads 10K+)
- ✅ 보안 취약점 없음
- ✅ 프로젝트 기술 스택과 호환

**우선순위 조건 (점수 가산)**
- ⭐ TypeScript 지원
- ⭐ 테스트 커버리지 80% 이상
- ⭐ 상세한 문서화
- ⭐ 활발한 커뮤니티 (Issues/PRs 활동)
- ⭐ 작은 번들 크기 (<50KB)

---

## 5. 사용자 상호작용

### 5.1 제안 방식

**Option A: 인라인 제안 (비침투적)**
```
에이전트: 로그인 화면에 소셜 로그인 버튼을 추가했습니다.
[ASCII UI 업데이트 표시]

💡 관련 오픈소스 추천:
   1. next-auth (⭐ 18.5k) - Next.js 인증 솔루션
      - OAuth, JWT, Magic Links 지원
      - 번들: 45KB | 업데이트: 2주 전

   2. Auth.js (⭐ 6.2k) - 프레임워크 독립적 인증
      - 40+ OAuth 제공자 지원
      - 번들: 38KB | 업데이트: 1주 전

   3. react-oauth/google (⭐ 2.1k) - Google OAuth 전용
      - 간단한 구현
      - 번들: 12KB | 업데이트: 3주 전

🔍 이 중 하나를 사용하시겠습니까? (번호 입력 또는 'skip')
```

**Option B: 컨텍스트 기반 자동 제안**
```
사용자: "데이터 테이블이 필요해요"
에이전트: 데이터 테이블을 추가합니다.

🔎 자동 검색 중... "React data table library"

✅ 3가지 옵션을 찾았습니다:
   1. TanStack Table (⭐ 22k) - 헤드리스 테이블
   2. AG Grid Community (⭐ 11k) - 엔터프라이즈급
   3. React Table (⭐ 9k) - 경량 솔루션

어떤 것을 사용하시겠습니까?
```

### 5.2 사용자 응답 처리

```python
user_response_patterns = {
    # 승인 패턴
    "accept": ["1", "첫번째", "TanStack Table", "좋아요", "사용할게요"],

    # 거부 패턴
    "reject": ["skip", "아니요", "나중에", "필요없어요"],

    # 더 보기 패턴
    "more_info": ["자세히", "상세 정보", "비교", "차이점"],

    # 대안 요청
    "alternatives": ["다른거", "더 찾아줘", "다른 옵션"]
}

def handle_user_response(response):
    if matches(response, "accept"):
        add_to_documentation()
        return "✅ 추가되었습니다!"

    elif matches(response, "more_info"):
        return detailed_comparison()

    elif matches(response, "alternatives"):
        return search_more_options()

    else:  # reject
        return "알겠습니다. 넘어갈게요."
```

### 5.3 의사결정 기록

사용자가 선택할 때마다 **왜 선택했는지** 기록:

```markdown
## 오픈소스 선택 로그

### 1. 소셜 로그인 구현
- **선택**: next-auth v5.0
- **이유**: Next.js 프로젝트에 최적화, 다양한 OAuth 제공자 지원
- **대안**: Auth.js (프레임워크 독립적이지만 Next.js 통합이 덜 간편)
- **결정 시각**: 2025-01-13 14:23
- **관련 화면**: 로그인 화면, 회원가입 화면

### 2. 아이콘 라이브러리
- **선택**: Lucide Icons v0.300
- **이유**: React 컴포넌트 형태, 가볍고 일관된 디자인, 트리 쉐이킹 지원
- **대안**: Heroicons (Tailwind 공식이지만 아이콘 수가 적음)
- **결정 시각**: 2025-01-13 14:28
- **관련 화면**: 모든 화면 (공통)
```

---

## 6. 문서화 시스템

### 6.1 추가될 문서 섹션

**Design_System_v0.9.md**
```markdown
## 오픈소스 컴포넌트 라이브러리

### UI 컴포넌트
- **shadcn/ui** (v0.8.0)
  - Purpose: 재사용 가능한 UI 컴포넌트
  - Components: Button, Input, Dialog, Dropdown
  - Why: Tailwind CSS 기반, 복사-붙여넣기 방식으로 커스터마이징 용이

### 아이콘
- **Lucide Icons** (v0.300)
  - Purpose: 모든 화면의 아이콘
  - Why: 일관된 디자인, React 최적화, 번들 크기 작음

### 폼 관리
- **React Hook Form** (v7.49) + **Zod** (v3.22)
  - Purpose: 폼 상태 관리 및 검증
  - Why: 성능 우수, TypeScript 지원, 선언적 검증
```

**Screen_Specifications_v0.9.md**
```markdown
## 로그인 화면

### 구현 라이브러리
- Authentication: next-auth v5.0
- Form: React Hook Form + Zod
- UI Components: shadcn/ui (Button, Input, Card)
- Icons: Lucide Icons

### 컴포넌트 매핑
```tsx
<Card>  {/* shadcn/ui Card */}
  <form onSubmit={handleSubmit}> {/* React Hook Form */}
    <Input icon={Mail} /> {/* shadcn Input + Lucide Mail icon */}
    <Button type="submit"> {/* shadcn Button */}
      Sign In
    </Button>
    <OAuthButtons> {/* next-auth */}
      <Button variant="outline">
        <Github /> Sign in with GitHub
      </Button>
    </OAuthButtons>
  </form>
</Card>
```
```

**Design_Guidelines_v0.9.md**
```markdown
## 오픈소스 사용 가이드라인

### 라이브러리 선택 원칙
1. MIT 또는 Apache 2.0 라이선스만 사용
2. 지난 6개월 이내 활발히 업데이트되는 프로젝트
3. TypeScript 지원 필수
4. 최소 1,000+ GitHub Stars
5. 번들 크기 고려 (가능한 한 작게)

### 설치 명령어
```bash
# UI 컴포넌트
npx shadcn-ui@latest init

# 아이콘
npm install lucide-react

# 인증
npm install next-auth

# 폼
npm install react-hook-form zod @hookform/resolvers
```

### 버전 관리
- 모든 라이브러리는 정확한 버전 명시 (^, ~ 사용 지양)
- 보안 업데이트 주간 확인
- Major 버전 업그레이드 전 Breaking Changes 리뷰 필수
```

**새로운 문서 추가: Open_Source_Recommendations_v0.9.md**
```markdown
# 오픈소스 추천 목록

## 프로젝트 정보
- **프로젝트명**: [프로젝트 이름]
- **기술 스택**: React 19, TypeScript, Next.js 15, Tailwind CSS
- **생성일**: 2025-01-13

---

## 카테고리별 추천

### 1. UI 컴포넌트 라이브러리
#### shadcn/ui ⭐ 선택됨
- **GitHub**: https://github.com/shadcn-ui/ui
- **Stars**: 85k+
- **License**: MIT
- **번들 크기**: ~15KB (트리 쉐이킹 적용)
- **선택 이유**:
  - Tailwind CSS 기반으로 프로젝트와 100% 호환
  - 복사-붙여넣기 방식으로 완전한 커스터마이징 가능
  - Radix UI Primitives 기반으로 접근성 우수
- **사용 화면**: 모든 화면
- **설치**: `npx shadcn-ui@latest init`

#### 고려했던 대안
- **Chakra UI**: 런타임 CSS-in-JS로 성능 이슈 우려
- **Material-UI**: 디자인이 너무 강하게 정의되어 커스터마이징 어려움

---

### 2. 인증 시스템
#### next-auth v5 ⭐ 선택됨
- **GitHub**: https://github.com/nextauthjs/next-auth
- **Stars**: 18.5k+
- **License**: ISC (MIT 호환)
- **번들 크기**: 45KB
- **선택 이유**:
  - Next.js App Router 완벽 지원
  - 40+ OAuth 제공자 내장
  - Edge Runtime 지원
- **사용 화면**: 로그인, 회원가입, 프로필
- **설치**: `npm install next-auth@beta`

---

### 3. 아이콘 라이브러리
#### Lucide Icons ⭐ 선택됨
- **GitHub**: https://github.com/lucide-icons/lucide
- **Stars**: 8k+
- **License**: ISC
- **번들 크기**: ~1KB per icon (트리 쉐이킹)
- **선택 이유**:
  - React 컴포넌트 형태로 사용 편리
  - 일관된 디자인 언어
  - 트리 쉐이킹 지원으로 번들 크기 최소화
- **사용 화면**: 모든 화면
- **설치**: `npm install lucide-react`

---

### 4. 폼 관리
#### React Hook Form + Zod ⭐ 선택됨
- **GitHub**:
  - React Hook Form: https://github.com/react-hook-form/react-hook-form
  - Zod: https://github.com/colinhacks/zod
- **Stars**: 39k+ (RHF), 30k+ (Zod)
- **License**: MIT
- **번들 크기**: 25KB (RHF) + 12KB (Zod)
- **선택 이유**:
  - 렌더링 최적화로 성능 우수
  - Zod와 완벽한 TypeScript 통합
  - 선언적 검증 스키마
- **사용 화면**: 로그인, 회원가입, 설정, 프로필 수정
- **설치**: `npm install react-hook-form zod @hookform/resolvers`

---

## 의존성 요약

```json
{
  "dependencies": {
    "next-auth": "5.0.0-beta.4",
    "react-hook-form": "^7.49.0",
    "zod": "^3.22.4",
    "@hookform/resolvers": "^3.3.4",
    "lucide-react": "^0.300.0"
  },
  "devDependencies": {
    "tailwindcss": "^3.4.1",
    "@types/node": "^20.10.6",
    "typescript": "^5.3.3"
  }
}
```

## 설치 스크립트

```bash
#!/bin/bash
# install-dependencies.sh

echo "📦 Installing UI components..."
npx shadcn-ui@latest init -y
npx shadcn-ui@latest add button input card dialog

echo "🔐 Installing authentication..."
npm install next-auth@beta

echo "📝 Installing form libraries..."
npm install react-hook-form zod @hookform/resolvers

echo "🎨 Installing icons..."
npm install lucide-react

echo "✅ All dependencies installed!"
```

## 보안 및 업데이트 체크리스트

- [ ] 매주 `npm audit` 실행
- [ ] Dependabot 알림 확인
- [ ] Major 버전 업데이트 전 Breaking Changes 리뷰
- [ ] 라이선스 변경 모니터링
- [ ] GitHub Security Advisories 구독

---

## 참고 자료

### 공식 문서
- shadcn/ui: https://ui.shadcn.com
- next-auth: https://authjs.dev
- React Hook Form: https://react-hook-form.com
- Zod: https://zod.dev
- Lucide: https://lucide.dev

### 커뮤니티
- Discord: [각 라이브러리 공식 Discord]
- Stack Overflow: [관련 태그]
```

---

## 7. 구현 세부사항

### 7.1 LangGraph 노드 추가

새로운 노드: `search_open_source`

```python
def search_open_source_node(state: DesignAgentState):
    """
    사용자 메시지 분석 후 관련 오픈소스 검색
    """
    user_message = state["current_user_message"]
    tech_stack = state["project_tech_stack"]

    # 1. 키워드 추출
    keywords = extract_keywords(user_message)

    # 2. 검색 필요 여부 판단
    if not needs_open_source_search(keywords):
        return state

    # 3. 웹 검색 실행
    search_queries = generate_search_queries(keywords, tech_stack)
    results = []

    for query in search_queries:
        # GitHub 검색
        github_results = search_github(query, tech_stack)
        # npm 검색
        npm_results = search_npm(query, tech_stack)
        # 웹 검색
        web_results = search_web(query + " 2025")

        results.extend(github_results + npm_results + web_results)

    # 4. 필터링 및 랭킹
    filtered = filter_results(results, tech_stack)
    ranked = rank_results(filtered)
    top_3 = ranked[:3]

    # 5. 사용자에게 제시
    state["open_source_suggestions"] = format_suggestions(top_3)

    return state
```

### 7.2 검색 API 통합

```python
import requests
from typing import List, Dict

class OpenSourceSearcher:
    def __init__(self):
        self.github_token = os.getenv("GITHUB_TOKEN")
        self.web_search_api = os.getenv("WEB_SEARCH_API_KEY")

    def search_github(self, query: str, language: str = "TypeScript") -> List[Dict]:
        """
        GitHub API를 사용한 검색
        """
        url = "https://api.github.com/search/repositories"
        params = {
            "q": f"{query} language:{language} stars:>500",
            "sort": "stars",
            "order": "desc",
            "per_page": 10
        }
        headers = {"Authorization": f"token {self.github_token}"}

        response = requests.get(url, params=params, headers=headers)
        repos = response.json()["items"]

        return [
            {
                "name": repo["name"],
                "url": repo["html_url"],
                "stars": repo["stargazers_count"],
                "description": repo["description"],
                "last_updated": repo["updated_at"],
                "license": repo.get("license", {}).get("spdx_id"),
                "language": repo["language"]
            }
            for repo in repos
        ]

    def search_npm(self, query: str) -> List[Dict]:
        """
        npm registry 검색
        """
        url = f"https://registry.npmjs.org/-/v1/search"
        params = {"text": query, "size": 10}

        response = requests.get(url, params=params)
        packages = response.json()["objects"]

        return [
            {
                "name": pkg["package"]["name"],
                "description": pkg["package"]["description"],
                "version": pkg["package"]["version"],
                "weekly_downloads": pkg.get("downloads", {}).get("weekly", 0),
                "npm_url": f"https://www.npmjs.com/package/{pkg['package']['name']}"
            }
            for pkg in packages
        ]

    def search_web(self, query: str) -> List[Dict]:
        """
        웹 검색 API 사용 (Google/Bing)
        """
        # WebSearch tool 사용 또는 직접 API 호출
        pass
```

### 7.3 State Schema 확장

```python
from typing import TypedDict, List, Dict, Optional

class OpenSourceRecommendation(TypedDict):
    category: str  # "ui-components", "auth", "forms", "icons", etc.
    name: str
    github_url: Optional[str]
    npm_url: Optional[str]
    stars: int
    license: str
    bundle_size: str
    description: str
    rationale: str  # 왜 추천하는지
    selected: bool  # 사용자가 선택했는지

class DesignAgentState(TypedDict):
    # 기존 필드...
    prd_content: str
    trd_content: str
    extracted_screens: List[str]

    # 새로 추가되는 필드
    open_source_suggestions: List[OpenSourceRecommendation]
    selected_open_source: List[OpenSourceRecommendation]
    open_source_search_history: List[Dict]  # 검색 로그
```

### 7.4 문서 생성 시 통합

```python
def generate_open_source_recommendations_doc(state: DesignAgentState) -> str:
    """
    Open_Source_Recommendations_v0.9.md 생성
    """
    selected = state["selected_open_source"]

    # 카테고리별 그룹화
    categorized = group_by_category(selected)

    doc = "# 오픈소스 추천 목록\n\n"
    doc += f"생성일: {datetime.now().isoformat()}\n\n"

    for category, items in categorized.items():
        doc += f"## {category}\n\n"
        for item in items:
            doc += f"### {item['name']} ⭐ 선택됨\n"
            doc += f"- **GitHub**: {item['github_url']}\n"
            doc += f"- **Stars**: {item['stars']}\n"
            doc += f"- **License**: {item['license']}\n"
            doc += f"- **번들 크기**: {item['bundle_size']}\n"
            doc += f"- **선택 이유**: {item['rationale']}\n\n"

    return doc
```

---

## 8. 품질 기준

### 8.1 검색 품질 지표

- **적합성**: 검색 결과가 사용자 요구사항과 80% 이상 일치
- **최신성**: 제안하는 라이브러리의 90%가 6개월 이내 업데이트
- **다양성**: 카테고리당 최소 2-3개 옵션 제공
- **정확성**: GitHub Stars, npm downloads 등 정보가 100% 정확

### 8.2 사용자 경험 지표

- **응답 시간**: 검색 결과 3초 이내 제시
- **수용률**: 사용자가 제안을 수용하는 비율 60% 이상
- **만족도**: 제안된 라이브러리에 대한 만족도 4.0/5.0 이상

### 8.3 문서 품질 지표

- **완성도**: 선택된 모든 라이브러리에 대한 상세 정보 포함
- **일관성**: 모든 라이브러리 정보 형식 통일
- **실용성**: 설치 명령어, 사용 예제 포함

---

## 9. 예시 시나리오

### 시나리오 1: 인증 시스템 추가

```
사용자: "Google과 GitHub 소셜 로그인을 추가하고 싶어요"

에이전트: 로그인 화면에 소셜 로그인을 추가하겠습니다.

🔍 관련 오픈소스를 검색 중입니다...

✅ 3가지 인증 라이브러리를 찾았습니다:

1. **next-auth v5.0** ⭐ 추천
   - GitHub Stars: 18,500+
   - 지원: Google, GitHub, 40+ OAuth 제공자
   - 번들: 45KB | 업데이트: 2주 전
   - 특징: Next.js App Router 완벽 지원

2. **Auth.js**
   - GitHub Stars: 6,200+
   - 프레임워크 독립적
   - 번들: 38KB | 업데이트: 1주 전

3. **react-oauth/google**
   - GitHub Stars: 2,100+
   - Google 전용 (가벼움)
   - 번들: 12KB | 업데이트: 3주 전

프로젝트에 Next.js를 사용 중이시므로 next-auth를 추천드립니다.
어떤 것을 사용하시겠습니까? (1, 2, 3 또는 skip)

사용자: "1번으로 할게요"

에이전트: ✅ next-auth v5.0를 선택하셨습니다!

📝 다음 문서에 추가되었습니다:
   - Design_System_v0.9.md (인증 시스템 섹션)
   - Screen_Specifications_v0.9.md (로그인 화면)
   - Open_Source_Recommendations_v0.9.md

[ASCII UI 업데이트하여 표시]
```

### 시나리오 2: 데이터 테이블 컴포넌트

```
사용자: "관리자 대시보드에 사용자 목록을 보여주는 테이블이 필요해요.
        정렬, 필터링, 페이지네이션 기능도 있어야 해요."

에이전트: 관리자 대시보드에 데이터 테이블을 추가하겠습니다.

🔍 "React data table with sorting filtering pagination"로 검색 중...

✅ 3가지 옵션을 찾았습니다:

1. **TanStack Table v8** ⭐ 추천
   - GitHub Stars: 22,000+
   - 헤드리스 UI (완전한 커스터마이징 가능)
   - 정렬, 필터, 페이지네이션, 가상화 모두 지원
   - 번들: 15KB | TypeScript 네이티브
   - 업데이트: 1주 전

2. **AG Grid Community**
   - GitHub Stars: 11,000+
   - 엔터프라이즈급 기능
   - 번들: 120KB (무거움)
   - 업데이트: 3일 전

3. **React Table v7**
   - GitHub Stars: 9,000+
   - 경량 솔루션
   - 번들: 12KB
   - ⚠️ 업데이트: 8개월 전 (TanStack Table이 후속 버전)

Tailwind CSS 커스터마이징이 필요하시므로 TanStack Table을 추천합니다.
선택하시겠습니까?

사용자: "TanStack Table로 할게요. 그런데 가상화가 뭔가요?"

에이전트: 좋은 질문입니다!

**가상화 (Virtualization)**란:
- 대량의 데이터(1000+ 행)를 렌더링할 때 성능 최적화 기법
- 화면에 보이는 행만 DOM에 렌더링
- 나머지는 스크롤 시 동적으로 렌더링
- 결과: 10,000개 행도 부드럽게 스크롤 가능

TanStack Table은 TanStack Virtual과 통합하여 이 기능을 지원합니다.

사용자 목록이 많을 것으로 예상되므로 함께 설치할까요?

사용자: "네 좋아요!"

에이전트: ✅ 추가되었습니다:
   - TanStack Table v8.11.0
   - TanStack Virtual v3.0.0 (가상화)

📝 문서 업데이트:
   - Open_Source_Recommendations_v0.9.md
   - Screen_Specifications_v0.9.md (관리자 대시보드)

설치 명령어:
```bash
npm install @tanstack/react-table @tanstack/react-virtual
```

[ASCII UI 업데이트]
```

---

## 10. 향후 개선 방향

### 10.1 AI 기반 스마트 추천

- 프로젝트 컨텍스트 분석하여 자동 추천
- 사용자 선호도 학습 (이전 선택 기반)
- 유사 프로젝트에서 많이 사용된 조합 추천

### 10.2 실시간 호환성 검증

- 선택한 라이브러리 간 의존성 충돌 자동 감지
- 버전 호환성 체크
- 번들 크기 시뮬레이션

### 10.3 커뮤니티 피드백 통합

- Stack Overflow Q&A 분석
- Reddit, Discord 커뮤니티 의견 수집
- "이 라이브러리의 장단점" 자동 요약

### 10.4 코드 스니펫 자동 생성

- 선택한 라이브러리 기반 샘플 코드 생성
- 프로젝트 구조에 맞는 파일 배치 제안
- 설정 파일 자동 생성 (tailwind.config.js 등)

---

*이 문서는 Design Agent의 오픈소스 검색 및 추천 시스템을 정의합니다.*
*버전: 1.0 | 작성일: 2025-01-13*
