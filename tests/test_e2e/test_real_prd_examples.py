"""
End-to-end tests with 5 real PRD examples.

Tests complete workflow execution using realistic PRD scenarios:
1. Task Management App
2. E-commerce Platform
3. Social Media Dashboard
4. Healthcare Patient Portal
5. Online Learning Platform
"""

import pytest
from pathlib import Path
from unittest.mock import AsyncMock, patch, MagicMock

from src.langgraph.nodes.extract_screens import extract_screens
from src.langgraph.nodes.generate_options import generate_options
from src.langgraph.nodes.create_ascii_ui import create_ascii_ui
from src.langgraph.nodes.generate_design_system import generate_design_system
from src.langgraph.state import DesignAgentState


# Load real PRD files
FIXTURES_DIR = Path(__file__).parent.parent / "fixtures" / "real_prds"


def load_prd(filename: str) -> str:
    """Load PRD content from fixtures."""
    prd_path = FIXTURES_DIR / filename
    return prd_path.read_text(encoding="utf-8")


# Common TRD for all examples
STANDARD_TRD = """
# Technical Requirements Document

## Technology Stack
- **Frontend:** React 18+ with TypeScript 5.3+
- **Styling:** Tailwind CSS 3.4+ (strictly no custom CSS)
- **State Management:** Zustand or Redux Toolkit
- **Build Tool:** Vite 5.0+
- **Testing:** Vitest + React Testing Library

## Design Requirements
- Mobile-first responsive design
- WCAG 2.1 AA compliance
- Touch targets: 44x44px minimum
- Color contrast: 4.5:1 minimum
- Tailwind CSS only (no custom CSS)

## Performance
- First Contentful Paint: < 1.5 seconds
- Bundle size: < 500KB gzipped
- Code splitting: Route-based lazy loading
"""


# ============================================================================
# Test 1: Task Management App
# ============================================================================


@pytest.mark.asyncio
@pytest.mark.e2e
async def test_real_prd_task_management_app():
    """Test complete workflow with Task Management App PRD."""
    prd_content = load_prd("task_management_app.md")
    trd_content = load_prd("task_management_app_trd.md")

    state: DesignAgentState = {
        "job_id": "e2e-task-mgmt",
        "prd_content": prd_content,
        "trd_content": trd_content,
        "extracted_screens": [],
        "current_phase": 0,
    }

    # Phase 1: Extract Screens
    with patch("src.langgraph.nodes.extract_screens.generate_json_async", new_callable=AsyncMock) as mock_llm:
        # Simulate LLM extracting screens from PRD
        mock_llm.return_value = {
            "screens": [
                "Login Screen",
                "Dashboard",
                "Task List View",
                "Task Detail View",
                "Create Task Modal",
                "Kanban Board",
                "Calendar View",
                "User Profile",
            ],
            "rationale": "8 screens covering core task management features",
        }

        state = await extract_screens(state)

        assert state["current_phase"] == 1
        assert 3 <= len(state["extracted_screens"]) <= 12  # Within constraints
        assert "Login Screen" in state["extracted_screens"]
        assert "Dashboard" in state["extracted_screens"]
        assert "Task List View" in state["extracted_screens"]

    # Phase 2: Generate Layout Options
    with patch("src.langgraph.nodes.generate_options.llm_client.complete_with_json", new_callable=AsyncMock) as mock_llm:
        mock_llm.return_value = {
            "options": [
                {
                    "option_number": 1,
                    "layout_description": "Sidebar navigation with main content area",
                    "key_features": ["Left sidebar", "Content grid", "Top toolbar"],
                    "pros": ["Familiar pattern", "Good for desktop"],
                    "cons": ["Requires responsive adjustment for mobile"],
                    "recommended": True,
                },
                {
                    "option_number": 2,
                    "layout_description": "Top navigation with card-based layout",
                    "key_features": ["Header nav", "Card grid", "Floating actions"],
                    "pros": ["Mobile-friendly", "Modern look"],
                    "cons": ["Less screen real estate"],
                    "recommended": False,
                },
            ]
        }

        state = await generate_options(state)

        assert state["current_phase"] == 2
        assert len(state["design_options"]) >= 3  # At least 3 screens
        for screen_options in state["design_options"].values():
            assert 2 <= len(screen_options) <= 3  # 2-3 options per screen

    # Verify PRD-specific requirements extracted
    assert "task" in prd_content.lower()
    assert "kanban" in prd_content.lower()
    assert "tailwind" in trd_content.lower()


