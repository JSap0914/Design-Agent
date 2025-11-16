# Design Agent Implementation Plan - Database-Centric ANYON Integration

## 🎯 Overview
Build the Design Agent system with a **shared PostgreSQL database** architecture where:
- ANYON and Design Agent share the same database
- ANYON triggers jobs by inserting rows into a `design_jobs` table
- Design Agent listens via PostgreSQL LISTEN/NOTIFY for instant job pickup
- ANYON reads real-time progress, documents, and decisions directly from database
- Google AI Studio integration is optional (user chooses at Phase 4)

## 📊 Database Architecture

### Shared PostgreSQL Database: `anyon_db`

**Schema Structure:**
- `anyon_core` schema - ANYON's core tables (user, project, kanban)
- `design_agent` schema - Design Agent tables (sessions, checkpoints)
- `shared` schema - Integration tables (jobs, progress, outputs)

**Key Tables to Create:**

1. **`shared.design_jobs`** (Job Queue)
   - Columns: job_id, project_id, user_id, prd_content, trd_content, status, created_at, started_at, completed_at
   - ANYON inserts here to trigger Design Agent
   - Status: pending → running → completed/failed

2. **`shared.design_progress`** (Real-Time Status)
   - Columns: job_id, current_phase, phase_name, progress_percent, screen_count, completed_screens, estimated_time_remaining, last_updated
   - Updated every 5-10 seconds during active sessions
   - ANYON reads for live progress bars

3. **`shared.design_outputs`** (Generated Documents)
   - Columns: job_id, document_type, file_name, content, version, created_at
   - Stores all 6 markdown documents + validation reports
   - ANYON reads to display/download documents

4. **`shared.design_decisions`** (Decision Log)
   - Columns: decision_id, job_id, screen_name, decision_type, rationale, alternatives, timestamp
   - Audit trail of all design choices
   - Useful for understanding "why" decisions were made

5. **`design_agent.sessions`** (Session State)
   - Columns: session_id, job_id, langgraph_thread_id, state_snapshot, current_phase, pause_reason, created_at, updated_at
   - Internal session management
   - Links to LangGraph checkpoints

6. **`design_agent.checkpoints`** (LangGraph State)
   - Standard LangGraph checkpoint table
   - Enables pause/resume functionality

7. **`shared.open_source_selections`** (Library Recommendations)
   - Columns: selection_id, job_id, category, library_name, github_url, npm_url, stars, license, bundle_size, rationale, timestamp
   - Tracks selected open-source libraries

## 🏗️ Implementation Structure

### Directory Structure to Create:

```
design-agent/
├── README.md
├── requirements.txt
├── pyproject.toml
├── .env.example
├── .gitignore
├── docker-compose.yml
├── Dockerfile
├── alembic.ini
├── alembic/
│   └── versions/
├── src/
│   ├── __init__.py
│   ├── main.py                    # FastAPI app (optional API layer)
│   ├── config.py                  # Configuration management
│   ├── database/
│   │   ├── __init__.py
│   │   ├── connection.py          # PostgreSQL connection pool
│   │   ├── models.py              # SQLAlchemy models
│   │   └── migrations/            # Alembic migrations
│   ├── langgraph/
│   │   ├── __init__.py
│   │   ├── state.py               # DesignAgentState schema
│   │   ├── workflow.py            # 11-node state machine
│   │   ├── nodes/                 # Individual node implementations
│   │   │   ├── extract_screens.py
│   │   │   ├── generate_options.py
│   │   │   ├── create_ascii_ui.py
│   │   │   ├── refine_design.py
│   │   │   ├── pause_for_google_ai.py
│   │   │   ├── receive_code.py
│   │   │   ├── validate_code.py
│   │   │   ├── generate_design_system.py
│   │   │   ├── generate_documents.py
│   │   │   ├── package_for_dev.py
│   │   │   └── error_handler.py
│   │   └── checkpointer.py        # PostgreSQL checkpointer setup
│   ├── workers/
│   │   ├── __init__.py
│   │   ├── job_listener.py        # PostgreSQL LISTEN for new jobs
│   │   ├── job_processor.py       # Execute LangGraph workflows
│   │   └── progress_updater.py    # Update progress table
│   ├── generators/
│   │   ├── __init__.py
│   │   ├── ascii_ui.py            # ASCII UI generation engine
│   │   ├── design_system.py       # Design System extraction
│   │   ├── documents.py           # 6 document generators
│   │   └── templates/             # Markdown templates
│   ├── validators/
│   │   ├── __init__.py
│   │   ├── code_validator.py      # Syntax, TypeScript, Tailwind checks
│   │   ├── accessibility.py       # WCAG AA validation
│   │   └── quality_score.py       # 0-100 scoring algorithm
│   ├── opensearch/
│   │   ├── __init__.py
│   │   ├── searcher.py            # Multi-source search (GitHub, npm, web)
│   │   ├── ranker.py              # 0-100 ranking algorithm
│   │   ├── filter.py              # License, recency, stars filtering
│   │   └── cache.py               # Redis caching for search results
│   ├── llm/
│   │   ├── __init__.py
│   │   ├── client.py              # Claude Sonnet 4.5 client
│   │   └── prompts.py             # System prompts for each node
│   └── utils/
│       ├── __init__.py
│       ├── bmad.py                # BMAD methodology helpers
│       └── logger.py              # Structured logging
├── tests/
│   ├── __init__.py
│   ├── conftest.py                # Pytest fixtures
│   ├── test_workflow.py
│   ├── test_nodes/
│   ├── test_validators/
│   └── test_opensearch/
└── docs/
    └── generated_outputs/         # Example outputs
```

