# ANYON 디자인 에이전트 제작 플랜 (LangGraph 기반)

## 📋 목차
1. [개요](#1-개요)
2. [시스템 아키텍처](#2-시스템-아키텍처)
3. [LangGraph 상태 머신 설계](#3-langgraph-상태-머신-설계)
4. [에이전트 구조 및 역할](#4-에이전트-구조-및-역할)
5. [대화형 ASCII UI 프로세스](#5-대화형-ascii-ui-프로세스)
6. [문서 생성 파이프라인](#6-문서-생성-파이프라인)
7. [ANYON 플랫폼 통합](#7-anyon-플랫폼-통합)
8. [기술 스택 및 구현 세부사항](#8-기술-스택-및-구현-세부사항)
9. [품질 검증 시스템](#9-품질-검증-시스템)
10. [배포 및 확장성](#10-배포-및-확장성)

---

## 1. 개요

### 1.1 목적
디자인 에이전트는 기획 에이전트가 생성한 PRD(Product Requirements Document)와 TRD(Technical Requirements Document)를 입력받아, 비개발자가 이해하기 쉬운 ASCII UI를 통해 대화형으로 디자인을 완성하고, 최종적으로 5가지 핵심 문서를 자동 생성하는 시스템입니다.

### 1.2 핵심 기능
- **입력**: 기획 에이전트의 PRD/TRD
- **프로세스**: ASCII UI 기반 대화형 디자인 반복
- **출력**: 5개 문서 자동 생성 + Google AI Studio 프롬프트

### 1.3 성공 지표
- 사용자 만족도: 디자인 대화 완료율 85% 이상
- 문서 품질: 자동 생성 문서 품질 점수 90/100 이상
- 효율성: 전통적 디자인 프로세스 대비 70% 시간 단축
- ANYON 통합: 칸반보드 티켓과 seamless 연동

---

## 2. 시스템 아키텍처

### 2.1 전체 구조

```
┌─────────────────────────────────────────────────────────────┐
│                    ANYON Platform Layer                      │
│  ┌──────────────────┐  ┌──────────────────┐                 │
│  │  Kanban Board UI │  │   Project State  │                 │
│  │   (Web Client)   │  │   Management     │                 │
│  └──────────────────┘  └──────────────────┘                 │
└─────────────────────────────────────────────────────────────┘
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                  Design Agent Layer                          │
│  ┌──────────────────────────────────────────────────────┐   │
│  │           LangGraph State Machine                    │   │
│  │  ┌──────┐   ┌──────┐   ┌──────┐   ┌──────┐         │   │
│  │  │ INIT │ → │DESIGN│ → │REVIEW│ → │ DONE │         │   │
│  │  └──────┘   └──────┘   └──────┘   └──────┘         │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │            Multi-Agent Orchestration                 │   │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐          │   │
│  │  │ ASCII UI │  │ Document │  │Validation│          │   │
│  │  │ Generator│  │ Generator│  │  Agent   │          │   │
│  │  └──────────┘  └──────────┘  └──────────┘          │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                     Data Layer                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   PRD/TRD    │  │  Design DB   │  │  Document    │      │
│  │   Storage    │  │   (State)    │  │   Storage    │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 데이터 플로우

```
기획 에이전트 PRD/TRD
         ▼
    [입력 검증]
         ▼
  [ASCII UI 초기 생성]
         ▼
    [사용자 대화]
         ▼
  [ASCII UI 반복 수정] ←───┐
         ▼                  │
    [사용자 승인?] ─NO──────┘
         │
        YES
         ▼
  [최종 UI 확정]
         ▼
  [5개 문서 병렬 생성]
         ▼
    [품질 검증]
         ▼
  [자동 개선 적용]
         ▼
  [ANYON 칸반보드 업데이트]
```

---

## 3. LangGraph 상태 머신 설계

### 3.1 State Schema

```python
from typing import TypedDict, List, Dict, Optional
from datetime import datetime

class DesignAgentState(TypedDict):
    # 입력 데이터
    project_id: str
    prd_content: str
    trd_content: str
    design_zip_url: Optional[str]  # 사용자 업로드 디자인 ZIP (선택)
    
    # 현재 단계
    current_phase: str  # "init", "design", "review", "validation", "done"
    
    # ASCII UI 관련
    screens: List[Dict]  # [{"name": "홈", "ascii_ui": "...", "version": 1}]
    current_screen_index: int
    modification_history: List[Dict]  # 수정 이력
    
    # 대화 상태
    conversation_history: List[Dict]  # [{"role": "user/assistant", "content": "..."}]
    user_feedback: Optional[str]
    
    # 문서 생성 상태
    design_system: Optional[Dict]
    ux_flow: Optional[Dict]
    screen_specs: List[Dict]
    ai_studio_prompts: List[str]
    design_guidelines: Optional[Dict]
    
    # 검증 결과
    validation_score: Optional[Dict]  # {"design_system": 96, "ux_flow": 93, ...}
    auto_improvements: List[str]
    
    # 메타데이터
    created_at: datetime
    updated_at: datetime
    status: str  # "in_progress", "completed", "failed"
    error_message: Optional[str]
```

### 3.2 Node 정의

```python
from langgraph.graph import StateGraph, END

class DesignAgentGraph:
    def __init__(self):
        self.graph = StateGraph(DesignAgentState)
        
        # Node 등록
        self.graph.add_node("initialize", self.initialize_node)
        self.graph.add_node("generate_ascii_ui", self.generate_ascii_ui_node)
        self.graph.add_node("process_feedback", self.process_feedback_node)
        self.graph.add_node("validate_design", self.validate_design_node)
        self.graph.add_node("generate_documents", self.generate_documents_node)
        self.graph.add_node("quality_check", self.quality_check_node)
        self.graph.add_node("auto_improve", self.auto_improve_node)
        self.graph.add_node("finalize", self.finalize_node)
        
        # Edge 설정
        self.graph.set_entry_point("initialize")
        
        self.graph.add_edge("initialize", "generate_ascii_ui")
        
        # 조건부 라우팅
        self.graph.add_conditional_edges(
            "generate_ascii_ui",
            self.should_continue_design,
            {
                "continue": "process_feedback",
                "validate": "validate_design"
            }
        )
        
        self.graph.add_edge("process_feedback", "generate_ascii_ui")
        self.graph.add_edge("validate_design", "generate_documents")
        self.graph.add_edge("generate_documents", "quality_check")
        self.graph.add_edge("quality_check", "auto_improve")
        self.graph.add_edge("auto_improve", "finalize")
        self.graph.add_edge("finalize", END)
        
        self.compiled_graph = self.graph.compile()
```

### 3.3 Conditional Routing Logic

```python
def should_continue_design(self, state: DesignAgentState) -> str:
    """
    사용자 피드백에 따라 디자인 계속 또는 검증 단계로 이동
    """
    if state.get("user_feedback"):
        feedback = state["user_feedback"].lower()
        
        # 승인 키워드
        approval_keywords = ["확정", "완료", "좋아", "ok", "승인", "다음"]
        
        if any(keyword in feedback for keyword in approval_keywords):
            return "validate"
        else:
            return "continue"
    
    # 기본적으로 계속 디자인
    return "continue"
```

---

## 4. 에이전트 구조 및 역할

### 4.1 ASCII UI Generator Agent

**역할**: PRD/TRD를 기반으로 ASCII 아트 형태의 화면 목업 생성

```python
class ASCIIUIGeneratorAgent:
    def __init__(self, llm):
        self.llm = llm
        self.system_prompt = """
당신은 ASCII 아트 UI 디자이너입니다.
PRD와 TRD를 분석하여 각 화면을 ASCII 아트로 표현합니다.

규칙:
1. 모바일 화면은 가로 40자 이내
2. 웹 화면은 가로 80자 이내
3. 박스는 ┌─┐│└┘ 문자 사용
4. 버튼은 [Button] 형식
5. 입력은 [_________] 형식
6. 아이콘은 🏠 📱 ⚙️ 등 이모지 사용
        """
    
    async def generate(self, prd: str, trd: str, screen_name: str) -> str:
        """특정 화면의 ASCII UI 생성"""
        prompt = f"""
PRD:
{prd}

TRD:
{trd}

위 정보를 바탕으로 '{screen_name}' 화면의 ASCII UI를 생성하세요.
        """
        
        response = await self.llm.ainvoke(
            [{"role": "system", "content": self.system_prompt},
             {"role": "user", "content": prompt}]
        )
        
        return response.content
    
    async def modify(self, current_ui: str, user_request: str) -> str:
        """사용자 요청에 따라 ASCII UI 수정"""
        prompt = f"""
현재 UI:
{current_ui}

사용자 요청: {user_request}

위 요청을 반영하여 UI를 수정하세요.
        """
        
        response = await self.llm.ainvoke(
            [{"role": "system", "content": self.system_prompt},
             {"role": "user", "content": prompt}]
        )
        
        return response.content
```

### 4.2 Document Generator Agent

**역할**: 확정된 ASCII UI를 기반으로 5개 문서 자동 생성

```python
class DocumentGeneratorAgent:
    def __init__(self, llm):
        self.llm = llm
    
    async def generate_design_system(self, screens: List[Dict]) -> Dict:
        """Design System Document 생성"""
        prompt = f"""
확정된 화면들:
{json.dumps(screens, indent=2, ensure_ascii=False)}

다음을 포함하는 Design System을 생성하세요:
1. Color Palette (Primary, Secondary, Accent, Neutral, Semantic)
2. Typography System
3. Spacing System (4pt/8pt grid)
4. Border Radius System
5. Shadow/Elevation System
6. Icon Style Guide
7. Component Library Specification

JSON 형식으로 출력하세요.
        """
        
        response = await self.llm.ainvoke([
            {"role": "user", "content": prompt}
        ])
        
        return json.loads(response.content)
    
    async def generate_ux_flow(self, screens: List[Dict], prd: str) -> Dict:
        """UX Flow Document 생성"""
        prompt = f"""
PRD:
{prd}

확정된 화면들:
{json.dumps(screens, indent=2, ensure_ascii=False)}

다음을 포함하는 UX Flow를 생성하세요:
1. Screen Sitemap (화면 구조도)
2. Screen Navigation Flow (화면 간 이동)
3. User Action → System Response
4. Edge Cases (Loading, Error, Empty States, Offline)
5. 핵심 사용자 플로우 3-5개

JSON 형식으로 출력하세요.
        """
        
        response = await self.llm.ainvoke([
            {"role": "user", "content": prompt}
        ])
        
        return json.loads(response.content)
    
    async def generate_screen_spec(self, screen: Dict) -> Dict:
        """개별 화면 상세 스펙 생성"""
        prompt = f"""
화면 정보:
{json.dumps(screen, indent=2, ensure_ascii=False)}

다음을 포함하는 Screen Specification을 생성하세요:
1. Layout Structure
2. Element Details (크기, 여백, 색상)
3. Interaction Definitions
4. State Variations

JSON 형식으로 출력하세요.
        """
        
        response = await self.llm.ainvoke([
            {"role": "user", "content": prompt}
        ])
        
        return json.loads(response.content)
    
    async def generate_ai_studio_prompt(self, screen: Dict, design_system: Dict) -> str:
        """Google AI Studio 프롬프트 생성"""
        prompt = f"""
화면 정보:
{json.dumps(screen, indent=2, ensure_ascii=False)}

Design System:
{json.dumps(design_system, indent=2, ensure_ascii=False)}

Google AI Studio에서 이 화면을 생성하기 위한 상세한 프롬프트를 작성하세요.
프롬프트는 다음을 포함해야 합니다:
1. 전체 레이아웃 설명
2. 각 요소의 위치와 스타일
3. 색상 및 타이포그래피
4. 인터랙션 동작

명확하고 실행 가능한 프롬프트로 작성하세요.
        """
        
        response = await self.llm.ainvoke([
            {"role": "user", "content": prompt}
        ])
        
        return response.content
    
    async def generate_design_guidelines(self, design_system: Dict, ux_flow: Dict) -> Dict:
        """Design Guidelines Document 생성"""
        prompt = f"""
Design System:
{json.dumps(design_system, indent=2, ensure_ascii=False)}

UX Flow:
{json.dumps(ux_flow, indent=2, ensure_ascii=False)}

다음을 포함하는 Design Guidelines를 생성하세요:
1. Design Philosophy
2. Accessibility Standards (WCAG AA)
3. Responsive Principles
4. Animation Guidelines
5. Dark Mode Policy (if applicable)

JSON 형식으로 출력하세요.
        """
        
        response = await self.llm.ainvoke([
            {"role": "user", "content": prompt}
        ])
        
        return json.loads(response.content)
```

### 4.3 Validation Agent

**역할**: PRD와 디자인의 정합성, 일관성, 완결성 검증

```python
class ValidationAgent:
    def __init__(self, llm):
        self.llm = llm
    
    async def validate_prd_alignment(self, prd: str, screens: List[Dict]) -> Dict:
        """PRD와 디자인 화면 매칭 검증"""
        prompt = f"""
PRD:
{prd}

디자인된 화면들:
{json.dumps([s["name"] for s in screens], ensure_ascii=False)}

다음을 검증하세요:
1. PRD에 명시된 모든 화면이 디자인되었는지
2. 누락된 화면이 있는지
3. 추가로 필요한 화면이 있는지

JSON 형식으로 결과를 반환하세요:
{
  "missing_screens": [],
  "extra_screens": [],
  "suggested_screens": [],
  "alignment_score": 0-100
}
        """
        
        response = await self.llm.ainvoke([
            {"role": "user", "content": prompt}
        ])
        
        return json.loads(response.content)
    
    async def validate_design_consistency(self, design_system: Dict, screens: List[Dict]) -> Dict:
        """디자인 시스템 일관성 검증"""
        prompt = f"""
Design System:
{json.dumps(design_system, indent=2, ensure_ascii=False)}

화면들:
{json.dumps(screens, indent=2, ensure_ascii=False)}

다음을 검증하세요:
1. 모든 화면이 동일한 Color Palette 사용
2. Typography 일관성
3. Spacing System 준수
4. Component 재사용성

JSON 형식으로 결과를 반환하세요:
{
  "color_consistency": true/false,
  "typography_consistency": true/false,
  "spacing_consistency": true/false,
  "consistency_score": 0-100,
  "issues": []
}
        """
        
        response = await self.llm.ainvoke([
            {"role": "user", "content": prompt}
        ])
        
        return json.loads(response.content)
    
    async def validate_ux_completeness(self, ux_flow: Dict) -> Dict:
        """UX Flow 완결성 검증"""
        prompt = f"""
UX Flow:
{json.dumps(ux_flow, indent=2, ensure_ascii=False)}

다음을 검증하세요:
1. 막다른 화면 (dead-end) 없는지
2. 모든 CTA 버튼의 이동 경로가 정의되었는지
3. 뒤로가기/취소 경로 존재
4. Edge Cases 처리 완료

JSON 형식으로 결과를 반환하세요:
{
  "dead_ends": [],
  "missing_paths": [],
  "completeness_score": 0-100,
  "issues": []
}
        """
        
        response = await self.llm.ainvoke([
            {"role": "user", "content": prompt}
        ])
        
        return json.loads(response.content)
```

---

## 5. 대화형 ASCII UI 프로세스

### 5.1 초기 UI 생성 및 표시

```python
async def generate_ascii_ui_node(state: DesignAgentState) -> DesignAgentState:
    """
    LangGraph Node: ASCII UI 생성 및 사용자에게 표시
    """
    ascii_generator = ASCIIUIGeneratorAgent(llm)
    
    # PRD에서 화면 목록 추출
    if not state.get("screens"):
        # 최초 실행
        screens = extract_screens_from_prd(state["prd_content"])
        state["screens"] = []
        state["current_screen_index"] = 0
        
        # 첫 번째 화면 생성
        screen_name = screens[0]
        ascii_ui = await ascii_generator.generate(
            state["prd_content"],
            state["trd_content"],
            screen_name
        )
        
        state["screens"].append({
            "name": screen_name,
            "ascii_ui": ascii_ui,
            "version": 1,
            "approved": False
        })
    else:
        # 수정 요청 처리
        current_screen = state["screens"][state["current_screen_index"]]
        user_feedback = state.get("user_feedback", "")
        
        if user_feedback:
            # ASCII UI 수정
            modified_ui = await ascii_generator.modify(
                current_screen["ascii_ui"],
                user_feedback
            )
            
            # 버전 업데이트
            current_screen["ascii_ui"] = modified_ui
            current_screen["version"] += 1
            
            # 수정 이력 기록
            state["modification_history"].append({
                "screen": current_screen["name"],
                "version": current_screen["version"],
                "request": user_feedback,
                "timestamp": datetime.now().isoformat()
            })
    
    # 현재 화면 표시용 UI 텍스트 생성
    current_screen = state["screens"][state["current_screen_index"]]
    ui_display = f"""
┌────────────────────────────────────┐
│ 🎨 화면 디자인: {current_screen['name']:<20} │
│ 버전: v{current_screen['version']:<29} │
└────────────────────────────────────┘

{current_screen['ascii_ui']}

┌────────────────────────────────────┐
│ 💬 피드백을 입력하세요:            │
│ - 수정 요청: "버튼 위치 변경해줘"  │
│ - 승인: "좋아", "확정", "다음"     │
└────────────────────────────────────┘
    """
    
    state["current_ui_display"] = ui_display
    state["updated_at"] = datetime.now()
    
    return state
```

### 5.2 사용자 피드백 처리

```python
async def process_feedback_node(state: DesignAgentState) -> DesignAgentState:
    """
    LangGraph Node: 사용자 피드백 분석 및 처리
    """
    feedback = state.get("user_feedback", "")
    current_index = state["current_screen_index"]
    current_screen = state["screens"][current_index]
    
    # 대화 이력 업데이트
    state["conversation_history"].append({
        "role": "user",
        "content": feedback,
        "screen": current_screen["name"],
        "timestamp": datetime.now().isoformat()
    })
    
    # 피드백 분류
    feedback_lower = feedback.lower()
    
    # 승인 키워드 체크
    approval_keywords = ["확정", "완료", "좋아", "ok", "승인", "다음", "넘어가"]
    is_approved = any(kw in feedback_lower for kw in approval_keywords)
    
    if is_approved:
        current_screen["approved"] = True
        
        # 다음 화면으로 이동
        if current_index + 1 < len(state["screens"]):
            state["current_screen_index"] += 1
            state["user_feedback"] = None  # 다음 화면 생성 트리거
        else:
            # 모든 화면 완료
            state["current_phase"] = "validation"
            
        state["conversation_history"].append({
            "role": "assistant",
            "content": f"'{current_screen['name']}' 화면이 확정되었습니다. ✅",
            "timestamp": datetime.now().isoformat()
        })
    else:
        # 수정 요청 - ASCII UI 재생성 트리거
        state["conversation_history"].append({
            "role": "assistant",
            "content": "수정 사항을 반영하고 있습니다...",
            "timestamp": datetime.now().isoformat()
        })
    
    state["updated_at"] = datetime.now()
    return state
```

### 5.3 화면 전환 및 진행률 표시

```python
def display_progress(state: DesignAgentState) -> str:
    """현재 진행률 표시"""
    total_screens = len(state["screens"])
    approved_screens = sum(1 for s in state["screens"] if s.get("approved", False))
    progress_percent = (approved_screens / total_screens * 100) if total_screens > 0 else 0
    
    progress_bar = "█" * int(progress_percent / 5) + "░" * (20 - int(progress_percent / 5))
    
    return f"""
┌────────────────────────────────────┐
│ 📊 디자인 진행률                   │
│ [{progress_bar}] {progress_percent:.0f}%  │
│ {approved_screens}/{total_screens} 화면 완료                  │
└────────────────────────────────────┘
    """
```

---

## 6. 문서 생성 파이프라인

### 6.1 병렬 문서 생성 전략

```python
import asyncio

async def generate_documents_node(state: DesignAgentState) -> DesignAgentState:
    """
    LangGraph Node: 5개 문서 병렬 생성
    """
    doc_generator = DocumentGeneratorAgent(llm)
    screens = state["screens"]
    prd = state["prd_content"]
    
    # 병렬 실행
    tasks = [
        doc_generator.generate_design_system(screens),
        doc_generator.generate_ux_flow(screens, prd),
        doc_generator.generate_design_guidelines({}, {})  # 임시
    ]
    
    # Design System과 UX Flow 먼저 생성
    results = await asyncio.gather(*tasks)
    
    state["design_system"] = results[0]
    state["ux_flow"] = results[1]
    state["design_guidelines"] = results[2]
    
    # Screen Specs와 AI Studio Prompts 생성
    screen_spec_tasks = [
        doc_generator.generate_screen_spec(screen)
        for screen in screens
    ]
    
    ai_prompt_tasks = [
        doc_generator.generate_ai_studio_prompt(screen, state["design_system"])
        for screen in screens
    ]
    
    screen_specs = await asyncio.gather(*screen_spec_tasks)
    ai_prompts = await asyncio.gather(*ai_prompt_tasks)
    
    state["screen_specs"] = screen_specs
    state["ai_studio_prompts"] = ai_prompts
    
    # 최종 Design Guidelines 재생성 (Design System과 UX Flow 반영)
    state["design_guidelines"] = await doc_generator.generate_design_guidelines(
        state["design_system"],
        state["ux_flow"]
    )
    
    state["current_phase"] = "quality_check"
    state["updated_at"] = datetime.now()
    
    return state
```

### 6.2 문서 저장 형식

```python
async def save_documents(state: DesignAgentState, output_dir: str):
    """
    생성된 문서를 파일로 저장
    """
    project_id = state["project_id"]
    base_path = f"{output_dir}/{project_id}/02_Design"
    
    os.makedirs(base_path, exist_ok=True)
    
    # 1. Design System
    with open(f"{base_path}/Design_System_v0.9.md", "w", encoding="utf-8") as f:
        f.write(format_design_system_markdown(state["design_system"]))
    
    # 2. UX Flow
    with open(f"{base_path}/UX_Flow_v0.9.md", "w", encoding="utf-8") as f:
        f.write(format_ux_flow_markdown(state["ux_flow"]))
    
    # 3. Screen Specifications
    with open(f"{base_path}/Screen_Specifications_v0.9.md", "w", encoding="utf-8") as f:
        f.write(format_screen_specs_markdown(state["screen_specs"]))
    
    # 4. Google AI Studio Prompts
    with open(f"{base_path}/Google_AI_Studio_Prompts_v0.9.md", "w", encoding="utf-8") as f:
        f.write(format_ai_prompts_markdown(state["ai_studio_prompts"]))
    
    # 5. Design Guidelines
    with open(f"{base_path}/Design_Guidelines_v0.9.md", "w", encoding="utf-8") as f:
        f.write(format_guidelines_markdown(state["design_guidelines"]))
    
    print(f"✅ 문서 저장 완료: {base_path}")
```

---

## 7. ANYON 플랫폼 통합

### 7.1 칸반보드 티켓 연동

```python
class ANYONKanbanIntegration:
    """
    ANYON 칸반보드와의 통합 레이어
    """
    
    def __init__(self, kanban_api_url: str):
        self.api_url = kanban_api_url
    
    async def create_design_ticket(self, project_id: str, prd: str, trd: str) -> str:
        """
        디자인 티켓 생성
        
        Returns:
            ticket_id: 생성된 티켓 ID
        """
        ticket_data = {
            "project_id": project_id,
            "title": "🎨 디자인 단계",
            "type": "design",
            "status": "IN_PROGRESS",
            "assignee": "Design AI Agent",
            "description": "PRD/TRD 기반 디자인 생성 중",
            "metadata": {
                "prd_id": extract_prd_id(prd),
                "trd_id": extract_trd_id(trd)
            }
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.api_url}/tickets",
                json=ticket_data
            )
            return response.json()["ticket_id"]
    
    async def update_ticket_progress(self, ticket_id: str, progress: int, message: str):
        """티켓 진행률 업데이트"""
        async with httpx.AsyncClient() as client:
            await client.patch(
                f"{self.api_url}/tickets/{ticket_id}",
                json={
                    "progress": progress,
                    "status_message": message
                }
            )
    
    async def complete_ticket(self, ticket_id: str, documents: Dict):
        """티켓 완료 처리 및 문서 첨부"""
        async with httpx.AsyncClient() as client:
            await client.patch(
                f"{self.api_url}/tickets/{ticket_id}",
                json={
                    "status": "DONE",
                    "completed_at": datetime.now().isoformat(),
                    "attachments": {
                        "design_system": documents["design_system"],
                        "ux_flow": documents["ux_flow"],
                        "screen_specs": documents["screen_specs"],
                        "ai_studio_prompts": documents["ai_studio_prompts"],
                        "design_guidelines": documents["design_guidelines"]
                    }
                }
            )
    
    async def create_development_tickets(self, project_id: str, screen_specs: List[Dict]):
        """
        화면별 개발 티켓 자동 생성
        """
        tickets = []
        for spec in screen_specs:
            ticket_data = {
                "project_id": project_id,
                "title": f"⚙️ {spec['screen_name']} 화면 개발",
                "type": "development",
                "status": "PLAN",
                "assignee": "Developer AI Agent",
                "description": spec["description"],
                "metadata": {
                    "screen_spec": spec,
                    "dependencies": spec.get("dependencies", [])
                }
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.api_url}/tickets",
                    json=ticket_data
                )
                tickets.append(response.json()["ticket_id"])
        
        return tickets
```

### 7.2 실시간 상태 업데이트

```python
class DesignAgentWithKanbanIntegration:
    """
    칸반보드와 통합된 디자인 에이전트
    """
    
    def __init__(self, graph: DesignAgentGraph, kanban: ANYONKanbanIntegration):
        self.graph = graph
        self.kanban = kanban
    
    async def run(self, project_id: str, prd: str, trd: str):
        """
        디자인 프로세스 실행 (칸반 통합)
        """
        # 1. 티켓 생성
        ticket_id = await self.kanban.create_design_ticket(project_id, prd, trd)
        
        # 2. 초기 상태 설정
        initial_state = {
            "project_id": project_id,
            "prd_content": prd,
            "trd_content": trd,
            "current_phase": "init",
            "screens": [],
            "conversation_history": [],
            "modification_history": [],
            "created_at": datetime.now(),
            "status": "in_progress"
        }
        
        # 3. LangGraph 실행 (스트리밍)
        async for event in self.graph.compiled_graph.astream(initial_state):
            node_name = list(event.keys())[0]
            state = event[node_name]
            
            # 칸반보드 실시간 업데이트
            if node_name == "generate_ascii_ui":
                progress = (state["current_screen_index"] + 1) / len(state["screens"]) * 40
                await self.kanban.update_ticket_progress(
                    ticket_id,
                    int(progress),
                    f"화면 생성 중: {state['screens'][state['current_screen_index']]['name']}"
                )
            
            elif node_name == "generate_documents":
                await self.kanban.update_ticket_progress(
                    ticket_id,
                    70,
                    "문서 생성 중..."
                )
            
            elif node_name == "quality_check":
                await self.kanban.update_ticket_progress(
                    ticket_id,
                    90,
                    "품질 검증 중..."
                )
            
            elif node_name == "finalize":
                # 티켓 완료
                await self.kanban.complete_ticket(ticket_id, {
                    "design_system": state["design_system"],
                    "ux_flow": state["ux_flow"],
                    "screen_specs": state["screen_specs"],
                    "ai_studio_prompts": state["ai_studio_prompts"],
                    "design_guidelines": state["design_guidelines"]
                })
                
                # 개발 티켓 자동 생성
                await self.kanban.create_development_tickets(
                    project_id,
                    state["screen_specs"]
                )
        
        return state
```

### 7.3 WebSocket을 통한 실시간 UI 업데이트

```python
class DesignAgentWebSocketHandler:
    """
    웹소켓을 통한 실시간 사용자 인터페이스 업데이트
    """
    
    def __init__(self, websocket):
        self.ws = websocket
    
    async def send_ascii_ui(self, screen: Dict):
        """ASCII UI를 클라이언트에 전송"""
        await self.ws.send_json({
            "type": "ascii_ui_update",
            "data": {
                "screen_name": screen["name"],
                "ascii_ui": screen["ascii_ui"],
                "version": screen["version"]
            }
        })
    
    async def send_progress(self, progress: int, message: str):
        """진행률 업데이트 전송"""
        await self.ws.send_json({
            "type": "progress_update",
            "data": {
                "progress": progress,
                "message": message
            }
        })
    
    async def send_document_status(self, doc_name: str, status: str):
        """문서 생성 상태 전송"""
        await self.ws.send_json({
            "type": "document_status",
            "data": {
                "document": doc_name,
                "status": status  # "generating", "completed"
            }
        })
    
    async def receive_feedback(self) -> str:
        """사용자 피드백 수신"""
        message = await self.ws.receive_json()
        return message.get("feedback", "")
```

---

## 8. 기술 스택 및 구현 세부사항

### 8.1 핵심 기술 스택

```yaml
Backend:
  - Language: Python 3.11+ (Python 3.13 recommended)
  - Framework: FastAPI 0.121+ (async support)
  - Orchestration: LangGraph 1.0+
  - LLM: Anthropic Claude Sonnet 4.5 (claude-sonnet-4-5-20250929) / GPT-4
  - State Management: Redis (분산 상태 저장)
  - Task Queue: Celery (비동기 작업)

Frontend:
  - Framework: React 19+ (React 18.3.1 also supported)
  - UI Library: Tailwind CSS
  - Real-time: Socket.io Client
  - State: Zustand

Infrastructure:
  - Container: Docker
  - Orchestration: Kubernetes (선택)
  - Cloud: GCP / AWS
  - Database: PostgreSQL (프로젝트 메타데이터)
  - Storage: GCS / S3 (문서 저장)

Monitoring:
  - Logging: Loguru
  - Metrics: Prometheus + Grafana
  - Tracing: LangSmith (LangGraph 디버깅)
```

### 8.2 LangGraph 설정

```python
# langgraph_config.py

from langgraph.checkpoint import MemorySaver
from langgraph.checkpoint.postgres import PostgresSaver

class DesignAgentConfig:
    """LangGraph 설정"""
    
    @staticmethod
    def get_checkpointer(env: str):
        """환경별 체크포인터 설정"""
        if env == "development":
            return MemorySaver()
        else:
            # Production: PostgreSQL 기반 체크포인터
            return PostgresSaver.from_conn_string(
                os.getenv("POSTGRES_CONN_STRING")
            )
    
    @staticmethod
    def get_graph_config():
        """그래프 설정"""
        return {
            "recursion_limit": 100,  # 최대 반복 횟수
            "configurable": {
                "thread_id": "design_agent",  # 스레드 ID
            }
        }
```

### 8.3 에러 핸들링

```python
class DesignAgentException(Exception):
    """디자인 에이전트 기본 예외"""
    pass

class PRDValidationError(DesignAgentException):
    """PRD 검증 실패"""
    pass

class ASCIIGenerationError(DesignAgentException):
    """ASCII UI 생성 실패"""
    pass

class DocumentGenerationError(DesignAgentException):
    """문서 생성 실패"""
    pass

# 에러 핸들링 미들웨어
async def handle_errors(state: DesignAgentState) -> DesignAgentState:
    """
    LangGraph 에러 핸들링 래퍼
    """
    try:
        # 정상 처리
        return state
    except PRDValidationError as e:
        state["status"] = "failed"
        state["error_message"] = f"PRD 검증 실패: {str(e)}"
        # 사용자에게 알림
        await notify_user(state["project_id"], state["error_message"])
    except ASCIIGenerationError as e:
        state["status"] = "failed"
        state["error_message"] = f"UI 생성 실패: {str(e)}"
        # 재시도 로직
        if state.get("retry_count", 0) < 3:
            state["retry_count"] = state.get("retry_count", 0) + 1
            # 재생성 트리거
    except Exception as e:
        state["status"] = "failed"
        state["error_message"] = f"알 수 없는 오류: {str(e)}"
        # 로그 기록
        logger.error(f"Unexpected error in design agent: {e}")
    
    return state
```

---

## 8.5 오픈소스 검색 및 추천 시스템 구현 ⭐ 신규

### 8.5.1 아키텍처 개요

```python
┌─────────────────────────────────────────────────────┐
│           Open Source Search System                 │
├─────────────────────────────────────────────────────┤
│                                                     │
│  ┌──────────────────┐    ┌──────────────────┐     │
│  │  Keyword         │    │  Search Query    │     │
│  │  Extractor       │ →  │  Generator       │     │
│  └──────────────────┘    └──────────────────┘     │
│           │                       │                │
│           ↓                       ↓                │
│  ┌──────────────────────────────────────────┐     │
│  │      Multi-Source Searcher               │     │
│  ├──────────────────────────────────────────┤     │
│  │  • GitHub API                            │     │
│  │  • npm Registry API                      │     │
│  │  • Web Search (Google/Bing)              │     │
│  │  • Curated Lists (awesome-*)             │     │
│  └──────────────────────────────────────────┘     │
│           │                                        │
│           ↓                                        │
│  ┌──────────────────┐    ┌──────────────────┐    │
│  │  Filter Engine   │ →  │  Ranking Engine  │    │
│  └──────────────────┘    └──────────────────┘    │
│           │                       │               │
│           ↓                       ↓               │
│  ┌──────────────────────────────────────────┐    │
│  │      Recommendation Presenter            │    │
│  └──────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────┘
```

### 8.5.2 코어 컴포넌트 구현

**1. Keyword Extractor**

```python
# src/agents/open_source/keyword_extractor.py

from typing import List, Dict
from langchain.prompts import ChatPromptTemplate
from langchain_anthropic import ChatAnthropic

class KeywordExtractor:
    """사용자 메시지에서 오픈소스 관련 키워드 추출"""

    def __init__(self, llm: ChatAnthropic):
        self.llm = llm
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """
            사용자 메시지를 분석하여 오픈소스 검색에 필요한 키워드를 추출하세요.

            추출할 정보:
            1. 기능/컴포넌트 이름 (예: "social login", "data table", "chart")
            2. 카테고리 (예: "authentication", "ui-component", "visualization")
            3. 요구사항 (예: "sorting", "filtering", "responsive")

            JSON 형식으로 반환:
            {{
              "keywords": ["keyword1", "keyword2"],
              "category": "category_name",
              "requirements": ["req1", "req2"]
            }}
            """),
            ("user", "{user_message}")
        ])

    async def extract(self, user_message: str) -> Dict:
        """키워드 추출"""
        chain = self.prompt | self.llm
        response = await chain.ainvoke({"user_message": user_message})

        import json
        return json.loads(response.content)

# 사용 예시
extractor = KeywordExtractor(llm)
result = await extractor.extract("데이터 테이블이 필요해요. 정렬과 필터링 기능도요.")
# {
#   "keywords": ["data table", "table", "grid"],
#   "category": "ui-component",
#   "requirements": ["sorting", "filtering", "pagination"]
# }
```

**2. Multi-Source Searcher**

```python
# src/agents/open_source/searchers.py

import asyncio
import httpx
from typing import List, Dict, Optional
from datetime import datetime, timedelta

class GitHubSearcher:
    """GitHub API 기반 검색"""

    def __init__(self, token: str):
        self.token = token
        self.base_url = "https://api.github.com"

    async def search_repositories(
        self,
        query: str,
        language: Optional[str] = None,
        min_stars: int = 500
    ) -> List[Dict]:
        """GitHub 저장소 검색"""
        async with httpx.AsyncClient() as client:
            # 검색 쿼리 구성
            search_query = f"{query} stars:>{min_stars}"
            if language:
                search_query += f" language:{language}"

            headers = {
                "Authorization": f"token {self.token}",
                "Accept": "application/vnd.github.v3+json"
            }

            response = await client.get(
                f"{self.base_url}/search/repositories",
                params={
                    "q": search_query,
                    "sort": "stars",
                    "order": "desc",
                    "per_page": 10
                },
                headers=headers,
                timeout=10.0
            )

            if response.status_code != 200:
                return []

            data = response.json()
            repos = data.get("items", [])

            return [
                {
                    "source": "github",
                    "name": repo["name"],
                    "full_name": repo["full_name"],
                    "url": repo["html_url"],
                    "description": repo["description"],
                    "stars": repo["stargazers_count"],
                    "language": repo["language"],
                    "license": repo.get("license", {}).get("spdx_id"),
                    "last_updated": repo["updated_at"],
                    "topics": repo.get("topics", [])
                }
                for repo in repos
            ]

class NpmSearcher:
    """npm Registry 검색"""

    async def search_packages(self, query: str) -> List[Dict]:
        """npm 패키지 검색"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://registry.npmjs.org/-/v1/search",
                params={"text": query, "size": 10},
                timeout=10.0
            )

            if response.status_code != 200:
                return []

            data = response.json()
            packages = data.get("objects", [])

            results = []
            for pkg in packages:
                package_data = pkg["package"]

                # 추가 정보 가져오기 (번들 크기, TypeScript 지원)
                details = await self._get_package_details(
                    package_data["name"]
                )

                results.append({
                    "source": "npm",
                    "name": package_data["name"],
                    "description": package_data.get("description", ""),
                    "version": package_data["version"],
                    "npm_url": f"https://www.npmjs.com/package/{package_data['name']}",
                    "weekly_downloads": pkg.get("downloads", {}).get("weekly", 0),
                    "has_typescript": details.get("has_typescript", False),
                    "bundle_size": details.get("bundle_size", "Unknown"),
                    "keywords": package_data.get("keywords", [])
                })

            return results

    async def _get_package_details(self, package_name: str) -> Dict:
        """패키지 상세 정보 (TypeScript, 번들 크기)"""
        async with httpx.AsyncClient() as client:
            # npm package.json 가져오기
            response = await client.get(
                f"https://registry.npmjs.org/{package_name}",
                timeout=5.0
            )

            if response.status_code != 200:
                return {}

            data = response.json()
            latest = data.get("dist-tags", {}).get("latest", "")
            version_data = data.get("versions", {}).get(latest, {})

            # TypeScript 지원 확인
            has_typescript = (
                "typescript" in version_data.get("devDependencies", {}) or
                "@types" in str(version_data.get("dependencies", {}))
            )

            # 번들 크기 추정 (bundlephobia API 사용)
            bundle_size = await self._get_bundle_size(package_name, latest)

            return {
                "has_typescript": has_typescript,
                "bundle_size": bundle_size
            }

    async def _get_bundle_size(self, package_name: str, version: str) -> str:
        """Bundlephobia에서 번들 크기 조회"""
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"https://bundlephobia.com/api/size",
                    params={"package": f"{package_name}@{version}"},
                    timeout=5.0
                )

                if response.status_code == 200:
                    data = response.json()
                    gzip_size = data.get("gzip", 0)
                    return f"{gzip_size // 1024}KB" if gzip_size else "Unknown"
            except:
                pass

            return "Unknown"

class WebSearcher:
    """웹 검색 (Google/Bing API 또는 LangChain WebSearch tool)"""

    async def search(self, query: str) -> List[Dict]:
        """웹 검색 실행"""
        # LangChain의 WebSearch tool 사용 또는 직접 API 호출
        # 여기서는 WebSearch tool 사용 예시
        from langchain_community.tools import DuckDuckGoSearchRun

        search = DuckDuckGoSearchRun()
        results = search.run(query + " 2025")

        # 결과 파싱 및 구조화
        return self._parse_web_results(results)

    def _parse_web_results(self, raw_results: str) -> List[Dict]:
        """웹 검색 결과 파싱"""
        # 실제로는 더 정교한 파싱 필요
        return [{
            "source": "web",
            "content": raw_results,
            "relevance_score": 0.8
        }]

class MultiSourceSearcher:
    """모든 소스를 통합 검색"""

    def __init__(
        self,
        github_token: str,
        web_search_api_key: Optional[str] = None
    ):
        self.github = GitHubSearcher(github_token)
        self.npm = NpmSearcher()
        self.web = WebSearcher()

    async def search_all(
        self,
        query: str,
        language: str = "TypeScript"
    ) -> List[Dict]:
        """모든 소스에서 병렬 검색"""
        tasks = [
            self.github.search_repositories(query, language),
            self.npm.search_packages(query),
            self.web.search(f"{query} {language} library")
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 에러 처리 및 결과 병합
        all_results = []
        for result in results:
            if isinstance(result, list):
                all_results.extend(result)

        return all_results
```

**3. Filter and Ranking Engine**

```python
# src/agents/open_source/filter_rank.py

from typing import List, Dict
from datetime import datetime, timedelta
import re

class OpenSourceFilter:
    """오픈소스 라이브러리 필터링"""

    ALLOWED_LICENSES = ["MIT", "Apache-2.0", "ISC", "BSD-3-Clause"]

    def filter(self, libraries: List[Dict], criteria: Dict) -> List[Dict]:
        """필터링 기준에 따라 라이브러리 필터"""
        filtered = []

        for lib in libraries:
            if self._meets_criteria(lib, criteria):
                filtered.append(lib)

        return filtered

    def _meets_criteria(self, lib: Dict, criteria: Dict) -> bool:
        """개별 라이브러리가 기준을 충족하는지 확인"""

        # 1. 라이선스 체크
        if lib.get("license") not in self.ALLOWED_LICENSES:
            return False

        # 2. 최소 Stars (GitHub)
        min_stars = criteria.get("min_stars", 500)
        if lib.get("source") == "github":
            if lib.get("stars", 0) < min_stars:
                return False

        # 3. 최신성 체크
        max_months = criteria.get("max_last_update_months", 12)
        if lib.get("last_updated"):
            last_update = datetime.fromisoformat(
                lib["last_updated"].replace("Z", "+00:00")
            )
            cutoff = datetime.now() - timedelta(days=max_months * 30)
            if last_update < cutoff:
                return False

        # 4. TypeScript 지원 (선택사항)
        if criteria.get("require_typescript", True):
            if not lib.get("has_typescript"):
                # GitHub의 경우 language로 체크
                if lib.get("language") != "TypeScript":
                    return False

        # 5. 보안 취약점 없음 (추후 구현)
        # if lib.get("has_security_issues"):
        #     return False

        return True

class OpenSourceRanker:
    """오픈소스 라이브러리 랭킹"""

    def rank(self, libraries: List[Dict]) -> List[Dict]:
        """점수 기반 랭킹"""
        scored = []

        for lib in libraries:
            score = self._calculate_score(lib)
            lib["score"] = score
            scored.append(lib)

        # 점수 내림차순 정렬
        scored.sort(key=lambda x: x["score"], reverse=True)

        return scored

    def _calculate_score(self, lib: Dict) -> float:
        """라이브러리 점수 계산 (0-100)"""
        score = 0.0

        # 1. 인기도 (40점)
        if lib.get("source") == "github":
            stars = lib.get("stars", 0)
            score += min(stars / 1000, 20)  # Max 20점

        if lib.get("source") == "npm":
            downloads = lib.get("weekly_downloads", 0)
            score += min(downloads / 10000, 20)  # Max 20점

        # 2. 최신성 (20점)
        if lib.get("last_updated"):
            last_update = datetime.fromisoformat(
                lib["last_updated"].replace("Z", "+00:00")
            )
            months_ago = (datetime.now() - last_update).days / 30

            if months_ago < 3:
                score += 20
            elif months_ago < 6:
                score += 15
            elif months_ago < 12:
                score += 10

        # 3. 품질 지표 (20점)
        if lib.get("has_typescript"):
            score += 10
        if lib.get("description"):
            score += 5  # 설명이 있으면 문서화가 잘 되어있을 가능성
        # 추가: test coverage, documentation 등

        # 4. 번들 크기 (20점)
        bundle_size = lib.get("bundle_size", "Unknown")
        if bundle_size != "Unknown":
            size_kb = int(re.search(r"\d+", bundle_size).group())
            if size_kb < 20:
                score += 20
            elif size_kb < 50:
                score += 15
            elif size_kb < 100:
                score += 10
            elif size_kb < 200:
                score += 5

        return score
```

**4. LangGraph 노드 통합**

```python
# src/graph/nodes/open_source_search.py

from typing import Dict
from langchain_anthropic import ChatAnthropic
from src.agents.open_source.keyword_extractor import KeywordExtractor
from src.agents.open_source.searchers import MultiSourceSearcher
from src.agents.open_source.filter_rank import OpenSourceFilter, OpenSourceRanker

async def open_source_search_node(state: Dict) -> Dict:
    """
    LangGraph Node: 오픈소스 검색 및 추천
    """
    user_message = state["user_feedback"]
    tech_stack = state.get("project_tech_stack", {})

    # 1. 키워드 추출
    extractor = KeywordExtractor(ChatAnthropic(model="claude-sonnet-4.5"))
    keywords_data = await extractor.extract(user_message)

    # 검색 필요 여부 판단
    if not keywords_data.get("keywords"):
        return state  # 검색 불필요

    # 2. 멀티소스 검색
    searcher = MultiSourceSearcher(
        github_token=os.getenv("GITHUB_TOKEN")
    )

    search_results = await searcher.search_all(
        query=" ".join(keywords_data["keywords"]),
        language=tech_stack.get("language", "TypeScript")
    )

    # 3. 필터링
    filter_engine = OpenSourceFilter()
    filtered = filter_engine.filter(search_results, {
        "min_stars": 1000,
        "max_last_update_months": 12,
        "require_typescript": True
    })

    # 4. 랭킹
    ranker = OpenSourceRanker()
    ranked = ranker.rank(filtered)

    # 5. 상위 3개 선택
    top_3 = ranked[:3]

    # 6. 사용자에게 제시할 형식으로 변환
    suggestions = format_suggestions(top_3, keywords_data)

    # 7. State 업데이트
    state["open_source_suggestions"] = {
        "keywords": keywords_data,
        "options": top_3,
        "formatted": suggestions,
        "timestamp": datetime.now().isoformat()
    }

    # 사용자에게 표시 (실제로는 WebSocket 등으로 전송)
    print(suggestions)

    return state

def format_suggestions(libraries: List[Dict], keywords: Dict) -> str:
    """사용자에게 보여줄 형식으로 변환"""
    output = f"""
┌──────────────────────────────────────────────────────┐
│ 🔍 오픈소스 라이브러리 검색 중...                   │
│ 키워드: {', '.join(keywords['keywords'])}           │
└──────────────────────────────────────────────────────┘

✅ {len(libraries)}가지 옵션을 찾았습니다:

"""

    for idx, lib in enumerate(libraries, 1):
        stars_str = f"{lib.get('stars', 0):,}" if lib.get('stars') else "N/A"
        license_str = lib.get('license', 'Unknown')
        bundle_str = lib.get('bundle_size', 'Unknown')

        output += f"""
{'━' * 54}
{idx}. {lib['name']} {'⭐ 추천' if idx == 1 else ''}
{'━' * 54}
   📦 GitHub: {lib.get('full_name', lib.get('npm_url', 'N/A'))}
   ⭐ Stars: {stars_str}
   📄 License: {license_str}
   📏 Bundle: {bundle_str}
   📅 Updated: {lib.get('last_updated', 'Unknown')[:10]}

   ✨ 특징:
   {lib.get('description', 'No description')}

   💡 점수: {lib.get('score', 0):.1f}/100

"""

    output += f"""
🤔 어떤 라이브러리를 사용하시겠습니까?
   입력: 1, 2, 3, 또는 "skip" (건너뛰기)
"""

    return output
```

**5. 사용자 선택 처리**

```python
# src/graph/nodes/handle_open_source_selection.py

async def handle_open_source_selection_node(state: Dict) -> Dict:
    """
    사용자가 선택한 오픈소스를 문서에 추가
    """
    user_choice = state["user_feedback"].strip()

    # 선택한 옵션 파싱
    if user_choice.lower() == "skip":
        return state

    try:
        choice_idx = int(user_choice) - 1
        suggestions = state["open_source_suggestions"]
        selected = suggestions["options"][choice_idx]

        # 선택된 라이브러리를 state에 추가
        if "selected_open_source" not in state:
            state["selected_open_source"] = []

        state["selected_open_source"].append({
            **selected,
            "selected_at": datetime.now().isoformat(),
            "screen": state["current_screen"],
            "keywords": suggestions["keywords"]
        })

        # 성공 메시지
        print(f"""
✅ {selected['name']}를 선택하셨습니다!

📝 다음 문서에 추가되었습니다:
   • Open_Source_Recommendations_v0.9.md
   • Design_System_v0.9.md
   • Screen_Specifications_v0.9.md

📦 설치 명령어:
   npm install {selected['name']}
""")

    except (ValueError, IndexError):
        print("올바른 선택지를 입력해주세요 (1, 2, 3 또는 skip)")

    return state
```

### 8.5.3 문서 생성 통합

**오픈소스 추천 문서 생성**

```python
# src/generators/open_source_recommendations_doc.py

async def generate_open_source_recommendations_doc(state: Dict) -> str:
    """
    Open_Source_Recommendations_v0.9.md 생성
    """
    selected = state.get("selected_open_source", [])

    if not selected:
        return ""  # 선택된 오픈소스 없음

    # 카테고리별 그룹화
    categorized = {}
    for lib in selected:
        category = lib.get("keywords", {}).get("category", "기타")
        if category not in categorized:
            categorized[category] = []
        categorized[category].append(lib)

    doc = f"""# 오픈소스 추천 목록

## 프로젝트 정보
- **프로젝트명**: {state.get('project_name', 'Unknown')}
- **기술 스택**: {', '.join(state.get('project_tech_stack', {}).values())}
- **생성일**: {datetime.now().strftime('%Y-%m-%d')}

---

"""

    for category, items in categorized.items():
        doc += f"## {category}\n\n"

        for item in items:
            doc += f"### {item['name']} ⭐ 선택됨\n\n"
            doc += f"- **GitHub**: {item.get('url', 'N/A')}\n"
            doc += f"- **Stars**: {item.get('stars', 'N/A'):,}\n"
            doc += f"- **License**: {item.get('license', 'Unknown')}\n"
            doc += f"- **번들 크기**: {item.get('bundle_size', 'Unknown')}\n"
            doc += f"- **선택 이유**: {item.get('description', 'N/A')}\n"
            doc += f"- **사용 화면**: {item.get('screen', 'N/A')}\n"
            doc += f"- **선택 시각**: {item.get('selected_at', 'N/A')}\n\n"

    # 의존성 요약
    doc += "## 의존성 요약\n\n```json\n{\n  \"dependencies\": {\n"
    for lib in selected:
        doc += f'    "{lib["name"]}": "^{lib.get("version", "latest")}",\n'
    doc += "  }\n}\n```\n\n"

    # 설치 스크립트
    doc += "## 설치 스크립트\n\n```bash\n"
    for lib in selected:
        doc += f"npm install {lib['name']}\n"
    doc += "```\n"

    return doc
```

### 8.5.4 API 엔드포인트

```python
# src/api/routes/open_source.py

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List

router = APIRouter()

class SearchRequest(BaseModel):
    query: str
    language: str = "TypeScript"

class SearchResponse(BaseModel):
    results: List[Dict]
    count: int

@router.post("/search", response_model=SearchResponse)
async def search_open_source(request: SearchRequest):
    """
    오픈소스 검색 API
    """
    searcher = MultiSourceSearcher(
        github_token=os.getenv("GITHUB_TOKEN")
    )

    results = await searcher.search_all(
        query=request.query,
        language=request.language
    )

    filter_engine = OpenSourceFilter()
    filtered = filter_engine.filter(results, {
        "min_stars": 500,
        "max_last_update_months": 12
    })

    ranker = OpenSourceRanker()
    ranked = ranker.rank(filtered)

    return SearchResponse(
        results=ranked[:10],
        count=len(ranked)
    )
```

### 8.5.5 캐싱 전략

```python
# src/cache/open_source_cache.py

import redis
import json
from typing import Optional, List, Dict

class OpenSourceCache:
    """Redis 기반 오픈소스 검색 캐시"""

    def __init__(self, redis_url: str):
        self.redis = redis.from_url(redis_url)
        self.ttl = 86400  # 24시간

    def get(self, query: str) -> Optional[List[Dict]]:
        """캐시에서 검색 결과 조회"""
        key = f"opensearch:{query}"
        cached = self.redis.get(key)

        if cached:
            return json.loads(cached)

        return None

    def set(self, query: str, results: List[Dict]):
        """검색 결과 캐싱"""
        key = f"opensearch:{query}"
        self.redis.setex(
            key,
            self.ttl,
            json.dumps(results)
        )
```

---

## 9. 품질 검증 시스템

### 9.1 자동 검증 프로세스

```python
async def quality_check_node(state: DesignAgentState) -> DesignAgentState:
    """
    LangGraph Node: 품질 검증 수행
    """
    validator = ValidationAgent(llm)
    
    # 1. PRD 정합성 검증
    prd_alignment = await validator.validate_prd_alignment(
        state["prd_content"],
        state["screens"]
    )
    
    # 2. 디자인 시스템 일관성 검증
    design_consistency = await validator.validate_design_consistency(
        state["design_system"],
        state["screens"]
    )
    
    # 3. UX Flow 완결성 검증
    ux_completeness = await validator.validate_ux_completeness(
        state["ux_flow"]
    )
    
    # 검증 점수 계산
    state["validation_score"] = {
        "design_system": design_consistency["consistency_score"],
        "ux_flow": ux_completeness["completeness_score"],
        "prd_alignment": prd_alignment["alignment_score"],
        "overall": (
            design_consistency["consistency_score"] +
            ux_completeness["completeness_score"] +
            prd_alignment["alignment_score"]
        ) / 3
    }
    
    # 개선 사항 수집
    issues = []
    issues.extend(prd_alignment.get("missing_screens", []))
    issues.extend(design_consistency.get("issues", []))
    issues.extend(ux_completeness.get("issues", []))
    
    state["validation_issues"] = issues
    state["current_phase"] = "auto_improve"
    
    return state
```

### 9.2 자동 개선 시스템

```python
async def auto_improve_node(state: DesignAgentState) -> DesignAgentState:
    """
    LangGraph Node: 검증 결과 기반 자동 개선
    """
    issues = state.get("validation_issues", [])
    improvements = []
    
    for issue in issues:
        if issue["type"] == "color_inconsistency":
            # 색상 변수명 통일
            improvement = await unify_color_variables(
                state["design_system"],
                state["screens"]
            )
            improvements.append({
                "type": "color_unification",
                "description": "색상 변수명 통일",
                "before": issue["details"]["before"],
                "after": improvement["after"]
            })
        
        elif issue["type"] == "missing_path":
            # 누락된 네비게이션 경로 추가
            improvement = await add_missing_navigation(
                state["ux_flow"],
                issue["details"]
            )
            improvements.append({
                "type": "navigation_added",
                "description": f"{issue['details']['from']} → {issue['details']['to']} 경로 추가",
                "path": improvement["path"]
            })
        
        elif issue["type"] == "missing_edge_case":
            # Edge case 디자인 추가
            improvement = await add_edge_case_design(
                state["screens"],
                issue["details"]
            )
            improvements.append({
                "type": "edge_case_added",
                "description": f"{issue['details']['state']} 상태 디자인 추가",
                "screen": issue["details"]["screen"]
            })
    
    state["auto_improvements"] = improvements
    state["current_phase"] = "finalize"
    
    return state

async def unify_color_variables(design_system: Dict, screens: List[Dict]) -> Dict:
    """색상 변수 통일"""
    # 예: #667eea → $primary-purple 로 변환
    color_map = {}
    for color_name, color_value in design_system["colors"].items():
        color_map[color_value] = f"${color_name}"
    
    for screen in screens:
        # ASCII UI에서 색상 코드를 변수로 치환
        for hex_code, var_name in color_map.items():
            screen["ascii_ui"] = screen["ascii_ui"].replace(hex_code, var_name)
    
    return {"after": color_map}
```

### 9.3 품질 점수 시각화

```python
def format_quality_report(state: DesignAgentState) -> str:
    """
    품질 검증 결과 포맷팅
    """
    scores = state["validation_score"]
    improvements = state.get("auto_improvements", [])
    
    # 별점 계산
    def get_stars(score: int) -> str:
        stars = int(score / 20)
        return "⭐" * stars
    
    report = f"""
┌────────────────────────────────────┐
│ 🎉 디자인 문서 생성 완료!          │
│                                    │
│ 📊 문서 품질 점수                  │
│ ├─ Design System: {scores['design_system']}/100 {get_stars(scores['design_system'])}│
│ ├─ UX Flow: {scores['ux_flow']}/100 {get_stars(scores['ux_flow'])}      │
│ ├─ PRD Alignment: {scores['prd_alignment']}/100 {get_stars(scores['prd_alignment'])} │
│ └─ Overall: {scores['overall']:.0f}/100 {get_stars(int(scores['overall']))}   │
│                                    │
│ ✅ 자동 개선 ({len(improvements)}건)                 │
"""
    
    for i, imp in enumerate(improvements[:5], 1):
        report += f"│ {i}. {imp['description']:<30} │\n"
    
    report += """│                                    │
│ [📄 문서 보기]  [다음: 개발 →]    │
└────────────────────────────────────┘
    """
    
    return report
```

---

## 10. 배포 및 확장성

### 10.1 Docker 컨테이너화

```dockerfile
# Dockerfile

FROM python:3.11-slim

WORKDIR /app

# 시스템 의존성 설치
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Python 의존성 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 애플리케이션 코드 복사
COPY . .

# 환경 변수 설정
ENV PYTHONUNBUFFERED=1
ENV ENVIRONMENT=production

# 헬스체크
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# 포트 노출
EXPOSE 8000

# 실행 명령
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

```yaml
# docker-compose.yml

version: '3.8'

services:
  design-agent:
    build: .
    ports:
      - "8000:8000"
    environment:
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
      - POSTGRES_CONN_STRING=postgresql://user:pass@postgres:5432/anyon
      - REDIS_URL=redis://redis:6379
    depends_on:
      - postgres
      - redis
    volumes:
      - ./output:/app/output
  
  postgres:
    image: postgres:15
    environment:
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=pass
      - POSTGRES_DB=anyon
    volumes:
      - postgres_data:/var/lib/postgresql/data
  
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

volumes:
  postgres_data:
```

### 10.2 Kubernetes 배포 (선택)

```yaml
# k8s/deployment.yaml

apiVersion: apps/v1
kind: Deployment
metadata:
  name: design-agent
spec:
  replicas: 3
  selector:
    matchLabels:
      app: design-agent
  template:
    metadata:
      labels:
        app: design-agent
    spec:
      containers:
      - name: design-agent
        image: gcr.io/anyon-project/design-agent:latest
        ports:
        - containerPort: 8000
        env:
        - name: ANTHROPIC_API_KEY
          valueFrom:
            secretKeyRef:
              name: api-keys
              key: anthropic
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "2Gi"
            cpu: "2000m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5

---
apiVersion: v1
kind: Service
metadata:
  name: design-agent-service
spec:
  selector:
    app: design-agent
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8000
  type: LoadBalancer
```

### 10.3 수평적 확장 전략

```python
class DesignAgentScaler:
    """
    디자인 에이전트 자동 스케일링
    """
    
    def __init__(self):
        self.min_instances = 2
        self.max_instances = 10
        self.target_cpu_percent = 70
    
    async def scale_based_on_load(self):
        """부하 기반 스케일링"""
        current_load = await self.get_current_load()
        current_instances = await self.get_current_instances()
        
        if current_load > self.target_cpu_percent:
            # 스케일 업
            new_instances = min(current_instances + 1, self.max_instances)
            await self.scale_to(new_instances)
        
        elif current_load < self.target_cpu_percent * 0.5:
            # 스케일 다운
            new_instances = max(current_instances - 1, self.min_instances)
            await self.scale_to(new_instances)
    
    async def scale_based_on_queue(self):
        """큐 길이 기반 스케일링"""
        queue_length = await self.get_queue_length()
        
        if queue_length > 50:
            # 대기 작업이 많으면 스케일 업
            await self.scale_to(self.max_instances)
        elif queue_length < 10:
            # 대기 작업이 적으면 스케일 다운
            await self.scale_to(self.min_instances)
```

### 10.4 성능 모니터링

```python
from prometheus_client import Counter, Histogram, Gauge

# 메트릭 정의
design_requests_total = Counter(
    'design_agent_requests_total',
    'Total number of design requests'
)

design_duration_seconds = Histogram(
    'design_agent_duration_seconds',
    'Time spent processing design requests'
)

active_design_sessions = Gauge(
    'design_agent_active_sessions',
    'Number of active design sessions'
)

document_generation_errors = Counter(
    'design_agent_document_errors_total',
    'Total number of document generation errors'
)

# 메트릭 수집
async def process_design_request_with_metrics(state: DesignAgentState):
    design_requests_total.inc()
    active_design_sessions.inc()
    
    start_time = time.time()
    
    try:
        result = await process_design_request(state)
        duration = time.time() - start_time
        design_duration_seconds.observe(duration)
        
        return result
    
    except Exception as e:
        document_generation_errors.inc()
        raise
    
    finally:
        active_design_sessions.dec()
```

---

## 11. 실행 예제

### 11.1 기본 실행

```python
# main.py

import asyncio
from design_agent import DesignAgentGraph, DesignAgentState
from anyon_integration import ANYONKanbanIntegration

async def main():
    # 초기화
    graph = DesignAgentGraph()
    kanban = ANYONKanbanIntegration("https://api.anyon.com")
    
    # 입력 데이터
    prd = load_prd_from_file("01_Planning/PRD_v1.0.md")
    trd = load_trd_from_file("01_Planning/TRD_v1.0.md")
    
    # 디자인 에이전트 실행
    agent = DesignAgentWithKanbanIntegration(graph, kanban)
    
    final_state = await agent.run(
        project_id="proj_12345",
        prd=prd,
        trd=trd
    )
    
    # 결과 출력
    print(format_quality_report(final_state))

if __name__ == "__main__":
    asyncio.run(main())
```

### 11.2 대화형 실행 (CLI)

```python
# cli.py

import asyncio
from design_agent import DesignAgentGraph

async def interactive_design():
    """대화형 CLI 모드"""
    graph = DesignAgentGraph()
    
    print("🎨 ANYON 디자인 에이전트 (대화형 모드)")
    print("=" * 50)
    
    # PRD/TRD 로드
    prd = input("PRD 파일 경로: ")
    trd = input("TRD 파일 경로: ")
    
    initial_state = {
        "project_id": "cli_session",
        "prd_content": open(prd).read(),
        "trd_content": open(trd).read(),
        "current_phase": "init",
        "screens": [],
        "conversation_history": []
    }
    
    # 스트리밍 실행
    async for event in graph.compiled_graph.astream(initial_state):
        node_name = list(event.keys())[0]
        state = event[node_name]
        
        if node_name == "generate_ascii_ui":
            # ASCII UI 표시
            print(state["current_ui_display"])
            
            # 사용자 피드백 입력
            feedback = input("\n피드백 입력: ")
            state["user_feedback"] = feedback

if __name__ == "__main__":
    asyncio.run(interactive_design())
```

### 11.3 API 서버 실행

```python
# api.py

from fastapi import FastAPI, WebSocket
from design_agent import DesignAgentGraph
from anyon_integration import ANYONKanbanIntegration

app = FastAPI()

@app.post("/api/design/start")
async def start_design(request: DesignRequest):
    """디자인 프로세스 시작"""
    graph = DesignAgentGraph()
    kanban = ANYONKanbanIntegration(settings.KANBAN_API_URL)
    
    agent = DesignAgentWithKanbanIntegration(graph, kanban)
    
    # 비동기 작업으로 실행
    task_id = await agent.run_async(
        project_id=request.project_id,
        prd=request.prd,
        trd=request.trd
    )
    
    return {"task_id": task_id, "status": "started"}

@app.websocket("/ws/design/{project_id}")
async def websocket_design(websocket: WebSocket, project_id: str):
    """실시간 디자인 업데이트"""
    await websocket.accept()
    
    handler = DesignAgentWebSocketHandler(websocket)
    graph = DesignAgentGraph()
    
    # 실시간 스트리밍
    async for event in graph.compiled_graph.astream(initial_state):
        await handler.send_progress(event)
    
    await websocket.close()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

---

## 12. 결론

### 12.1 핵심 성과
이 디자인 에이전트는 LangGraph 기반으로 구축되어 다음을 달성합니다:

1. **비개발자 친화적**: ASCII UI를 통한 직관적 디자인 프로세스
2. **자동화**: 5개 문서 자동 생성 및 품질 검증
3. **확장성**: 칸반보드와 seamless 통합
4. **안정성**: 에러 핸들링 및 재시도 메커니즘
5. **효율성**: 병렬 문서 생성으로 시간 단축

### 12.2 향후 개선 방향
- **다국어 지원**: ASCII UI 다국어 버전
- **AI 모델 선택**: 사용자가 LLM 선택 가능
- **버전 관리**: Git 통합 디자인 이력 관리
- **협업 기능**: 다중 사용자 동시 디자인
- **템플릿 라이브러리**: 사전 정의된 디자인 패턴

---

## 부록

### A. requirements.txt

```txt
# Core Framework
fastapi>=0.121.0,<1.0.0
uvicorn[standard]>=0.30.0,<1.0.0

# LangChain & LangGraph
langgraph>=1.0.3,<2.0.0
langchain>=1.0.0,<2.0.0
langchain-anthropic>=0.4.0
langchain-core>=1.0.0

# LLM Providers
anthropic>=0.40.0,<1.0.0  # Updated for Claude Sonnet 4.5
openai>=1.50.0,<2.0.0

# HTTP & WebSockets
httpx>=0.27.0,<1.0.0
websockets>=13.0,<14.0

# Database & State
redis>=5.2.0,<6.0.0
psycopg2-binary>=2.9.10,<3.0.0
sqlalchemy>=2.0.35,<3.0.0

# Data Validation
pydantic>=2.10.0,<3.0.0

# Utilities
python-dotenv>=1.0.1,<2.0.0
prometheus-client>=0.21.0,<1.0.0
loguru>=0.7.2,<1.0.0
```

### B. 환경 변수 템플릿

```bash
# .env.example

# API Keys
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-...

# Database
POSTGRES_CONN_STRING=postgresql://user:pass@localhost:5432/anyon
REDIS_URL=redis://localhost:6379

# ANYON Platform
KANBAN_API_URL=https://api.anyon.com
KANBAN_API_KEY=...

# Environment
ENVIRONMENT=development
LOG_LEVEL=INFO

# Paths
OUTPUT_DIR=/app/output
UPLOAD_DIR=/app/uploads
```

### C. 참고 자료
- [LangGraph 공식 문서](https://python.langchain.com/docs/langgraph)
- [ANYON 아키텍처 문서](https://github.com/anyon/architecture)
- [ASCII Art 가이드](https://en.wikipedia.org/wiki/ASCII_art)
- [Design System 베스트 프랙티스](https://www.designsystems.com/)