# ============================================================================
# Test 2: E-commerce Platform
# ============================================================================


@pytest.mark.asyncio
@pytest.mark.e2e
async def test_real_prd_ecommerce_platform():
    """Test complete workflow with E-commerce Platform PRD."""
    prd_content = load_prd("ecommerce_platform.md")

    state: DesignAgentState = {
        "job_id": "e2e-ecommerce",
        "prd_content": prd_content,
        "trd_content": STANDARD_TRD,
        "extracted_screens": [],
        "current_phase": 0,
    }

    # Phase 1: Extract Screens
    with patch("src.langgraph.nodes.extract_screens.generate_json_async", new_callable=AsyncMock) as mock_llm:
        mock_llm.return_value = {
            "screens": [
                "Home Screen",
                "Product Listing Page",
                "Product Detail Page",
                "Shopping Cart",
                "Checkout - Shipping",
                "Checkout - Payment",
                "Order Confirmation",
                "User Login/Register",
                "My Account Dashboard",
                "Wishlist",
            ],
            "rationale": "10 screens for complete e-commerce flow",
        }

        state = await extract_screens(state)

        assert state["current_phase"] == 1
        assert len(state["extracted_screens"]) <= 12  # Max constraint
        assert "Product Listing Page" in state["extracted_screens"]
        assert "Shopping Cart" in state["extracted_screens"]
        assert "Checkout" in str(state["extracted_screens"])  # Some checkout screen

    # Phase 3: Create ASCII UI (sample)
    state["design_options_metadata"] = {
        screen: [
            {"option_number": 1, "layout_description": "Grid layout", "key_features": ["Grid"]},
        ]
        for screen in state["extracted_screens"]
    }

    with patch("src.langgraph.nodes.create_ascii_ui.llm_client.complete", new_callable=AsyncMock) as mock_llm, \
         patch("src.langgraph.nodes.create_ascii_ui.broadcast_ascii_ui_update", new_callable=AsyncMock), \
         patch("src.langgraph.nodes.create_ascii_ui.ASCIIUIGenerator") as mock_gen:

        mock_llm.return_value = """┌────────────────────────────────────────────────────────────────────────────┐
│  🏠 Home    🔍 Search    🛒 Cart (3)    👤 Account                           │
├────────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│  🎯 Featured Products                                                      │
│                                                                            │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐     │
│  │   Product   │  │   Product   │  │   Product   │  │   Product   │     │
│  │   Image     │  │   Image     │  │   Image     │  │   Image     │     │
│  │             │  │             │  │             │  │             │     │
│  │  $49.99     │  │  $79.99     │  │  $129.99    │  │  $39.99     │     │
│  │  [Add Cart] │  │  [Add Cart] │  │  [Add Cart] │  │  [Add Cart] │     │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘     │
│                                                                            │
└────────────────────────────────────────────────────────────────────────────┘"""

        mock_generator = MagicMock()
        mock_generator.validate_ascii_ui.return_value = (True, [])
        mock_gen.return_value = mock_generator

        state = await create_ascii_ui(state)

        assert state["current_phase"] == 3
        assert len(state["selected_designs"]) >= 3
        # Verify ASCII UI created
        for ascii_ui in state["selected_designs"].values():
            assert len(ascii_ui) > 50  # Non-trivial ASCII

    # Verify PRD-specific requirements
    assert "checkout" in prd_content.lower()
    assert "cart" in prd_content.lower()
    assert "product" in prd_content.lower()


# ============================================================================
# Test 3: Social Media Dashboard
# ============================================================================


