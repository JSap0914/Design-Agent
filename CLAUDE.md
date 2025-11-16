# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**ANYON Design Agent** is an AI-powered design automation system that bridges the gap between product planning (PRD/TRD) and development by creating interactive ASCII-based UI designs and generating comprehensive design documentation.

**Current Status:** Planning/documentation phase. This repository contains detailed architectural specifications and implementation plans, but **no source code has been implemented yet**. All files are Markdown documentation.

## Core Architecture

### LangGraph State Machine + Human-in-the-Loop

The system follows a **6-phase hybrid workflow**:

```
Phase 1-4: Automated (LangGraph)
    ↓ Screen extraction → Design options → ASCII UI dialogue → Design System
⏸ PAUSE: Human intervention (Google AI Studio)
    ↓ User creates actual designs manually
▶ RESUME: Automated (LangGraph)
    ↓ Code validation → Document generation → Packaging
```

**Key Components:**
- **11-node LangGraph state machine** with conditional routing
- **PostgreSQL checkpointer** for state persistence with pause/resume
- **Multi-agent orchestration**: ASCII UI Generator, Document Generator, Validation Agent
- **WebSocket** for real-time UI updates
- **BMAD methodology** principles applied throughout

### Technology Stack (Planned)

**Backend:**
- Python 3.11+ (Python 3.13 recommended)
- FastAPI 0.121+ (async support)
- LangGraph 1.0+ (state machine orchestration)
- Anthropic Claude Sonnet 4.5 (claude-sonnet-4-5-20250929) / GPT-4
- PostgreSQL (state persistence) + Redis (caching)
- Celery (task queue)

**Frontend:**
- React 19+ with TypeScript (React 18.3.1 also supported)
- Tailwind CSS (strictly enforced, no custom CSS)
- Socket.io Client (real-time updates)
- Zustand (state management)

**Infrastructure:**
- Docker / Kubernetes
- GCP / AWS
- Prometheus, Grafana, LangSmith (monitoring)

## Critical Role Boundaries

**Understanding the agent boundaries is CRUCIAL to prevent scope creep.**

### Design Agent DOES:
✅ Extract screen list from PRD
✅ Create ASCII UI mockups through conversation
✅ Provide 2-3 layout options (never dictate single solution)
✅ **Search and recommend open-source libraries during conversation** ⭐ NEW
✅ Define Design System (colors, typography, spacing)
✅ Generate 6 documentation files (including Open_Source_Recommendations_v0.9.md)
✅ Create Google AI Studio prompts
✅ Validate uploaded code (syntax, TypeScript, accessibility)

### Design Agent DOES NOT:
❌ Create user personas (Planning Agent territory)
❌ Map user journeys (Planning Agent territory)
❌ Discover pain points (Planning Agent territory)
❌ Break down epics/stories (Tech Spec Agent territory)
❌ Write production code (Development Agent territory)

**The Design Agent operates ONLY on the design layer.**

## ASCII UI Generation Rules

### Strict Format Requirements

**Width:**
- Mobile screens: 40 characters
- Web screens: 80 characters

**Syntax:**
```
Box drawing: ┌─┐│└┘
Buttons:     [Text]
Inputs:      [_____]
Icons:       emoji (📱 🔍 👤)
```

**Example Mobile Screen (40 chars):**
```
┌──────────────────────────────────────┐
│  📱 MyApp                    ☰       │
├──────────────────────────────────────┤
│                                      │
│  Welcome back!                       │
│                                      │
│  Email                               │
│  [___________________________]       │
│                                      │
│  Password                            │
│  [___________________________]       │
│                                      │
│         [    Sign In    ]            │
│                                      │
│  Forgot password?                    │
│                                      │
└──────────────────────────────────────┘
```

### BMAD Principles for ASCII UI

1. **Design Exploration:** Always provide 2-3 layout options per screen (never single answer)
2. **Collaborative Iteration:** Refine through conversation ("Move button to bottom" → show updated ASCII)
3. **Decision Documentation:** Record "why" for every design choice
4. **Quality Validation:** Check WCAG AA, minimum 48x48px touch targets, 4.5:1 contrast

