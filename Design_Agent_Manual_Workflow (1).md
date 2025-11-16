# ANYON 디자인 에이전트 - Google AI Studio 수동 워크플로우

## 🎯 핵심 개념

**LangGraph 자동화 + 사용자 수동 개입 하이브리드 구조**

```
LangGraph 자동 → ⏸️ 일시정지 → 👤 사용자 작업 (Google AI Studio) → ▶️ LangGraph 재개
```

---

## 🔄 전체 워크플로우 (6 Phase)

### **Phase 1-4: LangGraph 자동 실행** (15분)

```
┌─────────────────────────────────────┐
│   기획 에이전트에서 PRD/TRD 전달    │
└─────────────────────────────────────┘
              ↓
┌─────────────────────────────────────┐
│  Phase 1: 화면 추출 (2분)           │
│  - PRD 파싱                         │
│  - 화면 목록 추출                   │
└─────────────────────────────────────┘
              ↓
┌─────────────────────────────────────┐
│  Phase 2: 옵션 생성 (3분)           │
│  - 화면별 2-3개 레이아웃 옵션       │
│  - 사용자 선택                      │
└─────────────────────────────────────┘
              ↓
┌─────────────────────────────────────┐
│  Phase 3: ASCII UI 대화 (8분) ⭐    │
│  - ASCII UI 생성                    │
│  - 자연어 대화형 수정               │
│  - 확정                             │
└─────────────────────────────────────┘
              ↓
┌─────────────────────────────────────┐
│  Phase 4: Design System (2분)       │
│  - 컴포넌트 추출                    │
│  - 디자인 시스템 정의               │
│  - 프롬프트 생성                    │
└─────────────────────────────────────┘
              ↓
┌─────────────────────────────────────┐
│  🎉 프롬프트 생성 완료!             │
│                                     │
│  ✅ ASCII UI 확정                   │
│  ✅ Design System 정의              │
│  ✅ Google AI Studio 프롬프트 준비  │
└─────────────────────────────────────┘
```

---

### **━━━━ ⏸️ LangGraph 일시 정지 ━━━━**

### **수동 개입 구간: Google AI Studio 작업** (10-30분)

```
┌─────────────────────────────────────────────┐
│  ANYON 화면:                                │
│                                             │
│  📋 생성된 프롬프트:                        │
│  ┌───────────────────────────────────────┐ │
│  │ Create React component for            │ │
│  │ HomeDashboard...                      │ │
│  │                                       │ │
│  │ ASCII Layout:                         │ │
│  │ ┌─────────────────────┐              │ │
│  │ │  FitTracker 🏋️     │              │ │
│  │ │  안녕하세요, 철수님!│              │ │
│  │ └─────────────────────┘              │ │
│  │ ...                                   │ │
│  └───────────────────────────────────────┘ │
│                                             │
│  [📋 프롬프트 복사]                         │
│  [🌐 Google AI Studio로 이동] ← 클릭!      │
└─────────────────────────────────────────────┘
              ↓
┌─────────────────────────────────────────────┐
│  🌐 Google AI Studio 웹사이트 열림          │
│  (새 탭 또는 새 창)                         │
└─────────────────────────────────────────────┘
              ↓
┌─────────────────────────────────────────────┐
│  👤 사용자 작업:                            │
│                                             │
│  1️⃣ 프롬프트 붙여넣기                       │
│     (이미 클립보드에 복사됨)                │
│                                             │
│  2️⃣ 이미지/디자인 생성                      │
│     - "Generate" 클릭                       │
│     - 결과 확인                             │
│                                             │
│  3️⃣ 마음에 들 때까지 조정                   │
│     - 프롬프트 수정                         │
│     - 재생성 반복                           │
│     - 색상, 레이아웃 조정                   │
│                                             │
│  4️⃣ 코드 생성 (선택)                        │
│     - "Get code" 버튼                       │
│     - 또는 직접 작성                        │
│                                             │
│  5️⃣ 코드 복사                               │
│     - 생성된 React 코드 복사                │
│     - 또는 .tsx 파일 다운로드               │
└─────────────────────────────────────────────┘
              ↓
┌─────────────────────────────────────────────┐
│  ANYON으로 돌아오기                         │
│                                             │
│  📤 코드 업로드 화면:                       │
│  ┌───────────────────────────────────────┐ │
│  │ HomeDashboard.tsx 코드를 붙여넣거나   │ │
│  │ 파일을 업로드하세요                   │ │
│  │                                       │ │
│  │ [📎 파일 업로드]                      │ │
│  │ [📝 코드 붙여넣기]                    │ │
│  └───────────────────────────────────────┘ │
│                                             │
│  [✅ 완료] ← 클릭하면 다음 Phase로         │
└─────────────────────────────────────────────┘
```