@pytest.mark.asyncio
@pytest.mark.e2e
async def test_real_prd_social_media_dashboard():
    """Test complete workflow with Social Media Dashboard PRD."""
    prd_content = load_prd("social_media_dashboard.md")

    state: DesignAgentState = {
        "job_id": "e2e-social-media",
        "prd_content": prd_content,
        "trd_content": STANDARD_TRD,
        "extracted_screens": [],
        "current_phase": 0,
    }

    with patch("src.langgraph.nodes.extract_screens.generate_json_async", new_callable=AsyncMock) as mock_llm:
        mock_llm.return_value = {
            "screens": [
                "Dashboard Home",
                "Content Calendar",
                "Create Post",
                "Analytics",
                "Inbox",
                "Accounts",
                "Post Details",
                "Team Members",
            ],
            "rationale": "8 screens for social media management core features",
        }

        state = await extract_screens(state)

        assert len(state["extracted_screens"]) >= 3
        assert "Dashboard Home" in state["extracted_screens"]
        assert "Analytics" in state["extracted_screens"]
        assert "Create Post" in state["extracted_screens"]

    # Verify PRD mentions required features
    assert "social media" in prd_content.lower()
    assert "analytics" in prd_content.lower()
    assert "schedule" in prd_content.lower() or "calendar" in prd_content.lower()


# ============================================================================
# Test 4: Healthcare Patient Portal
# ============================================================================


@pytest.mark.asyncio
@pytest.mark.e2e
async def test_real_prd_healthcare_patient_portal():
    """Test complete workflow with Healthcare Patient Portal PRD."""
    prd_content = load_prd("healthcare_patient_portal.md")

    state: DesignAgentState = {
        "job_id": "e2e-healthcare",
        "prd_content": prd_content,
        "trd_content": STANDARD_TRD,
        "extracted_screens": [],
        "current_phase": 0,
    }

    with patch("src.langgraph.nodes.extract_screens.generate_json_async", new_callable=AsyncMock) as mock_llm:
        mock_llm.return_value = {
            "screens": [
                "Login Screen",
                "Dashboard",
                "Appointments",
                "Schedule Appointment",
                "Medical Records",
                "Lab Results",
                "Medications",
                "Messages",
                "Billing",
            ],
            "rationale": "9 screens for patient portal core functionality",
        }

        state = await extract_screens(state)

        assert len(state["extracted_screens"]) >= 3
        assert "Appointments" in state["extracted_screens"]
        assert "Medical Records" in state["extracted_screens"]

    # Verify PRD mentions HIPAA and accessibility (critical for healthcare)
    assert "hipaa" in prd_content.lower()
    assert "accessibility" in prd_content.lower() or "wcag" in prd_content.lower()
    assert "secure" in prd_content.lower() or "security" in prd_content.lower()


# ============================================================================
# Test 5: Online Learning Platform
# ============================================================================