## Open-Source Discovery System ⭐ NEW

### Real-Time Library Recommendations

During Phase 3 (Interactive ASCII UI refinement), the agent **automatically searches and recommends open-source libraries** when users mention specific features or components.

**Trigger Keywords:**
- Authentication: "login", "OAuth", "social login", "JWT"
- UI Components: "button", "modal", "dropdown", "table", "form"
- Icons: "icon", "svg", "emoji"
- Charts: "chart", "graph", "visualization"
- Animation: "animation", "transition", "motion"

**Search Sources:**
1. **GitHub API** - Repository search with filters (stars, license, language)
2. **npm Registry** - Package search with download stats
3. **Web Search** - Latest articles and trends (2025)
4. **Curated Lists** - awesome-react, awesome-vue, etc.

**Filtering Criteria:**
- ✅ MIT/Apache 2.0 license only
- ✅ Updated within last 12 months
- ✅ Minimum 500+ GitHub stars
- ✅ TypeScript support
- ✅ No security vulnerabilities
- ✅ Compatible with project tech stack

**Ranking Algorithm (0-100 score):**
- **Popularity (40%):** GitHub stars + npm downloads
- **Recency (20%):** Last update timestamp
- **Quality (20%):** TypeScript support, documentation, tests
- **Size (20%):** Bundle size (prefer <50KB)

**Presentation Format:**
```
🔍 Searching for "data table" libraries...

✅ 3 options found:

1. TanStack Table v8 ⭐ Recommended
   📦 GitHub: tanstack/table
   ⭐ Stars: 22,000+
   📄 License: MIT
   📏 Bundle: 15KB
   💡 Score: 95/100

   Headless UI, perfect for Tailwind customization

2. AG Grid Community
   [details...]

3. React Table v7
   [details...]

Which would you like? (1, 2, 3, or "skip")
```

**User Selection Flow:**
1. User picks option (e.g., "1")
2. Agent adds to state: `selected_open_source[]`
3. Confirmation message with install command
4. Automatically added to 3 documents:
   - `Open_Source_Recommendations_v0.9.md`
   - `Design_System_v0.9.md` (libraries section)
   - `Screen_Specifications_v0.9.md` (per screen)

**Non-Intrusive Design:**
- Always provide "skip" option
- Never blocks conversation flow
- Context-aware (checks tech stack compatibility)
- Learns from user preferences

**Example Interaction:**
```
User: "I need a date picker for the booking form"

Agent: [Updates ASCII UI with date picker]

🔍 Found 3 date picker libraries:

1. React DayPicker v8 ⭐
   - Lightweight (12KB)
   - Accessible
   - Customizable with Tailwind

2. [other options...]

User: "1"

Agent: ✅ React DayPicker v8 added!
       Installation: npm install react-day-picker
```

## LangGraph Node Structure

### 11 Core Nodes (Planned Implementation)

**Note:** LangGraph 1.0+ maintains full backward compatibility with 0.2.x designs, with enhanced functionality moved to appropriate modules.

1. `extract_screens` - Parse PRD for screen list
2. `generate_options` - Create 2-3 layout options per screen
3. `create_ascii_ui` - Generate ASCII mockups
4. `refine_design` - Process user feedback (loop with conditional edge)
5. `pause_for_google_ai` - Pause for manual design work
6. `receive_code` - Accept user-uploaded code
7. `validate_code` - Quality checks (syntax, TypeScript, accessibility)
8. `generate_design_system` - Extract Design System from approved designs
9. `generate_documents` - Create 5 documentation files (parallel)
10. `package_for_dev` - Package 6 documents + validated code for Tech Spec Agent handoff
11. `error_handler` - Handle validation failures and errors

### State Schema (Key Fields)

```python
class DesignAgentState(TypedDict):
    prd_content: str
    trd_content: str
    extracted_screens: List[str]
    design_options: Dict[str, List[str]]  # screen_name -> [option1, option2, option3]
    selected_designs: Dict[str, str]      # screen_name -> final_ascii_ui
    design_decisions: List[str]           # Decision log
    uploaded_code: Optional[str]
    validation_results: Dict[str, Any]
    design_system: Dict[str, Any]
    generated_documents: Dict[str, str]
```