---

### **━━━━ ▶️ LangGraph 재개 ━━━━**

### **Phase 5-6: LangGraph 자동 실행** (5분)

```
┌─────────────────────────────────────┐
│  Phase 5: 코드 검증 (2분)           │
│  - Lint 검사                        │
│  - TypeScript 타입 검증             │
│  - Tailwind CSS 검증                │
│  - 접근성 체크                      │
└─────────────────────────────────────┘
              ↓
┌─────────────────────────────────────┐
│  Phase 6: 패키징 (3분)              │
│  - 문서 5개 생성                    │
│  - 코드 + 문서 패키징               │
│  - 백로그 에이전트로 전달           │
└─────────────────────────────────────┘
              ↓
┌─────────────────────────────────────┐
│  🎉 디자인 에이전트 완료!           │
│                                     │
│  📄 문서: 5개                       │
│  💻 코드: 6개 화면                  │
│  📊 품질: 검증 완료                 │
└─────────────────────────────────────┘
              ↓
┌─────────────────────────────────────┐
│   백로그 에이전트로 전달            │
│   (백로그 에이전트가 Epic/Story     │
│    분해 후 개발 티켓 생성)          │
└─────────────────────────────────────┘
```

---

## 📊 LangGraph State 설계

### **State 정의**

```python
from typing import TypedDict, List, Dict, Optional, Literal

class DesignAgentState(TypedDict):
    # INPUT (기획에서 받음)
    prd_content: str
    trd_content: str
    
    # Phase 1-2: 화면 분석
    screens: List[Dict]  # 추출한 화면 목록
    design_options: List[Dict]  # 각 화면의 레이아웃 옵션
    selected_options: Dict[str, int]  # 사용자가 선택한 옵션
    
    # Phase 3: ASCII UI 대화
    current_screen: str  # 현재 작업 중인 화면
    current_screen_ascii: str  # ASCII UI
    conversation_history: List[Dict]
    user_feedback: str
    design_confirmed: bool  # 확정 여부
    
    # Phase 4: Design System
    design_system: Dict
    components: List[Dict]
    ai_studio_prompts: Dict[str, str]  # 화면별 프롬프트
    
    # ⏸️ 일시정지 구간
    pause_state: Literal["waiting_for_code", "code_received", "completed"]
    current_screen_code: Optional[str]  # 사용자가 업로드한 코드
    
    # Phase 5-6: 검증 및 패키징
    code_validation_results: Dict
    generated_documents: Dict[str, str]
    final_package: Dict
    
    # 메타데이터
    timestamp: str
    user_id: str
    project_id: str
```

---

## 🏗️ LangGraph Nodes 구조

### **11개 노드 + 2개 Human-in-the-Loop 노드**

