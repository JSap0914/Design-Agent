# ANYON Design Agent

AI-powered design automation system that bridges the gap between product planning (PRD/TRD) and development by creating interactive ASCII-based UI designs and generating comprehensive design documentation.

## Overview

The Design Agent is a **database-centric AI system** that integrates seamlessly with the ANYON platform through a shared PostgreSQL database. It transforms product requirements into complete design specifications through a hybrid workflow combining LangGraph automation with optional human creativity.

### Key Features

- **6-Phase Hybrid Workflow**: Automated design generation with optional manual refinement
- **LangGraph State Machine**: 11-node orchestration with PostgreSQL checkpointer for pause/resume
- **Interactive ASCII UI**: Conversational refinement of mockups (40-char mobile, 80-char web)
- **Open-Source Discovery**: Real-time library recommendations during design conversations
- **Database-Centric Integration**: ANYON triggers jobs via database inserts, reads progress in real-time
- **BMAD Methodology**: Always provides 2-3 design options, never dictates single solution
- **Quality Validation**: WCAG AA accessibility, Tailwind CSS compliance, 90/100 minimum score
- **6 Documentation Outputs**: Design System, UX Flow, Screen Specs, AI Prompts, Guidelines, Open-Source Recommendations

## Architecture

### Workflow Overview

```
Phase 1-4: Automated (LangGraph)
    ↓ Screen extraction → Design options → ASCII UI dialogue → Design System
⏸ OPTIONAL: Human intervention (Google AI Studio)
    ↓ User creates actual designs manually
▶ RESUME: Automated (LangGraph)
    ↓ Code validation → Document generation → Packaging
```

### Database Integration

**Shared PostgreSQL Database: `anyon_db`**

- **ANYON triggers** jobs by inserting into `shared.design_jobs` table
- **Design Agent listens** via PostgreSQL LISTEN/NOTIFY (instant pickup, no polling)
- **ANYON reads** real-time progress from `shared.design_progress` table
- **Generated documents** stored in `shared.design_outputs` table
- **Design decisions** logged in `shared.design_decisions` table

### Technology Stack

**Backend (Python 3.11+, Python 3.13 recommended)**
- FastAPI 0.121+ (async web framework)
- LangGraph 1.0+ (state machine orchestration)
- Anthropic Claude Sonnet 4.5 (claude-sonnet-4-5-20250929)
- PostgreSQL (state persistence + shared data)
- Redis (caching for open-source search)
- asyncpg (async database driver)

**Key Libraries**
- LangChain 1.0+ (LLM orchestration)
- SQLAlchemy 2.0+ (ORM)
- Alembic 1.14+ (database migrations)
- Pydantic 2.10+ (data validation)

## Installation

### Prerequisites

- Python 3.11+ (Python 3.13 recommended)
- PostgreSQL 14+
- Redis 7+
- Anthropic API key (for Claude Sonnet 4.5)

### Setup Steps

1. **Clone the repository**
   ```bash
   cd "path/to/design-agent"
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv

   # Windows
   venv\Scripts\activate

   # Linux/Mac
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

5. **Run database migrations**
   ```bash
   alembic upgrade head
   ```

6. **Start Redis (if not running)**
   ```bash
   redis-server
   ```

7. **Start the Design Agent worker**
   ```bash
   python -m src.workers.job_listener
   ```

## Usage

### Triggering a Design Job (ANYON Side)

```sql
-- ANYON inserts a row to trigger Design Agent
INSERT INTO shared.design_jobs (
    project_id,
    user_id,
    prd_content,
    trd_content,
    status
) VALUES (
    'proj-12345',
    'user-67890',
    '...PRD content...',
    '...TRD content...',
    'pending'
);

-- Design Agent picks up job instantly via LISTEN/NOTIFY
```

### Monitoring Progress (ANYON Side)

```sql
-- Get real-time progress
SELECT
    current_phase,
    phase_name,
    progress_percent,
    screen_count,
    completed_screens,
    estimated_time_remaining
FROM shared.design_progress
WHERE job_id = 'job-12345';

-- Get generated documents
SELECT
    document_type,
    file_name,
    content,
    created_at
FROM shared.design_outputs
WHERE job_id = 'job-12345'
ORDER BY created_at DESC;

-- Get design decisions
SELECT
    screen_name,
    decision_type,
    rationale,
    alternatives,
    timestamp