## Six Output Documents ⭐ UPDATED

The system generates these documents automatically:

1. **Design_System_v0.9.md**
   - Color palette (Primary, Secondary, Semantic)
   - Typography system (fonts, sizes, weights)
   - Spacing system (8pt grid)
   - Border radius, shadows, icon style guide
   - **Open-source component libraries section** (new)

2. **UX_Flow_v0.9.md**
   - Screen sitemap and navigation flows
   - User actions → System responses
   - Edge cases (loading, error, empty, offline)

3. **Screen_Specifications_v0.9.md**
   - Final ASCII UI for each screen
   - Layout structure with measurements
   - Element details (sizes, colors, spacing)
   - Interaction specifications and state variations
   - Design decision logs
   - **Implementation libraries per screen** (new)

4. **Google_AI_Studio_Prompts_v0.9.md**
   - Screen-by-screen generation prompts
   - Visual style specifications
   - Expected outputs for manual design phase

5. **Design_Guidelines_v0.9.md**
   - Design philosophy
   - Accessibility standards (WCAG AA)
   - Responsive principles
   - Animation guidelines
   - Dark mode policy
   - **Open-source usage guidelines** (new)

6. **Open_Source_Recommendations_v0.9.md** ⭐ NEW
   - Category-based library recommendations (UI, Auth, Forms, Icons, etc.)
   - Detailed library information (GitHub stars, license, bundle size)
   - Selection rationale and decision logs
   - Installation scripts and dependency management
   - Version management guidelines

## Development Commands (When Implemented)

### Setup
```bash
pip install -r requirements.txt
# Create .env file from .env.example
```

### Run CLI Mode
```bash
python cli.py
# Interactive command-line interface
# Input: PRD.md and TRD.md files
# Output: 6 documents + validation report
```

### Run API Server
```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
# FastAPI server with WebSocket support
```

### Docker
```bash
docker-compose up -d
# Starts: design-agent, postgres, redis
```

### Testing
```bash
pytest tests/                          # All tests
pytest tests/test_ascii_generator.py   # Specific test file
pytest -k "test_screen_extraction"     # Specific test
```

### Kubernetes Deployment
```bash
kubectl apply -f k8s/deployment.yaml
```

## Code Quality Standards

### Automated Validation Checks

When validating uploaded code (Phase 5), enforce:

- ✅ Syntax checking (no errors)
- ✅ TypeScript type validation
- ✅ Tailwind CSS only (reject custom CSS)
- ✅ Design system compliance (colors, typography, spacing match)
- ✅ WCAG AA accessibility
- ✅ Responsive design checks
- ✅ Minimum touch target: 48x48px
- ✅ Color contrast ratio: 4.5:1

**Quality Score Target:** 90/100 minimum (auto-calculated)

## Key Documentation Files

When implementing features or debugging, reference these documents:

- **Design_Agent_Clean_Plan.md** (43KB) - Best overview of architecture and BMAD integration
- **Design_Agent_Implementation_Plan.md** (52KB) - Detailed technical specs, code examples
- **Design_Agent_Simulation.md** (32KB) - Full usage simulation and example outputs
- **Design_Agent_Manual_Workflow.md** (29KB) - Hybrid automation approach and Google AI Studio integration
- **Design_Agent_Manual_Workflow_Diagram.md** (38KB) - Visual workflow diagrams

## Typical User Journey (30-45 minutes) ⭐ UPDATED

1. **Input:** User provides `PRD.md` and `TRD.md`
2. **Phase 1 (2 min):** Extract 6-8 screens automatically
3. **Phase 2 (3 min):** Present 2-3 layout options per screen
4. **Phase 3 (10-12 min):** Interactive ASCII UI refinement **+ Open-Source Discovery**
   - User: "Move button to bottom"
   - Agent: [Shows updated ASCII UI]
   - User: "Add a data table with sorting"
   - Agent: **🔍 Searches open-source libraries → Suggests TanStack Table, AG Grid, etc.**
   - User: "1" (selects TanStack Table)
   - Agent: ✅ Added to documentation
   - Repeat until user approves each screen