```python
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.postgres import PostgresSaver

# PostgreSQL 체크포인터 (상태 저장)
checkpointer = PostgresSaver.from_conn_string(
    "postgresql://user:pass@localhost/anyon_db"
)

# Graph 생성
workflow = StateGraph(DesignAgentState)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Phase 1-4: 자동 실행
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# Phase 1: 화면 추출
workflow.add_node("extract_screens", extract_screens_node)

# Phase 2: 옵션 생성
workflow.add_node("generate_options", generate_options_node)
workflow.add_node("user_select_option", user_select_option_node)  # Human input

# Phase 3: ASCII UI 대화
workflow.add_node("create_ascii_ui", create_ascii_ui_node)
workflow.add_node("refine_design", refine_design_node)  # Human input, 반복

# Phase 4: Design System
workflow.add_node("build_design_system", build_design_system_node)
workflow.add_node("generate_ai_prompts", generate_ai_prompts_node)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# ⏸️ Human-in-the-Loop: Google AI Studio
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

workflow.add_node("pause_for_google_ai", pause_for_google_ai_node)  # 일시정지
workflow.add_node("receive_code", receive_code_node)  # 코드 수신

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Phase 5-6: 자동 실행
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# Phase 5: 코드 검증
workflow.add_node("validate_code", validate_code_node)

# Phase 6: 패키징
workflow.add_node("generate_documents", generate_documents_node)
workflow.add_node("package_for_dev", package_for_dev_node)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 엣지 정의
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

workflow.set_entry_point("extract_screens")

# Phase 1-2
workflow.add_edge("extract_screens", "generate_options")
workflow.add_edge("generate_options", "user_select_option")
workflow.add_edge("user_select_option", "create_ascii_ui")

# Phase 3: 대화형 반복
workflow.add_conditional_edges(
    "create_ascii_ui",
    lambda state: "refine" if not state["design_confirmed"] else "continue",
    {
        "refine": "refine_design",
        "continue": "build_design_system"
    }
)
workflow.add_edge("refine_design", "create_ascii_ui")  # 루프

# Phase 4
workflow.add_edge("build_design_system", "generate_ai_prompts")
workflow.add_edge("generate_ai_prompts", "pause_for_google_ai")

# ⏸️ Human-in-the-Loop
workflow.add_conditional_edges(
    "pause_for_google_ai",
    lambda state: state["pause_state"],
    {
        "waiting_for_code": "pause_for_google_ai",  # 대기 루프
        "code_received": "receive_code"
    }
)

# Phase 5-6
workflow.add_edge("receive_code", "validate_code")
workflow.add_edge("validate_code", "generate_documents")
workflow.add_edge("generate_documents", "package_for_dev")
workflow.add_edge("package_for_dev", END)

# 컴파일
app = workflow.compile(checkpointer=checkpointer)
```

---

## 💻 핵심 노드 구현

### **1. pause_for_google_ai_node - 일시정지**

```python
async def pause_for_google_ai_node(state: DesignAgentState) -> DesignAgentState:
    """
    LangGraph 실행을 일시정지하고 사용자 개입 대기
    """
    current_screen = state["current_screen"]
    prompt = state["ai_studio_prompts"][current_screen]
    
    # ANYON UI에 표시할 데이터 준비
    ui_data = {
        "status": "waiting_for_code",
        "current_screen": current_screen,
        "prompt": prompt,
        "instructions": {
            "step1": "아래 프롬프트를 복사하세요",
            "step2": "Google AI Studio로 이동하세요",
            "step3": "프롬프트를 붙여넣고 코드를 생성하세요",
            "step4": "생성된 코드를 복사해서 돌아오세요"
        },
        "buttons": {
            "copy_prompt": "📋 프롬프트 복사",
            "open_ai_studio": "🌐 Google AI Studio 열기"
        }
    }
    
    # WebSocket으로 UI 업데이트
    await send_to_ui(state["user_id"], ui_data)
    
    # 상태 업데이트
    return {
        **state,
        "pause_state": "waiting_for_code",
        "timestamp": datetime.now().isoformat()
    }
```

### **2. receive_code_node - 코드 수신**

```python
async def receive_code_node(state: DesignAgentState) -> DesignAgentState:
    """
    사용자가 업로드한 코드 수신 및 저장
    """
    current_screen = state["current_screen"]
    uploaded_code = state["current_screen_code"]
    
    # 코드 저장
    code_storage = state.get("screen_codes", {})
    code_storage[current_screen] = {
        "code": uploaded_code,
        "timestamp": datetime.now().isoformat(),
        "source": "google_ai_studio"
    }
    
    # 다음 화면이 있는지 확인
    all_screens = state["screens"]
    current_index = next(i for i, s in enumerate(all_screens) if s["name"] == current_screen)
    
    if current_index < len(all_screens) - 1:
        # 다음 화면으로
        next_screen = all_screens[current_index + 1]["name"]
        return {
            **state,
            "screen_codes": code_storage,
            "current_screen": next_screen,
            "pause_state": "waiting_for_code",  # 다시 일시정지
            "current_screen_code": None
        }
    else:
        # 모든 화면 완료
        return {
            **state,
            "screen_codes": code_storage,
            "pause_state": "completed"
        }
```