## 🔧 Implementation Phases (8 Weeks)

### **Week 1: Foundation + Database**
**Goal:** Database schema, connection management, job listening system

Tasks:
1. Create directory structure
2. Setup requirements.txt (FastAPI 0.121+, LangGraph 1.0+, anthropic, psycopg2, redis, pydantic 2.10+)
3. Create .env.example (DATABASE_URL, ANTHROPIC_API_KEY, REDIS_URL)
4. Design database schema (7 tables)
5. Create Alembic migrations
6. Implement database connection pool (asyncpg for async)
7. Create SQLAlchemy models for all tables
8. Implement PostgreSQL LISTEN/NOTIFY job listener
9. Write basic job processor (shell only)
10. Test database trigger flow: ANYON inserts → Design Agent picks up job

**Deliverable:** Database schema live, job listener working

### **Week 2: LangGraph Core + Phases 1-2**
**Goal:** State machine setup, screen extraction, layout options

Tasks:
1. Define `DesignAgentState` TypedDict schema
2. Setup PostgreSQL checkpointer for LangGraph
3. Implement `extract_screens` node (parse PRD for screens)
4. Implement `generate_options` node (2-3 layout options per screen)
5. Create LLM client wrapper (Claude Sonnet 4.5)
6. Write system prompts for Phases 1-2
7. Create workflow.py with conditional routing
8. Test Phase 1-2 end-to-end
9. Update `design_progress` table in real-time
10. Add error handling and logging

**Deliverable:** Phases 1-2 working, can extract screens and generate options

### **Week 3: ASCII UI Engine + Phase 3**
**Goal:** Interactive ASCII UI generation and refinement

Tasks:
1. Implement ASCII UI generator (40-char mobile, 80-char web)
2. Create `create_ascii_ui` node
3. Implement `refine_design` node with loop logic
4. Build feedback processing system
5. Implement ASCII modification engine (update based on user input)
6. Add conditional edge: "continue refining" vs "approve screen"
7. Test conversational refinement flow
8. Update progress table with screen completion
9. Implement BMAD principles (2-3 options, decision logging)
10. WebSocket integration for real-time UI updates (optional)

**Deliverable:** Phase 3 working, users can refine ASCII UIs conversationally

### **Week 4: Open-Source Discovery System**
**Goal:** Real-time library recommendations during Phase 3

Tasks:
1. Implement GitHub API search integration
2. Implement npm Registry API search
3. Implement web search API (Google Custom Search or Brave)
4. Create filtering logic (license, recency, stars, TypeScript)
5. Implement ranking algorithm (popularity 40%, recency 20%, quality 20%, size 20%)
6. Build user selection workflow
7. Add keyword trigger detection in refine_design node
8. Integrate with Redis cache (15-min TTL)
9. Store selections in `open_source_selections` table
10. Test end-to-end library recommendation flow

**Deliverable:** Open-source discovery working, selections stored in DB

### **Week 5: Pause/Resume + Validation (Phases 4-5)**
**Goal:** Optional Google AI Studio pause, code validation

Tasks:
1. Implement `pause_for_google_ai` node (ask user choice)
2. Create "skip" path directly to Phase 6
3. Implement `receive_code` node (accept uploaded code)
4. Build code validator (syntax, TypeScript, Tailwind CSS only)
5. Implement accessibility validator (WCAG AA checks)
6. Create quality scoring algorithm (0-100)
7. Implement `validate_code` node
8. Test pause → resume flow with PostgreSQL checkpointer
9. Store validation results in `design_outputs` table
10. Add error handling for failed validations

**Deliverable:** Phases 4-5 working, optional pause/resume functional

### **Week 6: Document Generation (Phase 6)**
**Goal:** Generate 6 markdown documents in parallel

Tasks:
1. Implement `generate_design_system` node (extract from approved designs)
2. Create 6 document generator functions (async):
   - Design_System_v0.9.md
   - UX_Flow_v0.9.md
   - Screen_Specifications_v0.9.md
   - Google_AI_Studio_Prompts_v0.9.md
   - Design_Guidelines_v0.9.md
   - Open_Source_Recommendations_v0.9.md
