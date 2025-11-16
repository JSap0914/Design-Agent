# ANYON 디자인 에이전트 제작 플랜 (LangGraph + BMAD 디자인 방법론)

## 📋 목차
1. [역할 정의 및 경계](#1-역할-정의-및-경계)
2. [BMAD 디자인 방법론 차용](#2-bmad-디자인-방법론-차용)
3. [LangGraph 아키텍처](#3-langgraph-아키텍처)
4. [4단계 워크플로우](#4-4단계-워크플로우)
5. [대화형 ASCII UI 시스템](#5-대화형-ascii-ui-시스템)
6. [문서 생성](#6-문서-생성)
7. [ANYON 통합](#7-anyon-통합)
8. [구현 예제](#8-구현-예제)

---

## 1. 역할 정의 및 경계

### 1.1 명확한 역할 분담

```
┌─────────────────────────────────────────────────────┐
│  기획 에이전트 (이미 완료된 INPUT)                   │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━    │
│  ✓ PRD.md (User Personas, User Journeys, Pain Points) │
│  ✓ TRD.md (Technical Requirements)                   │
│  ✓ 화면 목록 정의                                    │
│  ✓ 기능 요구사항                                     │
└─────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────┐
│  디자인 에이전트 (이 문서의 범위) ⭐                │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━    │
│  1. PRD/TRD 읽고 화면 목록 추출                     │
│  2. 각 화면을 ASCII UI로 변환                       │
│  3. 사용자와 대화하며 디자인 수정                   │
│  4. Design System 정의                              │
│  5. Google AI Studio에서 실제 코드 생성             │
│  6. 업로드된 코드 검증 (품질 점수 90/100 이상)     │
│  7. 6개 문서 생성                                    │
│     - Design_System_v0.9.md                         │
│     - UX_Flow_v0.9.md                               │
│     - Screen_Specifications_v0.9.md                 │
│     - Google_AI_Studio_Prompts_v0.9.md              │
│     - Design_Guidelines_v0.9.md                     │
│     - Open_Source_Recommendations_v0.9.md ⭐        │
│  8. 패키지 생성 (6개 문서 + 검증된 코드)            │
└─────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────┐
│  기술 스펙 에이전트 (다음 단계)                     │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━    │
│  INPUT: 6개 디자인 문서 + 검증된 코드 + 검증 리포트│
│  ✓ 디자인 문서 기반 기술 스펙 작성                  │
│  ✓ API 명세, 데이터 모델, 아키텍처 정의            │
│  ✓ 검증된 코드를 참고하여 구현 가이드 작성          │
│  ✓ 오픈소스 라이브러리를 기술 스택에 통합          │
└─────────────────────────────────────────────────────┘
```

### 1.2 디자인 에이전트가 하는 일

✅ **해야 할 것:**
- PRD에서 화면 목록 추출
- 화면을 ASCII UI로 시각화
- 사용자와 대화하며 레이아웃 수정
- **실시간 오픈소스 라이브러리 검색 및 추천** ⭐ 신규
- 색상, 타이포, 간격 시스템 정의
- 컴포넌트 라이브러리 정의
- 접근성 검증
- 반응형 스펙 정의
- Google AI Studio 프롬프트 생성
- **업로드된 코드 품질 검증 (90/100 이상)** ⭐ 신규
- 6개 문서 생성 (Open_Source_Recommendations_v0.9.md 포함)
- **검증된 코드 + 문서 패키지를 기술 스펙 에이전트에 전달** ⭐ 신규

❌ **하면 안 되는 것:**
- User Persona 만들기 (PRD에 이미 있음)
- User Journey 매핑 (PRD에 이미 있음)
- Pain Point 발굴 (PRD에 이미 있음)
- 기능 요구사항 정의 (PRD 영역)
- Epic/Story 분해 (기술 스펙 에이전트 영역)
- 실제 프로덕션 코드 작성 (개발 에이전트 영역)

---

## 2. BMAD 디자인 방법론 차용

### 2.1 BMAD에서 가져올 핵심 요소

BMAD의 `create-ux-design` 워크플로우에서 **순수 디자인 부분만** 차용:

#### 1) Design Exploration (옵션 생성)
```
하나의 정답을 제시하지 않고, 여러 디자인 옵션 생성
→ 사용자가 선택하게 함

예: "홈 화면" 3가지 옵션
- Option A: 카드 기반 레이아웃
- Option B: 리스트 기반 레이아웃  
- Option C: 분할 화면 레이아웃

사용자: "A와 C를 섞은 느낌으로..."
```

#### 2) Collaborative Iteration (대화형 수정)
```
템플릿 채우기가 아닌 진정한 협업

사용자: "이 버튼 위치를 오른쪽으로 옮겨줘"
AI: [ASCII UI 수정하여 다시 보여줌]
사용자: "좋아, 그런데 색상을 좀 더 밝게..."
AI: [다시 수정]
사용자: "완벽해! 확정"
```

#### 3) Decision Documentation (결정 근거 기록)
```
모든 디자인 결정에 "왜?"를 기록

Decision #1:
- 선택: 카드 기반 레이아웃
- 근거: 정보 스캔성이 높고, 모바일 친화적
- 대안: 리스트형 (정보 밀도가 높지만 모바일에서 불편)
```

#### 4) Adaptive Communication (사용자 수준에 맞춤)
```python
if user_skill_level == "beginner":
    "와이어프레임(화면의 골격을 보여주는 간단한 스케치)을 만들어볼게요"
elif user_skill_level == "intermediate":
    "와이어프레임을 만들어볼게요"
else:
    "Low-fidelity wireframe 생성합니다"
```

#### 5) Quality Validation (품질 검증)
```yaml
Design System Checklist:
  ✓ 색상 팔레트 정의 (Primary, Secondary, Neutral, Semantic)
  ✓ 타이포그래피 시스템 (폰트, 크기, 행간)
  ✓ Spacing 시스템 (8pt grid)
  ✓ Border Radius 일관성
  ✓ Shadow/Elevation 정의
  ✓ Icon Style 통일
  ✓ Component 재사용성
```

### 2.2 BMAD에서 가져오지 않을 것

❌ Phase 1 (UX Foundation) 전체
- User Research → PRD에 있음
- Personas → PRD에 있음
- User Journeys → PRD에 있음
- Pain Points → PRD에 있음

❌ Epic Breakdown
- 기술 스펙 에이전트에서 처리

---

## 3. LangGraph 아키텍처

### 3.1 State Schema (간결 버전)

```python
from typing import TypedDict, List, Dict, Optional
from datetime import datetime

class DesignAgentState(TypedDict):
    # INPUT (기획 에이전트로부터)
    project_id: str
    project_name: str
    prd_content: str
    trd_content: str
    
    # Phase 1: 화면 분석
    screens: List[Dict]  # PRD에서 추출한 화면 목록
    current_screen_index: int
    
    # Phase 2: 디자인 옵션
    design_options: List[Dict]  # 각 화면의 레이아웃 옵션
    selected_options: Dict[str, str]  # {screen_name: option_id}
    
    # Phase 3: ASCII UI 대화
    current_ascii_ui: str
    ascii_ui_history: List[Dict]  # 수정 이력
    conversation_history: List[Dict]
    user_feedback: Optional[str]
    
    # Phase 4: Design System
    design_system: Dict
    component_library: Dict
    accessibility_checks: Dict
    responsive_specs: Dict
    
    # OUTPUT (5개 문서)
    documents: Dict[str, str]
    
    # 메타데이터
    current_phase: int  # 1-4
    status: str
    decisions: List[Dict]  # 결정 + 근거
    quality_score: Optional[int]
    created_at: datetime
    updated_at: datetime
```

### 3.2 Graph 구조 (간결 버전)

```python
from langgraph.graph import StateGraph, END

class DesignAgentGraph:
    def __init__(self):
        self.graph = StateGraph(DesignAgentState)
        
        # 6개 핵심 노드만
        self.graph.add_node("extract_screens", self.extract_screens_node)
        self.graph.add_node("generate_options", self.generate_options_node)
        self.graph.add_node("create_ascii_ui", self.create_ascii_ui_node)
        self.graph.add_node("refine_design", self.refine_design_node)
        self.graph.add_node("build_design_system", self.build_design_system_node)
        self.graph.add_node("generate_documents", self.generate_documents_node)
        
        # 간단한 흐름
        self.graph.set_entry_point("extract_screens")
        self.graph.add_edge("extract_screens", "generate_options")
        self.graph.add_edge("generate_options", "create_ascii_ui")
        
        # 대화형 반복
        self.graph.add_conditional_edges(
            "create_ascii_ui",
            self.should_refine_or_continue,
            {
                "refine": "refine_design",
                "next_screen": "create_ascii_ui",
                "done": "build_design_system"
            }
        )
        
        self.graph.add_edge("refine_design", "create_ascii_ui")
        self.graph.add_edge("build_design_system", "generate_documents")
        self.graph.add_edge("generate_documents", END)
        
        self.compiled_graph = self.graph.compile()
```

---

## 4. 4단계 워크플로우

### Phase 1: 화면 분석 및 추출

```python
async def extract_screens_node(state: DesignAgentState) -> DesignAgentState:
    """
    PRD에서 화면 목록 추출
    """
    state["current_phase"] = 1
    
    prd = state["prd_content"]
    
    # PRD 파싱하여 화면 목록 추출
    screens = await extract_screens_from_prd(prd)
    
    # 각 화면의 기본 정보 구성
    screen_list = []
    for screen in screens:
        screen_info = {
            "name": screen["name"],
            "description": screen["description"],
            "key_elements": screen["elements"],  # 버튼, 입력, 리스트 등
            "user_actions": screen["actions"],   # 사용자가 할 수 있는 것
            "approved": False
        }
        screen_list.append(screen_info)
    
    state["screens"] = screen_list
    state["current_screen_index"] = 0
    
    # 사용자에게 알림
    message = f"""
┌────────────────────────────────────┐
│ 📱 PRD 분석 완료                   │
└────────────────────────────────────┘

발견된 화면: {len(screen_list)}개

{format_screen_list(screen_list)}

이제 각 화면의 디자인을 시작하겠습니다.
    """
    
    state["conversation_history"].append({
        "phase": 1,
        "message": message
    })
    
    return state
```

### Phase 2: 디자인 옵션 생성

```python
async def generate_options_node(state: DesignAgentState) -> DesignAgentState:
    """
    각 화면에 대해 2-3개 디자인 옵션 생성
    BMAD Principle: Multiple Design Directions
    """
    state["current_phase"] = 2
    
    options = {}
    
    for screen in state["screens"]:
        # 화면 특성에 맞는 2-3개 레이아웃 옵션 생성
        screen_options = await generate_layout_options(
            screen,
            state["prd_content"]
        )
        
        # 각 옵션을 간단한 ASCII로 미리보기
        for option in screen_options:
            option["preview_ascii"] = generate_simple_preview(option)
        
        options[screen["name"]] = screen_options
        
        # 사용자에게 옵션 제시
        message = f"""
┌────────────────────────────────────┐
│ 🎨 {screen['name']} - 레이아웃 옵션  │
└────────────────────────────────────┘

{format_options_with_preview(screen_options)}

어떤 옵션이 좋으신가요? (A/B/C 또는 "A와 B를 섞은 느낌")
        """
        
        # 사용자 선택 대기
        selection = await get_user_input(message)
        
        selected_option = await resolve_selection(
            screen_options,
            selection
        )
        
        state["selected_options"][screen["name"]] = selected_option["id"]
        
        # 결정 근거 기록
        state["decisions"].append({
            "phase": 2,
            "screen": screen["name"],
            "decision": f"Selected layout: {selected_option['name']}",
            "rationale": selection,
            "alternatives": [opt["name"] for opt in screen_options],
            "timestamp": datetime.now().isoformat()
        })
    
    state["design_options"] = options
    return state

def generate_simple_preview(option: Dict) -> str:
    """레이아웃 옵션을 간단한 ASCII로 미리보기"""
    
    if option["type"] == "card-grid":
        return """
    ┌──────────────────────┐
    │ ┌────┐ ┌────┐ ┌────┐│
    │ │    │ │    │ │    ││
    │ └────┘ └────┘ └────┘│
    │ ┌────┐ ┌────┐ ┌────┐│
    │ │    │ │    │ │    ││
    │ └────┘ └────┘ └────┘│
    └──────────────────────┘
        """
    elif option["type"] == "list":
        return """
    ┌──────────────────────┐
    │ ┌──────────────────┐ │
    │ │  Item 1          │ │
    │ └──────────────────┘ │
    │ ┌──────────────────┐ │
    │ │  Item 2          │ │
    │ └──────────────────┘ │
    │ ┌──────────────────┐ │
    │ │  Item 3          │ │
    │ └──────────────────┘ │
    └──────────────────────┘
        """
    elif option["type"] == "split-pane":
        return """
    ┌──────────────────────┐
    │ ┌─────┐ ┌──────────┐ │
    │ │     │ │          │ │
    │ │Side │ │  Main    │ │
    │ │bar  │ │  Content │ │
    │ │     │ │          │ │
    │ └─────┘ └──────────┘ │
    └──────────────────────┘
        """
```

### Phase 3: ASCII UI 대화형 생성 및 수정 ⭐

```python
async def create_ascii_ui_node(state: DesignAgentState) -> DesignAgentState:
    """
    선택된 옵션을 상세 ASCII UI로 변환
    BMAD Principle: Collaborative Design
    """
    state["current_phase"] = 3
    
    current_idx = state["current_screen_index"]
    screen = state["screens"][current_idx]
    
    # 선택된 옵션 가져오기
    selected_option_id = state["selected_options"][screen["name"]]
    selected_option = next(
        opt for opt in state["design_options"][screen["name"]]
        if opt["id"] == selected_option_id
    )
    
    # 상세 ASCII UI 생성
    ascii_ui = await generate_detailed_ascii_ui(
        screen,
        selected_option,
        state["prd_content"]
    )
    
    state["current_ascii_ui"] = ascii_ui
    
    # 사용자에게 표시
    display = f"""
┌────────────────────────────────────┐
│ 🎨 {screen['name']:<30}│
│ 버전: v1                           │
└────────────────────────────────────┘

{ascii_ui}

┌────────────────────────────────────┐
│ 💬 피드백을 입력하세요:            │
│                                    │
│ 수정 예시:                         │
│ - "버튼을 오른쪽 상단으로"         │
│ - "제목 폰트를 더 크게"            │
│ - "색상을 더 밝게"                 │
│ - "입력창 아래 버튼 배치"          │
│                                    │
│ 확정: "좋아", "확정", "다음"       │
└────────────────────────────────────┘
    """
    
    state["conversation_history"].append({
        "phase": 3,
        "screen": screen["name"],
        "ascii_ui": ascii_ui,
        "version": 1
    })
    
    # 사용자 피드백 대기 (다음 노드에서 처리)
    return state

async def refine_design_node(state: DesignAgentState) -> DesignAgentState:
    """
    사용자 피드백에 따라 ASCII UI 수정
    """
    feedback = state["user_feedback"]
    current_ascii = state["current_ascii_ui"]
    current_idx = state["current_screen_index"]
    screen = state["screens"][current_idx]
    
    # 피드백 분석 및 ASCII UI 수정
    modified_ascii = await modify_ascii_ui(
        current_ascii,
        feedback,
        screen
    )
    
    # 버전 업
    version = len([
        h for h in state["ascii_ui_history"]
        if h["screen"] == screen["name"]
    ]) + 1
    
    state["current_ascii_ui"] = modified_ascii
    
    # 수정 이력 기록
    state["ascii_ui_history"].append({
        "screen": screen["name"],
        "version": version,
        "feedback": feedback,
        "ascii_ui": modified_ascii,
        "timestamp": datetime.now().isoformat()
    })
    
    # 다시 표시
    display = f"""
┌────────────────────────────────────┐
│ 🎨 {screen['name']:<30}│
│ 버전: v{version:<29}│
└────────────────────────────────────┘

{modified_ascii}

┌────────────────────────────────────┐
│ 💬 추가 수정사항이 있으신가요?     │
│ (없으면 "확정" 또는 "다음")        │
└────────────────────────────────────┘
    """
    
    state["conversation_history"].append({
        "phase": 3,
        "screen": screen["name"],
        "ascii_ui": modified_ascii,
        "version": version,
        "modification": feedback
    })
    
    # 피드백 초기화
    state["user_feedback"] = None
    
    return state

def should_refine_or_continue(state: DesignAgentState) -> str:
    """
    다음 단계 결정
    """
    feedback = state.get("user_feedback", "")
    
    if not feedback:
        return "refine"  # 피드백 대기
    
    # 승인 키워드
    approval_keywords = ["확정", "좋아", "완벽", "ok", "다음", "넘어가"]
    if any(kw in feedback.lower() for kw in approval_keywords):
        # 현재 화면 승인
        current_idx = state["current_screen_index"]
        state["screens"][current_idx]["approved"] = True
        state["screens"][current_idx]["final_ascii"] = state["current_ascii_ui"]
        
        # 다음 화면으로
        if current_idx + 1 < len(state["screens"]):
            state["current_screen_index"] += 1
            state["user_feedback"] = None
            return "next_screen"
        else:
            # 모든 화면 완료
            return "done"
    else:
        # 수정 요청
        return "refine"
```

### Phase 4: Design System 구축 및 문서 생성

```python
async def build_design_system_node(state: DesignAgentState) -> DesignAgentState:
    """
    확정된 화면들로부터 Design System 추출
    """
    state["current_phase"] = 4
    
    approved_screens = [s for s in state["screens"] if s["approved"]]
    
    # 1. 공통 컴포넌트 추출
    components = extract_common_components(approved_screens)
    
    # 2. 색상 팔레트 추출
    colors = extract_color_palette(approved_screens)
    
    # 3. 타이포그래피 시스템
    typography = extract_typography(approved_screens)
    
    # 4. Spacing 시스템 (8pt grid)
    spacing = {"base": 8, "scale": [4, 8, 12, 16, 24, 32, 48, 64]}
    
    # 5. Border Radius
    border_radius = {"sm": 4, "md": 8, "lg": 12, "xl": 16}
    
    # 6. Shadow/Elevation
    shadows = {
        "sm": "0 1px 2px rgba(0,0,0,0.05)",
        "md": "0 4px 6px rgba(0,0,0,0.1)",
        "lg": "0 10px 15px rgba(0,0,0,0.1)",
        "xl": "0 20px 25px rgba(0,0,0,0.15)"
    }
    
    design_system = {
        "colors": colors,
        "typography": typography,
        "spacing": spacing,
        "border_radius": border_radius,
        "shadows": shadows,
        "components": components
    }
    
    # 접근성 검증
    accessibility = await validate_accessibility(
        approved_screens,
        design_system
    )
    
    # 반응형 스펙
    responsive = await define_responsive_specs(approved_screens)
    
    state["design_system"] = design_system
    state["component_library"] = components
    state["accessibility_checks"] = accessibility
    state["responsive_specs"] = responsive
    
    return state

async def generate_documents_node(state: DesignAgentState) -> DesignAgentState:
    """
    5개 최종 문서 생성
    """
    
    # 병렬 생성
    tasks = [
        generate_design_system_doc(state),
        generate_ux_flow_doc(state),
        generate_screen_specs_doc(state),
        generate_ai_studio_prompts(state),
        generate_design_guidelines_doc(state)
    ]
    
    docs = await asyncio.gather(*tasks)
    
    state["documents"] = {
        "design_system": docs[0],
        "ux_flow": docs[1],
        "screen_specs": docs[2],
        "ai_studio_prompts": docs[3],
        "design_guidelines": docs[4]
    }
    
    state["status"] = "completed"
    
    return state
```

---

## 5. 대화형 ASCII UI 시스템

### 5.1 ASCII UI 생성 규칙

```python
class ASCIIUIGenerator:
    """ASCII UI 생성 엔진"""
    
    RULES = {
        "mobile_width": 40,
        "web_width": 80,
        "box_chars": "┌─┐│└┘",
        "button_format": "[Button Text]",
        "input_format": "[_________________]",
        "icons": {
            "home": "🏠",
            "user": "👤",
            "settings": "⚙️",
            "search": "🔍",
            "notification": "🔔"
        }
    }
    
    async def generate(
        self,
        screen: Dict,
        layout_option: Dict,
        prd_context: str
    ) -> str:
        """
        화면 정보와 레이아웃 옵션으로 ASCII UI 생성
        """
        
        # 1. 레이아웃 구조 결정
        if layout_option["type"] == "card-grid":
            return self._generate_card_grid(screen)
        elif layout_option["type"] == "list":
            return self._generate_list(screen)
        elif layout_option["type"] == "split-pane":
            return self._generate_split_pane(screen)
        elif layout_option["type"] == "form":
            return self._generate_form(screen)
    
    def _generate_card_grid(self, screen: Dict) -> str:
        """카드 그리드 레이아웃"""
        
        width = self.RULES["mobile_width"]
        
        ui = f"""
┌{'─' * (width-2)}┐
│ {screen['name']:<{width-4}} │
├{'─' * (width-2)}┤
│                                      │
│  ┌──────┐ ┌──────┐ ┌──────┐        │
│  │      │ │      │ │      │        │
│  │ Card │ │ Card │ │ Card │        │
│  │      │ │      │ │      │        │
│  └──────┘ └──────┘ └──────┘        │
│                                      │
│  ┌──────┐ ┌──────┐ ┌──────┐        │
│  │      │ │      │ │      │        │
│  │ Card │ │ Card │ │ Card │        │
│  │      │ │      │ │      │        │
│  └──────┘ └──────┘ └──────┘        │
│                                      │
└{'─' * (width-2)}┘
        """
        
        return ui.strip()
    
    def _generate_form(self, screen: Dict) -> str:
        """폼 레이아웃"""
        
        elements = screen["key_elements"]
        
        ui = f"""
┌────────────────────────────────────┐
│ {screen['name']:<34} │
├────────────────────────────────────┤
│                                    │
"""
        
        for element in elements:
            if element["type"] == "input":
                ui += f"│  {element['label']:<32}  │\n"
                ui += f"│  [{'_' * 30}]  │\n"
                ui += "│                                    │\n"
            elif element["type"] == "button":
                ui += f"│  [{element['label']:^30}]  │\n"
                ui += "│                                    │\n"
        
        ui += "└────────────────────────────────────┘"
        
        return ui

async def modify_ascii_ui(
    current_ui: str,
    user_request: str,
    screen: Dict
) -> str:
    """
    사용자 요청에 따라 ASCII UI 수정
    """
    
    prompt = f"""
현재 ASCII UI:
{current_ui}

사용자 수정 요청: {user_request}

화면 정보:
{json.dumps(screen, ensure_ascii=False)}

사용자 요청을 정확히 반영하여 ASCII UI를 수정하세요.

규칙:
- 모바일: 가로 40자
- 웹: 가로 80자
- 박스: ┌─┐│└┘
- 버튼: [Button]
- 입력: [_________]
- 아이콘: 이모지
    """
    
    response = await llm.ainvoke(prompt)
    return response.content
```

### 5.2 피드백 처리 예제

```python
# 예제 1: 버튼 위치 변경
user: "로그인 버튼을 하단으로 옮겨줘"

current:
┌────────────────────────────────────┐
│  이메일                            │
│  [_____________________________]   │
│                                    │
│  [       로그인       ]            │
└────────────────────────────────────┘

modified:
┌────────────────────────────────────┐
│  이메일                            │
│  [_____________________________]   │
│                                    │
│                                    │
│  [       로그인       ]            │
└────────────────────────────────────┘

# 예제 2: 색상 밝게
user: "배경 색상을 더 밝게 해줘"

→ Design System의 color palette 조정
→ ASCII에는 표현 안 되지만 문서에 기록

# 예제 3: 요소 추가
user: "비밀번호 찾기 링크를 추가해줘"

modified:
┌────────────────────────────────────┐
│  이메일                            │
│  [_____________________________]   │
│                                    │
│  [       로그인       ]            │
│                                    │
│  비밀번호를 잊으셨나요?            │
└────────────────────────────────────┘
```

---

## 5.5 오픈소스 검색 및 추천 시스템 ⭐ 신규

### 5.5.1 개요

대화 중 사용자의 요구사항에 맞는 **오픈소스 라이브러리, 컴포넌트, 도구를 실시간으로 검색**하여 제안하고, 사용자 승인 시 문서에 자동 추가하는 시스템입니다.

**핵심 가치:**
- ✅ 검증된 오픈소스 솔루션으로 개발 시간 단축
- ✅ 최신 트렌드 반영 (2025년 기준 인기 라이브러리)
- ✅ 프로젝트 기술 스택과 호환되는 솔루션만 제안
- ✅ 라이선스, 보안, 성능 검증된 라이브러리

### 5.5.2 검색 트리거 시나리오

```python
# 사용자 메시지에서 키워드 감지
trigger_keywords = {
    "인증": ["login", "social login", "OAuth", "JWT"],
    "UI 컴포넌트": ["button", "modal", "dropdown", "table"],
    "폼": ["form", "validation", "input"],
    "아이콘": ["icon", "svg"],
    "애니메이션": ["animation", "transition", "motion"],
    "차트": ["chart", "graph", "visualization"],
    "날짜": ["date picker", "calendar", "time"]
}

# 예시 대화
사용자: "로그인 화면에 Google과 GitHub 소셜 로그인을 추가해줘"
        ↓
검색 트리거: "social login", "OAuth", "authentication"
        ↓
검색 쿼리 생성:
  - "React social login library 2025"
  - "OAuth authentication component TypeScript"
  - "next-auth alternative"
        ↓
검색 실행 (GitHub + npm + 웹)
        ↓
필터링 (라이선스, 최신성, Stars, TypeScript 지원)
        ↓
랭킹 (인기도 + 품질 + 호환성)
        ↓
상위 3개 제안
```

### 5.5.3 실시간 검색 프로세스

```python
async def search_and_suggest_open_source(
    state: DesignAgentState,
    user_message: str
) -> DesignAgentState:
    """
    사용자 메시지 분석 → 오픈소스 검색 → 제안
    """
    # 1. 키워드 추출
    keywords = extract_keywords(user_message)

    if not needs_open_source_search(keywords):
        return state

    # 2. 검색 쿼리 생성
    tech_stack = state["project_tech_stack"]  # React, TypeScript 등
    queries = generate_search_queries(keywords, tech_stack)

    # 3. 멀티소스 검색
    results = []
    for query in queries:
        # GitHub API
        github_repos = await search_github(
            query=query,
            language=tech_stack["language"],
            min_stars=500,
            max_results=5
        )

        # npm registry
        npm_packages = await search_npm(
            query=query,
            keywords=tech_stack["frameworks"]
        )

        # 웹 검색 (최신 트렌드)
        web_articles = await search_web(
            query=f"{query} best library 2025"
        )

        results.extend(github_repos + npm_packages)

    # 4. 필터링
    filtered = filter_by_criteria(results, {
        "license": ["MIT", "Apache-2.0", "ISC"],
        "last_update_months": 6,
        "min_stars": 1000,
        "has_typescript": True,
        "no_security_issues": True
    })

    # 5. 랭킹 (점수 계산)
    ranked = rank_libraries(filtered)
    top_3 = ranked[:3]

    # 6. 사용자에게 제안
    suggestion_message = format_suggestion(top_3, keywords)

    state["open_source_suggestions"] = {
        "keywords": keywords,
        "options": top_3,
        "timestamp": datetime.now().isoformat()
    }

    # 사용자에게 표시
    print(suggestion_message)

    return state
```

### 5.5.4 제안 형식

```
사용자: "데이터 테이블이 필요해요. 정렬, 필터링, 페이지네이션 기능도요."

에이전트:
┌──────────────────────────────────────────────────────┐
│ 🔍 오픈소스 라이브러리 검색 중...                   │
│ 키워드: data table, sorting, filtering, pagination   │
└──────────────────────────────────────────────────────┘

✅ 3가지 옵션을 찾았습니다:

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1. TanStack Table v8 ⭐ 추천
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
   📦 GitHub: tanstack/table
   ⭐ Stars: 22,000+
   📄 License: MIT
   📏 Bundle: 15KB (gzipped)
   📅 Updated: 1주 전

   ✨ 특징:
   - 헤드리스 UI (Tailwind 완벽 커스터마이징)
   - 정렬, 필터, 페이지네이션, 가상화 모두 지원
   - TypeScript 네이티브
   - React 19 지원

   💡 추천 이유: 프로젝트의 Tailwind CSS와 완벽히 호환

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
2. AG Grid Community
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
   📦 GitHub: ag-grid/ag-grid
   ⭐ Stars: 11,000+
   📄 License: MIT (Community), Commercial (Enterprise)
   📏 Bundle: 120KB (무거움)
   📅 Updated: 3일 전

   ✨ 특징:
   - 엔터프라이즈급 기능 (Excel export, 그룹화 등)
   - 매우 강력하지만 번들 크기 큼

   ⚠️ 주의: Pro 기능은 유료 라이선스 필요

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
3. React Table v7 (Legacy)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
   ⭐ Stars: 9,000+
   📏 Bundle: 12KB
   ⚠️ Updated: 8개월 전 (현재는 TanStack Table로 이전)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🤔 어떤 라이브러리를 사용하시겠습니까?
   입력: 1, 2, 3, 또는 "skip" (건너뛰기)

사용자: "1번으로 할게요"

에이전트:
✅ TanStack Table v8를 선택하셨습니다!

📝 다음 문서에 추가되었습니다:
   • Open_Source_Recommendations_v0.9.md
   • Design_System_v0.9.md (데이터 테이블 섹션)
   • Screen_Specifications_v0.9.md (관리자 화면)

📦 설치 명령어:
   npm install @tanstack/react-table

[ASCII UI 업데이트하여 표시]
```

### 5.5.5 검색 카테고리

**UI 컴포넌트**
- shadcn/ui, Radix UI, Headless UI, Chakra UI, Material-UI

**인증/권한**
- next-auth, Auth.js, Supabase Auth, Clerk

**폼 관리**
- React Hook Form, Formik, TanStack Form, Zod (validation)

**아이콘**
- Lucide Icons, Heroicons, Phosphor Icons, Tabler Icons

**애니메이션**
- Framer Motion, React Spring, GSAP, Auto Animate

**데이터 시각화**
- Recharts, Victory, Chart.js, D3.js

**날짜/시간**
- date-fns, Day.js, React DayPicker

**상태 관리**
- Zustand, Jotai, Redux Toolkit, TanStack Query

### 5.5.6 필터링 및 랭킹 알고리즘

```python
def rank_open_source_library(lib: Dict) -> float:
    """
    오픈소스 라이브러리 점수 계산 (0-100점)
    """
    score = 0

    # 1. 인기도 (40점)
    score += min(lib.github_stars / 1000, 20)  # Max 20
    score += min(lib.npm_weekly_downloads / 10000, 20)  # Max 20

    # 2. 최신성 (20점)
    months_ago = lib.last_update_months
    if months_ago < 3:
        score += 20
    elif months_ago < 6:
        score += 15
    elif months_ago < 12:
        score += 10

    # 3. 품질 (20점)
    if lib.has_typescript:
        score += 10
    if lib.test_coverage > 80:
        score += 5
    if lib.has_docs:
        score += 5

    # 4. 기술 스택 호환성 (20점)
    if lib.supports_react_19:
        score += 5
    if lib.supports_tailwind:
        score += 5
    if lib.tree_shakeable:
        score += 5
    if lib.bundle_size < 50:  # KB
        score += 5

    return score

# 필터링 기준
FILTER_CRITERIA = {
    "licenses": ["MIT", "Apache-2.0", "ISC"],
    "max_last_update_months": 12,
    "min_github_stars": 500,
    "no_security_vulnerabilities": True,
    "max_bundle_size_kb": 200
}
```

### 5.5.7 문서 통합

선택된 오픈소스는 다음 문서에 자동 추가:

**1. Open_Source_Recommendations_v0.9.md** (신규 문서)
```markdown
# 오픈소스 추천 목록

## UI 컴포넌트
### shadcn/ui ⭐ 선택됨
- GitHub: https://github.com/shadcn-ui/ui
- Stars: 85,000+
- License: MIT
- 선택 이유: Tailwind 기반, 완전한 커스터마이징, 접근성 우수

## 인증 시스템
### next-auth v5 ⭐ 선택됨
- GitHub: https://github.com/nextauthjs/next-auth
- Stars: 18,500+
- License: ISC
- 선택 이유: Next.js 완벽 통합, 40+ OAuth 제공자

[...모든 선택된 라이브러리 상세 정보...]
```

**2. Design_System_v0.9.md에 섹션 추가**
```markdown
## 오픈소스 컴포넌트 라이브러리
- UI: shadcn/ui v0.8.0
- Icons: Lucide Icons v0.300
- Forms: React Hook Form v7.49 + Zod v3.22
```

**3. Screen_Specifications_v0.9.md에 구현 라이브러리 명시**
```markdown
### 로그인 화면 구현 스택
- Authentication: next-auth v5
- Form: React Hook Form + Zod
- UI: shadcn/ui (Button, Input, Card)
```

### 5.5.8 LangGraph 노드 추가

```python
# 새로운 노드: open_source_search
def should_search_open_source(state: DesignAgentState) -> bool:
    """
    오픈소스 검색이 필요한지 판단
    """
    msg = state["user_feedback"].lower()

    search_triggers = [
        "라이브러리", "library", "컴포넌트", "component",
        "아이콘", "icon", "인증", "auth", "login",
        "차트", "chart", "테이블", "table", "폼", "form"
    ]

    return any(trigger in msg for trigger in search_triggers)

# Conditional Edge 추가
graph.add_conditional_edges(
    "refine_design",
    lambda state: "search_open_source" if should_search_open_source(state) else "next_action",
    {
        "search_open_source": "open_source_search_node",
        "next_action": "check_approval"
    }
)
```

### 5.5.9 사용자 경험 개선

**비침투적 제안**
- 대화 흐름을 방해하지 않음
- "skip" 옵션 항상 제공
- 제안은 선택사항, 강요 없음

**맥락 인식**
- 이전 대화 기록 분석
- 프로젝트 기술 스택 고려
- 이미 선택된 라이브러리와 호환성 체크

**학습 및 개선**
- 사용자 선택 패턴 기록
- 자주 선택되는 라이브러리 우선순위 상향
- 거부된 제안은 향후 제안 시 제외

---

## 6. 문서 생성

### 6.1 Design System Document

```python
async def generate_design_system_doc(state: DesignAgentState) -> str:
    """
    Design_System_v0.9.md 생성
    """
    
    ds = state["design_system"]
    
    doc = f"""
# Design System

Project: {state['project_name']}
Generated: {datetime.now().strftime("%Y-%m-%d")}

---

## 1. Color Palette

### Primary Colors
{format_colors(ds['colors']['primary'])}

### Secondary Colors
{format_colors(ds['colors']['secondary'])}

### Neutral Colors
{format_colors(ds['colors']['neutral'])}

### Semantic Colors
{format_colors(ds['colors']['semantic'])}

---

## 2. Typography System

### Font Family
- Primary: {ds['typography']['primary_font']}
- Secondary: {ds['typography']['secondary_font']}

### Font Sizes
{format_font_sizes(ds['typography']['sizes'])}

### Line Heights
{format_line_heights(ds['typography']['line_heights'])}

---

## 3. Spacing System

**Base Unit:** {ds['spacing']['base']}px (8pt grid)

**Scale:**
{format_spacing_scale(ds['spacing']['scale'])}

---

## 4. Border Radius

{format_border_radius(ds['border_radius'])}

---

## 5. Shadow & Elevation

{format_shadows(ds['shadows'])}

---

## 6. Icon Style Guide

- Style: {ds.get('icon_style', 'Outlined')}
- Size: 24x24px (default)
- Color: Inherit from context

---

## 7. Component Library

{format_components(ds['components'])}

---

## 8. Usage Guidelines

### Color Usage
- Primary: Main actions, key UI elements
- Secondary: Supporting actions
- Neutral: Backgrounds, borders, dividers
- Semantic: Error, Warning, Success, Info states

### Typography Hierarchy
- H1: Page titles
- H2: Section headers
- H3: Subsection headers
- Body: Regular content
- Caption: Helper text, timestamps

### Spacing Application
- Use multiples of 8px for consistency
- Component padding: 16px (2x base)
- Section gaps: 32px (4x base)
- Element spacing: 8px (1x base)
    """
    
    return doc
```

### 6.2 UX Flow Document

```python
async def generate_ux_flow_doc(state: DesignAgentState) -> str:
    """
    UX_Flow_v0.9.md 생성
    """
    
    screens = state["screens"]
    prd = state["prd_content"]
    
    doc = f"""
# UX Flow Document

Project: {state['project_name']}

---

## 1. Screen Sitemap

```
{generate_sitemap(screens)}
```

---

## 2. Screen Navigation Flow

{generate_navigation_flow(screens, prd)}

---

## 3. User Actions & System Responses

{generate_action_response_matrix(screens)}

---

## 4. Edge Cases

### Loading States
{generate_loading_states(screens)}

### Error States
{generate_error_states(screens)}

### Empty States
{generate_empty_states(screens)}

### Offline Mode
{generate_offline_behavior(screens)}

---

## 5. Key User Flows

{extract_key_flows_from_prd(prd, screens)}
    """
    
    return doc
```

### 6.3 Screen Specifications Document

```python
async def generate_screen_specs_doc(state: DesignAgentState) -> str:
    """
    Screen_Specifications_v0.9.md 생성
    """
    
    doc = f"""
# Screen Specifications

Project: {state['project_name']}

---

"""
    
    for screen in state["screens"]:
        if not screen["approved"]:
            continue
        
        doc += f"""
## {screen['name']}

### ASCII UI (Final Version)

```
{screen['final_ascii']}
```

### Layout Structure

{describe_layout_structure(screen)}

### Element Details

{format_element_details(screen)}

### Interaction Specifications

{format_interactions(screen)}

### State Variations

{format_state_variations(screen)}

### Design Decisions

{get_decisions_for_screen(screen['name'], state['decisions'])}

---

"""
    
    return doc
```

### 6.4 Google AI Studio Prompts

```python
async def generate_ai_studio_prompts(state: DesignAgentState) -> str:
    """
    Google_AI_Studio_Prompts_v0.9.md 생성
    """
    
    doc = f"""
# Google AI Studio Prompts

Project: {state['project_name']}

각 화면을 Google AI Studio에서 생성하기 위한 프롬프트입니다.

---

"""
    
    for screen in state["screens"]:
        if not screen["approved"]:
            continue
        
        prompt = await generate_ai_prompt_for_screen(
            screen,
            state["design_system"]
        )
        
        doc += f"""
## {screen['name']}

### Prompt

```
{prompt}
```

### Expected Output
- Image dimensions: 1920x1080 (desktop) or 375x812 (mobile)
- Format: PNG with transparency
- Style: {state['design_system'].get('visual_style', 'Modern, clean')}

---

"""
    
    return doc

async def generate_ai_prompt_for_screen(
    screen: Dict,
    design_system: Dict
) -> str:
    """화면별 AI 이미지 생성 프롬프트"""
    
    prompt = f"""
Create a high-fidelity UI mockup for a {screen['name']} screen with the following specifications:

**Layout:**
{describe_layout_from_ascii(screen['final_ascii'])}

**Visual Style:**
- Design aesthetic: Modern, clean, minimalist
- Color scheme: 
  Primary: {design_system['colors']['primary']}
  Secondary: {design_system['colors']['secondary']}
- Typography: {design_system['typography']['primary_font']}
- Spacing: 8px grid system

**Key Elements:**
{format_key_elements_for_prompt(screen['key_elements'])}

**Visual Requirements:**
- High contrast for readability
- WCAG AA compliance
- Clear visual hierarchy
- Consistent with provided color palette
- Professional, production-ready quality

**Format:**
- Resolution: 1920x1080 (desktop) or 375x812 (mobile)
- File type: PNG with transparency
- Artboard: Include subtle drop shadow for presentation
    """
    
    return prompt
```

### 6.5 Design Guidelines Document

```python
async def generate_design_guidelines_doc(state: DesignAgentState) -> str:
    """
    Design_Guidelines_v0.9.md 생성
    """
    
    doc = f"""
# Design Guidelines

Project: {state['project_name']}

---

## 1. Design Philosophy

{extract_design_philosophy(state)}

---

## 2. Accessibility Standards

### WCAG AA Compliance

**Color Contrast:**
- Normal text: Minimum 4.5:1
- Large text: Minimum 3:1
- UI components: Minimum 3:1

**Keyboard Navigation:**
- All interactive elements must be keyboard accessible
- Focus indicators must be visible
- Logical tab order

**Screen Reader Support:**
- Semantic HTML
- ARIA labels where needed
- Alt text for images

{format_accessibility_checks(state['accessibility_checks'])}

---

## 3. Responsive Principles

{format_responsive_specs(state['responsive_specs'])}

---

## 4. Animation Guidelines

**Duration:**
- Micro-interactions: 150-300ms
- Transitions: 300-500ms
- Complex animations: 500-800ms

**Easing:**
- Default: cubic-bezier(0.4, 0.0, 0.2, 1)
- Emphasis: cubic-bezier(0.0, 0.0, 0.2, 1)
- Decelerate: cubic-bezier(0.0, 0.0, 0.2, 1)

---

## 5. Dark Mode Policy

{determine_dark_mode_policy(state)}

---

## 6. Component Usage Rules

{format_component_usage_rules(state['component_library'])}

---

## 7. Do's and Don'ts

{generate_dos_and_donts(state)}
    """
    
    return doc
```

---

## 7. ANYON 통합

### 7.1 칸반보드 연동

```python
class DesignAgentKanbanIntegration:
    """ANYON 칸반보드 통합"""
    
    def __init__(self, kanban_api_url: str):
        self.api_url = kanban_api_url
    
    async def run_with_kanban(
        self,
        graph: DesignAgentGraph,
        project_id: str,
        prd: str,
        trd: str
    ):
        """칸반보드와 통합된 실행"""
        
        # 1. 디자인 티켓 생성
        ticket_id = await self.create_design_ticket(project_id, prd, trd)
        
        # 2. 초기 상태
        initial_state = {
            "project_id": project_id,
            "prd_content": prd,
            "trd_content": trd,
            "screens": [],
            "design_options": [],
            "selected_options": {},
            "conversation_history": [],
            "decisions": [],
            "current_screen_index": 0,
            "current_phase": 1,
            "status": "in_progress",
            "created_at": datetime.now()
        }
        
        # 3. 그래프 실행 (스트리밍)
        async for event in graph.compiled_graph.astream(initial_state):
            node_name = list(event.keys())[0]
            state = event[node_name]
            
            # 진행률 업데이트
            progress = self._calculate_progress(node_name, state)
            await self.update_ticket_progress(
                ticket_id,
                progress,
                f"Phase {state['current_phase']}: {node_name}"
            )
        
        # 4. 완료 처리
        await self.complete_ticket(ticket_id, state["documents"])
        
        return state
    
    def _calculate_progress(self, node_name: str, state: Dict) -> int:
        """노드별 진행률 계산"""
        
        progress_map = {
            "extract_screens": 10,
            "generate_options": 30,
            "create_ascii_ui": 50,
            "refine_design": 60,
            "build_design_system": 80,
            "generate_documents": 95
        }
        
        base_progress = progress_map.get(node_name, 0)
        
        # 화면별 진행률 추가
        if node_name in ["create_ascii_ui", "refine_design"]:
            total_screens = len(state["screens"])
            current_screen = state["current_screen_index"]
            screen_progress = (current_screen / total_screens) * 40
            return base_progress + int(screen_progress)
        
        return base_progress
```

### 7.2 WebSocket 실시간 업데이트

```python
class DesignAgentWebSocket:
    """WebSocket을 통한 실시간 UI 업데이트"""
    
    def __init__(self, websocket):
        self.ws = websocket
    
    async def send_ascii_ui(self, screen_name: str, ascii_ui: str, version: int):
        """ASCII UI를 클라이언트에 전송"""
        
        await self.ws.send_json({
            "type": "ascii_ui_update",
            "data": {
                "screen": screen_name,
                "ascii_ui": ascii_ui,
                "version": version
            }
        })
    
    async def send_options(self, screen_name: str, options: List[Dict]):
        """디자인 옵션을 클라이언트에 전송"""
        
        await self.ws.send_json({
            "type": "design_options",
            "data": {
                "screen": screen_name,
                "options": options
            }
        })
    
    async def receive_feedback(self) -> str:
        """사용자 피드백 수신"""
        
        message = await self.ws.receive_json()
        return message.get("feedback", "")
    
    async def send_progress(self, progress: int, message: str):
        """진행률 업데이트"""
        
        await self.ws.send_json({
            "type": "progress",
            "data": {
                "progress": progress,
                "message": message
            }
        })
```

---

## 8. 구현 예제

### 8.1 CLI 실행

```python
# cli.py

async def main():
    print("""
┌────────────────────────────────────┐
│  🎨 ANYON Design Agent            │
│     (ASCII UI Collaboration)      │
└────────────────────────────────────┘
    """)
    
    # PRD/TRD 로드
    prd_path = input("\nPRD 파일 경로: ")
    trd_path = input("TRD 파일 경로: ")
    
    prd = open(prd_path).read()
    trd = open(trd_path).read()
    
    project_name = input("프로젝트 이름: ")
    
    # 그래프 초기화
    graph = DesignAgentGraph()
    
    initial_state = {
        "project_id": "cli_session",
        "project_name": project_name,
        "prd_content": prd,
        "trd_content": trd,
        "screens": [],
        "design_options": [],
        "selected_options": {},
        "conversation_history": [],
        "decisions": [],
        "documents": {},
        "current_screen_index": 0,
        "current_phase": 1,
        "status": "in_progress"
    }
    
    # 실행
    async for event in graph.compiled_graph.astream(initial_state):
        node_name = list(event.keys())[0]
        state = event[node_name]
        
        # 대화 메시지 출력
        if state["conversation_history"]:
            last_message = state["conversation_history"][-1]
            if "message" in last_message:
                print(last_message["message"])
        
        # 사용자 입력 필요 시
        if node_name in ["generate_options", "create_ascii_ui", "refine_design"]:
            if state.get("user_feedback") is None:
                feedback = input("\n💬 입력: ")
                state["user_feedback"] = feedback
    
    # 결과 출력
    print("\n" + "="*50)
    print("✅ 디자인 완료!")
    print("="*50)
    print(f"\n생성된 문서:")
    for doc_name in state["documents"].keys():
        print(f"  ✓ {doc_name}")
    
    # 문서 저장
    output_dir = f"output/{project_name}/02_Design"
    os.makedirs(output_dir, exist_ok=True)
    
    for doc_name, content in state["documents"].items():
        filename = f"{doc_name}.md"
        filepath = os.path.join(output_dir, filename)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
    
    print(f"\n📁 문서 저장 완료: {output_dir}")

if __name__ == "__main__":
    asyncio.run(main())
```

### 8.2 API 서버

```python
# api.py

from fastapi import FastAPI, WebSocket

app = FastAPI()

@app.post("/api/design/start")
async def start_design(request: DesignRequest):
    """디자인 프로세스 시작"""
    
    graph = DesignAgentGraph()
    kanban = DesignAgentKanbanIntegration(settings.KANBAN_API_URL)
    
    # 비동기 실행
    final_state = await kanban.run_with_kanban(
        graph,
        request.project_id,
        request.prd,
        request.trd
    )
    
    return {
        "status": "completed",
        "documents": list(final_state["documents"].keys())
    }

@app.websocket("/ws/design/{project_id}")
async def websocket_endpoint(websocket: WebSocket, project_id: str):
    """실시간 디자인 협업"""
    
    await websocket.accept()
    ws_handler = DesignAgentWebSocket(websocket)
    
    # ... WebSocket 처리 로직
    
    await websocket.close()
```

---

## 9. 결론

### 9.1 핵심 요약

이 디자인 에이전트는:

✅ **명확한 역할 경계**
- 기획(PRD/TRD) → 디자인 → 개발
- 기획 영역 침범 없음
- 순수 디자인 작업에만 집중

✅ **BMAD 방법론 차용** (순수 디자인 부분만)
- Design Exploration (옵션 생성)
- Collaborative Iteration (대화형 수정)
- Decision Documentation (근거 기록)
- Quality Validation (검증)

✅ **간결한 구조**
- 4 Phases, 6 Nodes
- 명확한 입력/출력
- 복잡도 최소화

✅ **핵심 가치**
- ASCII UI 대화형 수정
- 비개발자 친화적
- 5개 문서 자동 생성
- ANYON 플랫폼 통합

### 9.2 구현 우선순위

**Week 1-2:** Core Structure
- LangGraph 기본 구조
- Phase 1-2 (화면 추출, 옵션 생성)
- ASCII UI 생성 로직

**Week 3-4:** Interactive Design ⭐
- Phase 3 (대화형 수정)
- 피드백 처리
- ASCII UI 수정 엔진

**Week 5:** Documentation
- Phase 4 (Design System)
- 5개 문서 생성

**Week 6:** Integration
- ANYON 칸반보드 연동
- WebSocket 실시간 업데이트

### 9.3 성공 지표

- ✅ 역할 경계 명확 (기획/디자인/개발)
- ✅ 5개 문서 자동 생성
- ✅ 비개발자가 쉽게 사용 가능
- ✅ 10회 이내 수정으로 화면 확정
- ✅ ANYON 플랫폼과 seamless 통합

**이제 기획 침범 없이, 순수하게 디자인 에이전트의 역할만 수행합니다.** 🎨