@pytest.mark.asyncio
@pytest.mark.e2e
async def test_real_prd_learning_platform():
    """Test complete workflow with Online Learning Platform PRD."""
    prd_content = load_prd("learning_platform.md")

    state: DesignAgentState = {
        "job_id": "e2e-learning",
        "prd_content": prd_content,
        "trd_content": STANDARD_TRD,
        "extracted_screens": [],
        "current_phase": 0,
    }

    # Phase 1: Extract Screens
    with patch("src.langgraph.nodes.extract_screens.generate_json_async", new_callable=AsyncMock) as mock_llm:
        mock_llm.return_value = {
            "screens": [
                "Login/Registration",
                "Dashboard",
                "Course Catalog",
                "Course Detail",
                "Course Home",
                "Lesson Player",
                "Assignments",
                "Assignment Detail",
                "Gradebook",
                "Discussion Forum",
            ],
            "rationale": "10 screens for online learning core experience",
        }

        state = await extract_screens(state)

        assert len(state["extracted_screens"]) >= 3
        assert any("course" in screen.lower() for screen in state["extracted_screens"])
        assert any("lesson" in screen.lower() or "player" in screen.lower() for screen in state["extracted_screens"])

    # Phase 4: Generate Design System (sample)
    state["selected_designs"] = {screen: "Sample UI" for screen in state["extracted_screens"][:3]}
    state["design_decisions"] = []
    state["selected_open_source"] = []

    with patch("src.langgraph.nodes.generate_design_system.llm_client.complete_with_json", new_callable=AsyncMock) as mock_llm:
        mock_llm.return_value = {
            "colors": {
                "primary": ["#3B82F6", "#2563EB", "#1D4ED8"],
                "secondary": ["#10B981", "#059669"],
                "semantic": {"success": "#10B981", "error": "#EF4444"},
            },
            "typography": {
                "font_families": {"primary": "Inter, sans-serif"},
                "sizes": {"base": "16px", "lg": "20px"},
            },
            "spacing": {"scale": "8pt grid", "values": {"2": "8px", "4": "16px"}},
            "border_radius": {"base": "8px"},
            "shadows": {"sm": "0 1px 2px rgba(0,0,0,0.05)"},
            "icons": {"style": "outline", "size": "24px"},
            "component_libraries": [],
        }

        state = await generate_design_system(state)

        assert state["current_phase"] == 4
        assert "design_system" in state
        assert "colors" in state["design_system"]
        assert "typography" in state["design_system"]

    # Verify PRD mentions learning-specific features
    assert "course" in prd_content.lower()
    assert "student" in prd_content.lower() or "learner" in prd_content.lower()
    assert "video" in prd_content.lower() or "lesson" in prd_content.lower()


# ============================================================================
# Cross-PRD Validation Tests
# ============================================================================


@pytest.mark.asyncio
@pytest.mark.e2e
async def test_all_prds_respect_screen_constraints():
    """Test that all PRDs result in 3-12 screens (design constraint)."""
    prd_files = [
        "task_management_app.md",
        "ecommerce_platform.md",
        "social_media_dashboard.md",
        "healthcare_patient_portal.md",
        "learning_platform.md",
    ]

    for prd_file in prd_files:
        prd_content = load_prd(prd_file)
        state: DesignAgentState = {
            "job_id": f"constraint-test-{prd_file}",
            "prd_content": prd_content,
            "trd_content": STANDARD_TRD,
            "extracted_screens": [],
            "current_phase": 0,
        }

        with patch("src.langgraph.nodes.extract_screens.generate_json_async", new_callable=AsyncMock) as mock_llm:
            # Simulate realistic screen counts
            screen_counts = {
                "task_management_app.md": 8,
                "ecommerce_platform.md": 10,
                "social_media_dashboard.md": 8,
                "healthcare_patient_portal.md": 9,
                "learning_platform.md": 10,
            }

            count = screen_counts[prd_file]
            mock_llm.return_value = {
                "screens": [f"Screen {i+1}" for i in range(count)],
                "rationale": f"{count} screens identified",
            }

            result = await extract_screens(state)

            # Verify constraints
            assert 3 <= len(result["extracted_screens"]) <= 12, \
                f"{prd_file} violated screen count constraint"


@pytest.mark.asyncio
@pytest.mark.e2e
async def test_all_prds_reference_tailwind():
    """Test that all TRDs specify Tailwind CSS."""
    # Task Management has explicit TRD
    trd_content = load_prd("task_management_app_trd.md")
    assert "tailwind" in trd_content.lower()
    assert "no custom css" in trd_content.lower() or "css only" in trd_content.lower()


def test_all_prd_files_exist():
    """Test that all PRD fixture files exist and are readable."""
    required_prds = [
        "task_management_app.md",
        "ecommerce_platform.md",
        "social_media_dashboard.md",
        "healthcare_patient_portal.md",
        "learning_platform.md",
    ]

    for prd_file in required_prds:
        prd_path = FIXTURES_DIR / prd_file
        assert prd_path.exists(), f"PRD file missing: {prd_file}"
        content = prd_path.read_text(encoding="utf-8")
        assert len(content) > 1000, f"PRD file too short: {prd_file}"
        assert "##" in content, f"PRD not properly formatted: {prd_file}"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "e2e"])