3. Build markdown template system
4. Implement parallel execution with asyncio.gather()
5. Implement `generate_documents` node
6. Store all documents in `design_outputs` table
7. Implement `package_for_dev` node (prepare handoff)
8. Test Phase 6 end-to-end
9. Measure performance (target: 3-4 minutes for all 6 docs)
10. Add document versioning support

**Deliverable:** Phase 6 working, 6 documents generated in parallel

### **Week 7: ANYON Integration + Testing**
**Goal:** Complete ANYON integration, end-to-end testing

Tasks:
1. Create database views for ANYON read access
2. Test ANYON → Design Agent trigger flow
3. Test Design Agent → ANYON data access (progress, documents, decisions)
4. Implement session history tracking
5. Add analytics queries for ANYON dashboard
6. Write comprehensive unit tests (pytest)
7. Write integration tests for each phase
8. Test complete workflow with real PRD examples
9. Load testing (simulate multiple concurrent jobs)
10. Fix bugs and edge cases

**Deliverable:** Full ANYON integration working, comprehensive test suite

### **Week 8: Polish + Deployment**
**Goal:** Production-ready code, Docker deployment

Tasks:
1. Code quality improvements (type hints, docstrings)
2. Performance optimization (query optimization, caching)
3. Create Dockerfile for Design Agent worker
4. Create docker-compose.yml (design-agent, postgres, redis)
5. Write comprehensive README.md
6. Create setup instructions
7. Add monitoring (Prometheus metrics)
8. Implement graceful shutdown
9. Final end-to-end testing
10. Deployment to staging environment

**Deliverable:** Production-ready Design Agent, deployed to staging

## 🔑 Key Technical Decisions

### PostgreSQL LISTEN/NOTIFY for Job Triggering

```python
# ANYON triggers job (inserts row)
INSERT INTO shared.design_jobs (project_id, user_id, prd_content, trd_content, status)
VALUES ('proj-123', 'user-456', '...PRD...', '...TRD...', 'pending');

# Automatic trigger sends notification
CREATE TRIGGER notify_new_job
AFTER INSERT ON shared.design_jobs
FOR EACH ROW EXECUTE FUNCTION notify_new_job_func();

# Design Agent listens
LISTEN new_design_job;

# Instant pickup (no polling needed!)
```

### Database Schema Isolation

- **anyon_core schema:** ANYON owns, Design Agent has read-only access
- **design_agent schema:** Design Agent owns, ANYON has no access (internal)
- **shared schema:** Both have read/write access, integration layer

### Progress Update Frequency

- Real-time events: Phase changes, screen completions
- Periodic updates: Progress percentage every 5-10 seconds
- Bulk updates: Document generation completion

### Optional Pause Implementation

```python
# At end of Phase 4, ask user
if user_choice == "pause_for_google_ai":
    # Save state to checkpointer
    # Update job status: "paused_waiting_for_upload"
    # ANYON shows "Waiting for Design Upload" badge
    # User uploads code → job resumes
elif user_choice == "skip_to_documents":
    # Go directly to Phase 6
    # uploaded_code = None
    # validation_results = None
```

## 📦 Key Dependencies

```txt
# Core
fastapi>=0.121.0
uvicorn[standard]>=0.27.0
pydantic>=2.10.0
pydantic-settings>=2.7.0

# LangGraph
langgraph>=1.0.3
langchain>=1.0.0
langchain-anthropic>=0.4.0

# Database
asyncpg>=0.30.0
psycopg2-binary>=2.9.10
sqlalchemy>=2.0.36
alembic>=1.14.0

# LLM
anthropic>=0.40.0

# Cache
redis>=5.2.0

# Utils
httpx>=0.28.0
beautifulsoup4>=4.12.3
python-dotenv>=1.0.1
```

## 🎯 Success Criteria

✅ ANYON can trigger Design Agent by inserting database row
✅ Design Agent picks up jobs within 1 second (LISTEN/NOTIFY)
✅ Real-time progress visible to ANYON (updated every 5-10s)
✅ All 6 documents stored in database and accessible to ANYON
✅ Decision log captured for audit trails
✅ Optional Google AI Studio pause/resume works
✅ Open-source library recommendations integrated
✅ Complete workflow executes in 30-45 minutes
✅ Quality score 90/100 minimum for validated code
✅ PostgreSQL checkpointer enables reliable pause/resume
✅ Session history queryable by ANYON for analytics

## 🚀 Next Steps After Implementation

1. Create comprehensive API documentation (OpenAPI/Swagger)
2. Build Kubernetes deployment manifests
3. Setup CI/CD pipeline (GitHub Actions)
4. Implement monitoring dashboards (Grafana)
5. Add LangSmith tracing for LLM debugging
6. Scale horizontally (multiple worker instances)
7. Add rate limiting and quota management
8. Implement webhook notifications for job completion

---

**Total Estimated Timeline:** 8 weeks for full implementation
**Team Size:** 1-2 developers
**Technology Stack:** Python 3.11+, FastAPI, LangGraph, PostgreSQL, Redis, Claude Sonnet 4.5