5. **Phase 4 (2 min):** Extract Design System automatically from approved designs
6. **⏸ Pause (10-20 min):** User goes to Google AI Studio
   - Copy generated prompt
   - Create visual design
   - Upload code back to agent
7. **Phase 5 (2 min):** Validate code automatically (quality score)
8. **Phase 6 (3-4 min):** Generate 6 documents in parallel (including Open_Source_Recommendations_v0.9.md)
9. **Output:** Package handed to Tech Spec Agent
   - 6 documentation files
   - Validated code (from Google AI Studio)
   - Quality validation report

## Implementation Priority

When building this system, follow this order (from existing docs):

**Week 1-2:** Core Structure
- LangGraph basic setup with PostgreSQL checkpointer
- Phase 1-2 nodes (screen extraction, option generation)
- ASCII UI generation engine

**Week 3-4:** Interactive Design ⭐ (Most Complex)
- Phase 3 conversational refinement
- Feedback processing with conditional routing
- ASCII modification engine

**Week 5:** Documentation
- Phase 4 Design System extraction
- 5 parallel document generators
- Template system for consistency

**Week 6:** Integration
- ANYON Kanban API integration
- WebSocket real-time updates
- End-to-end testing with pytest

## ANYON Platform Integration

### Kanban Board Integration

```python
# POST /api/design/start
# Creates new ticket: "Design in Progress"

# WebSocket /ws/design/{project_id}
# Real-time updates: Phase changes, user feedback, completion

# POST /api/design/complete
# Updates ticket: "Design Complete" + attaches 6 documents + validated code
```

### Tech Spec Agent Handoff

**Package Contents:**
1. **6 Documentation Files:**
   - Design_System_v0.9.md
   - UX_Flow_v0.9.md
   - Screen_Specifications_v0.9.md
   - Google_AI_Studio_Prompts_v0.9.md
   - Design_Guidelines_v0.9.md
   - Open_Source_Recommendations_v0.9.md ⭐

2. **Validated Code:**
   - User-created design code (from Google AI Studio)
   - Passed all quality checks (90/100 minimum score)
   - TypeScript compliant
   - Tailwind CSS only
   - WCAG AA accessible
   - Design system compliant

3. **Validation Report:**
   - Quality score breakdown
   - Accessibility audit results
   - Design system compliance check
   - Performance metrics (bundle size, etc.)

**Tech Spec Agent Responsibilities:**
- Create API specifications based on Screen_Specifications
- Define data models from UX_Flow
- Design system architecture
- Create technical implementation guide using validated code as reference
- Integrate open-source library recommendations into tech stack

### External Services

- **Google AI Studio:** Manual design generation during pause phase
- **Anthropic Claude / OpenAI GPT:** LLM backend for agents
- **PostgreSQL:** State persistence across sessions
- **Redis:** Session caching and temporary storage

## Important Reminders for Implementation

1. **Always provide multiple options** - Never dictate a single design solution
2. **Record decision rationale** - Every design choice needs "why" documentation
3. **Strict Tailwind CSS only** - Reject any custom CSS during validation
4. **WCAG AA is non-negotiable** - Accessibility checks are mandatory
5. **Pause/resume must be reliable** - PostgreSQL checkpointer is critical
6. **State must be fully serializable** - No complex objects in LangGraph state
7. **Parallel document generation** - Use async/await for 5 documents
8. **Clear error messages** - User-friendly language for non-technical users

## Project Status

**Missing Infrastructure (Needs Creation):**
- [ ] README.md with setup instructions
- [ ] requirements.txt with all dependencies
- [ ] .env.example template
- [ ] pyproject.toml or setup.py
- [ ] .gitignore
- [ ] docker-compose.yml
- [ ] src/ directory structure
- [ ] tests/ directory with pytest setup
- [ ] docs/ directory for generated outputs

**Existing Documentation:**
- [x] Comprehensive architecture plans (5 detailed Markdown files)
- [x] BMAD methodology integration
- [x] LangGraph node specifications
- [x] Example simulations and outputs

---

*This repository is ready for implementation. All planning and architectural decisions are complete and well-documented.*