### **3. validate_code_node - 코드 검증**

```python
async def validate_code_node(state: DesignAgentState) -> DesignAgentState:
    """
    업로드된 코드 자동 검증
    """
    screen_codes = state["screen_codes"]
    validation_results = {}
    
    for screen_name, code_info in screen_codes.items():
        code = code_info["code"]
        
        # 검증 항목
        checks = {
            "syntax": await check_syntax(code),
            "typescript": await check_typescript_types(code),
            "tailwind": await check_tailwind_only(code),
            "design_system": await check_design_system_compliance(
                code, 
                state["design_system"]
            ),
            "accessibility": await check_accessibility(code),
            "responsive": await check_responsive_design(code)
        }
        
        # 품질 점수 계산
        score = sum(1 for check in checks.values() if check["passed"]) / len(checks) * 100
        
        validation_results[screen_name] = {
            "score": score,
            "checks": checks,
            "passed": score >= 80  # 80점 이상 통과
        }
    
    return {
        **state,
        "code_validation_results": validation_results
    }
```

---

## 🎨 ANYON UI 구현

### **프롬프트 표시 화면**

```tsx
// components/DesignAgent/GoogleAIStudioPrompt.tsx

import React, { useState } from 'react';

interface Props {
  screenName: string;
  prompt: string;
  onCodeUpload: (code: string) => void;
}

export const GoogleAIStudioPrompt: React.FC<Props> = ({
  screenName,
  prompt,
  onCodeUpload
}) => {
  const [code, setCode] = useState('');
  const [uploadMode, setUploadMode] = useState<'paste' | 'file'>('paste');

  const handleCopyPrompt = () => {
    navigator.clipboard.writeText(prompt);
    toast.success('프롬프트가 클립보드에 복사되었습니다!');
  };

  const handleOpenAIStudio = () => {
    const aiStudioUrl = 'https://aistudio.google.com/';
    window.open(aiStudioUrl, '_blank');
    
    // 프롬프트 자동 복사
    navigator.clipboard.writeText(prompt);
  };

  const handleFileUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      const reader = new FileReader();
      reader.onload = (e) => {
        const content = e.target?.result as string;
        setCode(content);
      };
      reader.readAsText(file);
    }
  };

  const handleSubmit = () => {
    if (!code.trim()) {
      toast.error('코드를 입력해주세요');
      return;
    }
    onCodeUpload(code);
  };

  return (
    <div className="max-w-4xl mx-auto p-6">
      {/* 단계 표시 */}
      <div className="mb-8">
        <h2 className="text-2xl font-bold mb-4">
          {screenName} 화면 디자인 코드 생성
        </h2>
        
        <div className="flex items-center gap-4 mb-6">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-full bg-blue-500 text-white flex items-center justify-center">
              1
            </div>
            <span>프롬프트 복사</span>
          </div>
          
          <div className="flex-1 h-px bg-gray-300" />
          
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-full bg-blue-500 text-white flex items-center justify-center">
              2
            </div>
            <span>AI Studio 작업</span>
          </div>
          
          <div className="flex-1 h-px bg-gray-300" />
          
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-full bg-gray-300 text-white flex items-center justify-center">
              3
            </div>
            <span>코드 업로드</span>
          </div>
        </div>
      </div>

      {/* 프롬프트 표시 */}
      <div className="mb-6">
        <div className="flex items-center justify-between mb-2">
          <h3 className="font-semibold">생성된 프롬프트</h3>
          <button
            onClick={handleCopyPrompt}
            className="px-4 py-2 bg-gray-100 hover:bg-gray-200 rounded-lg flex items-center gap-2"
          >
            📋 복사
          </button>
        </div>
        
        <pre className="bg-gray-50 p-4 rounded-lg overflow-auto max-h-96 text-sm">
          {prompt}
        </pre>
      </div>

      {/* Google AI Studio 버튼 */}
      <button
        onClick={handleOpenAIStudio}
        className="w-full mb-8 py-4 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-semibold flex items-center justify-center gap-2"
      >
        🌐 Google AI Studio로 이동
        <span className="text-sm">(새 탭에서 열림)</span>
      </button>

      {/* 구분선 */}
      <div className="relative mb-8">
        <div className="absolute inset-0 flex items-center">
          <div className="w-full border-t border-gray-300" />
        </div>
        <div className="relative flex justify-center text-sm">
          <span className="px-4 bg-white text-gray-500">
            Google AI Studio에서 작업 후 코드를 가져오세요
          </span>
        </div>
      </div>

      {/* 코드 업로드 */}
      <div>
        <h3 className="font-semibold mb-4">생성된 코드 업로드</h3>
        
        <div className="flex gap-2 mb-4">
          <button
            onClick={() => setUploadMode('paste')}
            className={`px-4 py-2 rounded-lg ${
              uploadMode === 'paste'
                ? 'bg-blue-600 text-white'
                : 'bg-gray-100'
            }`}
          >
            📝 직접 붙여넣기
          </button>
          
          <button
            onClick={() => setUploadMode('file')}
            className={`px-4 py-2 rounded-lg ${
              uploadMode === 'file'
                ? 'bg-blue-600 text-white'
                : 'bg-gray-100'
            }`}
          >
            📎 파일 업로드
          </button>
        </div>

        {uploadMode === 'paste' ? (
          <textarea
            value={code}
            onChange={(e) => setCode(e.target.value)}
            placeholder="Google AI Studio에서 생성한 코드를 여기에 붙여넣으세요..."
            className="w-full h-64 p-4 border border-gray-300 rounded-lg font-mono text-sm"
          />
        ) : (
          <div className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center">
            <input
              type="file"
              accept=".tsx,.jsx,.ts,.js"
              onChange={handleFileUpload}
              className="hidden"
              id="file-upload"
            />
            <label
              htmlFor="file-upload"
              className="cursor-pointer"
            >
              <div className="text-4xl mb-2">📁</div>
              <div className="text-sm text-gray-600">
                .tsx 또는 .jsx 파일을 선택하세요
              </div>
            </label>
            
            {code && (
              <div className="mt-4 text-sm text-green-600">
                ✅ 파일이 로드되었습니다
              </div>
            )}
          </div>
        )}

        <button
          onClick={handleSubmit}
          disabled={!code.trim()}
          className="w-full mt-4 py-3 bg-green-600 hover:bg-green-700 disabled:bg-gray-300 text-white rounded-lg font-semibold"
        >
          ✅ 코드 제출하고 다음 단계로
        </button>
      </div>
    </div>
  );
};
```