FROM shared.design_decisions
WHERE job_id = 'job-12345'
ORDER BY timestamp;
```

### Complete Workflow (30-45 minutes)

1. **Input**: ANYON provides PRD.md and TRD.md
2. **Phase 1 (2 min)**: Extract 6-8 screens automatically
3. **Phase 2 (3 min)**: Present 2-3 layout options per screen
4. **Phase 3 (10-12 min)**: Interactive ASCII UI refinement + Open-Source Discovery
5. **Phase 4 (2 min)**: Extract Design System from approved designs
6. **⏸ Optional Pause (10-30 min)**: User creates designs in Google AI Studio
7. **Phase 5 (2 min)**: Validate uploaded code (quality score)
8. **Phase 6 (3-4 min)**: Generate 6 documents in parallel
9. **Output**: 6 documentation files + validated code + validation report

## Development

### Project Structure

```
design-agent/
├── src/
│   ├── database/           # PostgreSQL connection, models, migrations
│   ├── langgraph/          # 11-node state machine
│   │   └── nodes/          # Individual node implementations
│   ├── workers/            # Job listener, processor, progress updater
│   ├── generators/         # ASCII UI, Design System, Documents
│   │   └── templates/      # Markdown templates
│   ├── validators/         # Code, accessibility, quality score
│   ├── opensearch/         # Library recommendations (GitHub, npm, web)
│   ├── llm/                # Claude client, prompts
│   └── utils/              # BMAD helpers, logging
├── tests/                  # Comprehensive test suite
├── alembic/                # Database migrations
└── docs/                   # Documentation
```

### Running Tests

```bash
# All tests
pytest tests/

# Specific test file
pytest tests/test_workflow.py

# Specific test
pytest -k "test_screen_extraction"

# With coverage
pytest --cov=src tests/
```

### Database Migrations

```bash
# Create new migration
alembic revision -m "description"

# Apply migrations
alembic upgrade head

# Rollback one migration
alembic downgrade -1

# View migration history
alembic history
```

### Code Quality

```bash
# Type checking
mypy src/

# Linting
ruff check src/

# Formatting
black src/
```

## Configuration

### Environment Variables

See `.env.example` for all configuration options:

- `DATABASE_URL`: PostgreSQL connection string
- `REDIS_URL`: Redis connection string
- `ANTHROPIC_API_KEY`: Claude API key
- `OPENAI_API_KEY`: GPT-4 fallback API key (optional)
- `GITHUB_TOKEN`: GitHub API token for open-source search
- `LOG_LEVEL`: Logging level (DEBUG, INFO, WARNING, ERROR)

### Database Schema

The system uses 7 main tables across 3 schemas:

**Shared Schema (Integration Layer)**
- `shared.design_jobs` - Job queue for triggering Design Agent
- `shared.design_progress` - Real-time status updates
- `shared.design_outputs` - Generated documents
- `shared.design_decisions` - Design choice audit trail
- `shared.open_source_selections` - Selected libraries

**Design Agent Schema (Internal)**
- `design_agent.sessions` - Session state management
- `design_agent.checkpoints` - LangGraph state snapshots

## Output Documents

The Design Agent generates 6 comprehensive markdown documents:

1. **Design_System_v0.9.md** - Colors, typography, spacing, libraries
2. **UX_Flow_v0.9.md** - Screen sitemap, navigation, edge cases
3. **Screen_Specifications_v0.9.md** - ASCII UI, layouts, interactions, decisions
4. **Google_AI_Studio_Prompts_v0.9.md** - Prompts for manual design generation
5. **Design_Guidelines_v0.9.md** - Philosophy, accessibility, responsive principles
6. **Open_Source_Recommendations_v0.9.md** - Library selections, rationale, installation

## Contributing

### Development Workflow

1. Create feature branch from `main`
2. Implement changes with tests
3. Ensure all tests pass: `pytest tests/`
4. Run type checking: `mypy src/`
5. Format code: `black src/`
6. Submit pull request

### Code Standards

- **Type Hints**: All functions must have complete type hints
- **Docstrings**: Use Google-style docstrings
- **Testing**: Minimum 80% code coverage
- **BMAD Principles**: Always provide multiple design options
- **Accessibility**: WCAG AA is non-negotiable

## BMAD Methodology

The Design Agent follows **BMAD (Better Managed Automated Design)** principles:

1. **Design Exploration**: Always provide 2-3 layout options per screen (never single answer)
2. **Collaborative Iteration**: Refine through conversation ("Move button to bottom" → show updated ASCII)
3. **Decision Documentation**: Record "why" for every design choice
4. **Quality Validation**: WCAG AA, 48x48px touch targets, 4.5:1 contrast ratios

## Role Boundaries

**Design Agent DOES:**
- ✅ Extract screen list from PRD
- ✅ Create ASCII UI mockups through conversation
- ✅ Provide 2-3 layout options (never dictate single solution)
- ✅ Search and recommend open-source libraries
- ✅ Define Design System
- ✅ Generate 6 documentation files
- ✅ Validate uploaded code

**Design Agent DOES NOT:**
- ❌ Create user personas (Planning Agent territory)
- ❌ Map user journeys (Planning Agent territory)
- ❌ Break down epics/stories (Tech Spec Agent territory)
- ❌ Write production code (Development Agent territory)

## License

[To be determined]

## Support

For issues, questions, or contributions, please contact the ANYON platform team.

---

**Status**: Week 1 Implementation - Foundation Phase

**Last Updated**: 2025-01-13