---

## 🔄 실행 플로우 예시

### **전체 타임라인**

```
[0:00] 디자인 에이전트 시작
[0:02] Phase 1 완료 - 6개 화면 추출
[0:05] Phase 2 완료 - 레이아웃 옵션 선택
[0:13] Phase 3 완료 - ASCII UI 대화형 수정
[0:15] Phase 4 완료 - Design System + 프롬프트 생성

━━━━ ⏸️ LangGraph 일시정지 ━━━━

[0:15] 사용자: Google AI Studio로 이동
[0:16] 사용자: 프롬프트 붙여넣기
[0:17] AI Studio: 디자인 생성 중...
[0:20] 사용자: 결과 확인 및 조정
[0:25] 사용자: "Get code" 클릭
[0:26] 사용자: 코드 복사
[0:27] 사용자: ANYON으로 돌아와서 코드 붙여넣기
[0:28] 사용자: "제출" 클릭

━━━━ ▶️ LangGraph 재개 ━━━━

[0:28] Phase 5 시작 - 코드 검증
[0:30] Phase 6 시작 - 문서 생성 및 패키징
[0:33] ✅ 완료! 백로그 에이전트로 전달
```

---

## 📦 최종 산출물

### **백로그 에이전트로 전달되는 패키지**

```
📦 Design Package:

1. 📄 문서 5개
   ├─ Design_System_v0.9.md
   ├─ UX_Flow_v0.9.md
   ├─ Screen_Specifications_v0.9.md
   ├─ Google_AI_Studio_Prompts_v0.9.md
   └─ Design_Guidelines_v0.9.md

2. 💻 코드 6개 (사용자가 Google AI Studio에서 생성)
   ├─ HomeDashboard.tsx
   ├─ Login.tsx
   ├─ ExerciseSelection.tsx
   ├─ ExerciseLogging.tsx
   ├─ Profile.tsx
   └─ Onboarding.tsx

3. ✅ 검증 리포트
   ├─ Code Quality: 평균 92/100
   ├─ Design System Compliance: 95%
   ├─ Accessibility: WCAG AA 통과
   └─ TypeScript: 타입 완전성 100%

4. 📊 메타데이터
   ├─ 디자인 결정 기록 (12건)
   ├─ 사용자 피드백 로그
   └─ Google AI Studio 생성 로그
```

---

## 🎯 핵심 차별점

### **1. 하이브리드 자동화**
- ✅ 단순 반복 작업: LangGraph 자동화
- ✅ 창의적 작업: 사용자가 Google AI Studio에서 직접
- ✅ 검증 작업: LangGraph 자동화

### **2. 유연성**
- 사용자가 Google AI Studio에서 원하는 만큼 시간 투자
- 여러 버전 생성 및 비교 가능
- 만족할 때까지 반복

### **3. 품질 보증**
- Google AI Studio의 최신 생성 모델 활용
- ANYON의 자동 검증으로 품질 보증
- Design System 준수 자동 체크

### **4. 학습 곡선**
- 비개발자도 Google AI Studio의 직관적 UI 사용
- 실시간 프리뷰로 즉시 확인
- 코드 지식 불필요

---

## 🚀 구현 우선순위

### **1주차: 기본 플로우**
- Phase 1-4 구현 (화면 추출 → ASCII UI)
- 일시정지 노드 구현
- 코드 수신 노드 구현

### **2주차: UI 개발**
- 프롬프트 표시 화면
- Google AI Studio 리다이렉트 버튼
- 코드 업로드 화면

### **3주차: 검증 시스템**
- Phase 5 코드 검증 노드
- 품질 체크 알고리즘
- 자동 피드백 생성

### **4주차: 통합 및 테스트**
- 백로그 에이전트 연동
- 패키지 전달 구조 구현
- End-to-End 테스트

---

## 💡 개선 가능성

### **미래 고도화 옵션**

1. **Google AI Studio API 통합** (선택)
   - 현재: 수동 개입
   - 미래: API로 자동화 옵션 제공
   - 사용자 선택 가능하게

2. **버전 관리**
   - Google AI Studio에서 여러 버전 생성
   - ANYON에서 버전 비교 및 선택

3. **자동 개선**
   - 검증 실패 시 자동 수정 제안
   - 사용자가 선택만 하면 자동 적용

4. **템플릿 라이브러리**
   - 자주 쓰는 레이아웃 템플릿화
   - Google AI Studio 프롬프트 템플릿

---

## 🎉 결론

이 워크플로우는:

✅ **LangGraph의 자동화** + **Google AI Studio의 창의성** 결합
✅ **비개발자 친화적** - 코드 지식 불필요
✅ **유연성** - 사용자가 원하는 만큼 시간 투자
✅ **품질 보증** - 자동 검증 시스템
✅ **역할 명확** - 기획 → 디자인 → 백로그 → 개발 경계 존중

**디자인 에이전트의 역할:**
- PRD 읽기 → ASCII UI 생성 → 사용자와 대화 → 프롬프트 준비 → 코드 검증 → 문서화 → **백로그 에이전트로 전달**

**사용자의 역할:**
- Google AI Studio에서 창의적 디자인 작업

**백로그 에이전트의 역할 (다음 단계):**
- 디자인 산출물 받기 → Epic/Story 분해 → 칸반보드 티켓 생성 → 개발 에이전트로 전달

**완벽한 협업!** 🚀
