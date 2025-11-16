"""
Week 5 Integration Tests: Pause/Resume Flow with Code Validation.

Tests the critical pause/resume workflow:
1. pause_for_google_ai node (user chooses pause vs skip)
2. receive_code node (waits for code upload)
3. validate_code node (comprehensive validation)
4. Conditional routing based on validation results
"""

import pytest

from src.langgraph.nodes.pause_for_google_ai import (
    pause_for_google_ai,
    should_pause_or_continue,
)
from src.langgraph.nodes.receive_code import has_code_been_uploaded, receive_code
from src.langgraph.nodes.validate_code import (
    handle_validation_failure,
    should_proceed_after_validation,
    validate_code,
)
from src.langgraph.state import DesignAgentState
from src.validators.quality_scorer import MIN_ACCEPTABLE_SCORE


# ============================================================================
# Test: pause_for_google_ai Node
# ============================================================================


@pytest.mark.asyncio
async def test_pause_for_google_ai_waiting_for_choice():
    """Test pause_for_google_ai when no user feedback yet."""
    state: DesignAgentState = {
        "job_id": "test-123",
        "user_feedback": None,
        "awaiting_feedback": False,
    }

    result = await pause_for_google_ai(state)

    assert result["awaiting_feedback"] is True
    assert result["phase_name"] == "Choose: Pause for Google AI Studio or Skip to Documents"
    assert result["progress_percent"] == 72.0


@pytest.mark.asyncio
async def test_pause_for_google_ai_user_chooses_pause():
    """Test pause_for_google_ai when user chooses to pause."""
    state: DesignAgentState = {
        "job_id": "test-123",
        "user_feedback": "pause",
        "awaiting_feedback": True,
    }

    result = await pause_for_google_ai(state)

    assert result["should_pause_for_google_ai"] is True
    assert result["paused"] is True
    assert result["phase_name"] == "Paused - Waiting for Design Upload"
    assert result["user_feedback"] is None
    assert result["awaiting_feedback"] is False


@pytest.mark.asyncio
async def test_pause_for_google_ai_user_chooses_skip():
    """Test pause_for_google_ai when user chooses to skip."""
    state: DesignAgentState = {
        "job_id": "test-123",
        "user_feedback": "skip",
        "awaiting_feedback": True,
    }

    result = await pause_for_google_ai(state)

    assert result["should_pause_for_google_ai"] is False
    assert result["paused"] is False
    assert result["uploaded_code"] is None
    assert result["validation_results"] is None
    assert result["phase_name"] == "Skipping to Document Generation"


@pytest.mark.asyncio
async def test_pause_for_google_ai_alternative_inputs():
    """Test pause_for_google_ai with alternative user inputs."""
    # Test "use google ai"
    state: DesignAgentState = {
        "job_id": "test-123",
        "user_feedback": "use google ai",
    }
    result = await pause_for_google_ai(state)
    assert result["should_pause_for_google_ai"] is True

    # Test "continue"
    state["user_feedback"] = "continue"
    result = await pause_for_google_ai(state)
    assert result["should_pause_for_google_ai"] is False

    # Test "skip to documents"
    state["user_feedback"] = "skip to documents"
    result = await pause_for_google_ai(state)
    assert result["should_pause_for_google_ai"] is False


def test_should_pause_or_continue_routing():
    """Test conditional routing for pause_for_google_ai."""
    # Test waiting for choice
    state: DesignAgentState = {
        "awaiting_feedback": True,
        "user_feedback": None,
    }
    assert should_pause_or_continue(state) == "wait_for_choice"

    # Test pause chosen
    state = {
        "should_pause_for_google_ai": True,
        "paused": True,
        "awaiting_feedback": False,
    }
    assert should_pause_or_continue(state) == "pause"

    # Test skip chosen
    state = {
        "should_pause_for_google_ai": False,
        "paused": False,
        "awaiting_feedback": False,
    }
    assert should_pause_or_continue(state) == "skip_to_phase6"


# ============================================================================
# Test: receive_code Node
# ============================================================================


@pytest.mark.asyncio
async def test_receive_code_no_upload_yet():
    """Test receive_code when no code uploaded yet."""
    state: DesignAgentState = {
        "job_id": "test-123",
        "uploaded_code": None,
        "paused": True,
    }

    result = await receive_code(state)

    assert result["paused"] is True
    assert result["phase_name"] == "Waiting for Design Code Upload"
    assert result["progress_percent"] == 77.0


@pytest.mark.asyncio
async def test_receive_code_with_upload():
    """Test receive_code when code has been uploaded."""
    uploaded_code = """
import React from 'react';

export const LoginScreen = () => {
  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <button className="px-6 py-3 bg-blue-600 text-white rounded-lg">
        Sign In
      </button>
    </div>
  );
};
"""

    state: DesignAgentState = {
        "job_id": "test-123",
        "uploaded_code": uploaded_code,
        "uploaded_code_metadata": {
            "files": ["LoginScreen.tsx"],
            "total_size_bytes": len(uploaded_code),
        },
        "paused": True,
    }

    result = await receive_code(state)

    assert result["paused"] is False
    assert result["uploaded_code"] == uploaded_code
    assert result["phase_name"] == "Code Received - Ready for Validation"
    assert result["progress_percent"] == 80.0


def test_has_code_been_uploaded_routing():
    """Test conditional routing for receive_code."""
    # Test no code uploaded
    state: DesignAgentState = {
        "uploaded_code": None,
    }
    assert has_code_been_uploaded(state) == "waiting"

    # Test code uploaded
    state = {
        "uploaded_code": "const App = () => <div>Hello</div>;",
    }
    assert has_code_been_uploaded(state) == "code_uploaded"


# ============================================================================
# Test: validate_code Node
# ============================================================================


@pytest.mark.asyncio
async def test_validate_code_high_quality():
    """Test validate_code with high-quality code (should pass)."""
    # High-quality TypeScript + Tailwind code
    high_quality_code = """
import React from 'react';

interface LoginScreenProps {
  onSubmit: (email: string, password: string) => void;
}

export const LoginScreen: React.FC<LoginScreenProps> = ({ onSubmit }) => {
  const [email, setEmail] = React.useState<string>('');
  const [password, setPassword] = React.useState<string>('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSubmit(email, password);
  };

  return (
    <main className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="max-w-md w-full space-y-8">
        <header>
          <h1 className="text-3xl font-bold text-center text-gray-900">
            Welcome Back
          </h1>
        </header>

        <form onSubmit={handleSubmit} className="mt-8 space-y-6">
          <div>
            <label htmlFor="email" className="block text-sm font-medium text-gray-700">
              Email
            </label>
            <input
              id="email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md"
              aria-required="true"
            />
          </div>

          <div>
            <label htmlFor="password" className="block text-sm font-medium text-gray-700">
              Password
            </label>
            <input
              id="password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md"
              aria-required="true"
            />
          </div>

          <button
            type="submit"
            className="w-full flex justify-center py-3 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
          >
            Sign In
          </button>
        </form>
      </div>
    </main>
  );
};
"""

    state: DesignAgentState = {
        "job_id": "test-123",
        "uploaded_code": high_quality_code,
        "uploaded_code_metadata": {
            "file_extension": ".tsx",
        },
        "design_system": {
            "colors": {
                "primary": ["#3B82F6"],
            },
        },
    }

    result = await validate_code(state)

    assert "validation_results" in result
    assert "quality_score" in result
    assert result["current_phase"] == 5

    # Should have high score
    assert result["quality_score"] >= 80.0  # At least B- grade

    # Check validation results structure
    validation_results = result["validation_results"]
    assert "overall_score" in validation_results
    assert "grade" in validation_results
    assert "component_scores" in validation_results
    assert "code_validation" in validation_results
    assert "accessibility_validation" in validation_results


@pytest.mark.asyncio
async def test_validate_code_low_quality():
    """Test validate_code with low-quality code (should fail)."""
    # Low-quality code: no types, custom CSS, missing alt text
    low_quality_code = """
import React from 'react';
import './custom.css';

const LoginScreen = () => {
  return (
    <div style={{backgroundColor: 'blue', padding: '20px'}}>
      <h1>Login</h1>
      <img src="logo.png" />
      <input placeholder="Email" />
      <input placeholder="Password" />
      <div onClick={() => alert('clicked')}>Submit</div>
    </div>
  );
};
"""

    state: DesignAgentState = {
        "job_id": "test-123",
        "uploaded_code": low_quality_code,
        "uploaded_code_metadata": {
            "file_extension": ".jsx",
        },
    }

    result = await validate_code(state)

    assert "validation_results" in result
    assert "quality_score" in result

    # Should have low score
    validation_results = result["validation_results"]
    assert validation_results["overall_score"] < MIN_ACCEPTABLE_SCORE  # Below 90
    assert validation_results["meets_minimum"] is False

    # Should have violations
    assert not validation_results["code_validation"]["tailwind_only"]
    assert validation_results["code_validation"]["has_custom_css"] is True


@pytest.mark.asyncio
async def test_validate_code_no_uploaded_code():
    """Test validate_code when no code is uploaded (error case)."""
    state: DesignAgentState = {
        "job_id": "test-123",
        "uploaded_code": None,
    }

    result = await validate_code(state)

    assert "errors" in result
    assert len(result["errors"]) > 0
    assert "No uploaded code to validate" in result["errors"][0]
    assert result["should_retry"] is True


def test_should_proceed_after_validation_routing():
    """Test conditional routing for validate_code."""
    # Test validation passed (high score)
    state: DesignAgentState = {
        "validation_passed": True,
        "quality_score": 92.5,
    }
    assert should_proceed_after_validation(state) == "validation_passed"

    # Test validation failed (low score)
    state = {
        "validation_passed": False,
        "quality_score": 75.0,
    }
    assert should_proceed_after_validation(state) == "validation_failed"

    # Test retry (validation errors)
    state = {
        "should_retry": True,
        "retry_count": 1,
    }
    assert should_proceed_after_validation(state) == "retry"

    # Test retry exhausted (max 3 retries)
    state = {
        "should_retry": True,
        "retry_count": 3,
    }
    assert should_proceed_after_validation(state) == "validation_failed"


@pytest.mark.asyncio
async def test_handle_validation_failure():
    """Test handle_validation_failure provides user feedback."""
    state: DesignAgentState = {
        "job_id": "test-123",
        "quality_score": 65.5,
        "validation_results": {
            "grade": "D",
            "component_scores": {
                "syntax": 80.0,
                "typescript": 60.0,
                "tailwind": 50.0,
                "accessibility": 70.0,
            },
            "code_validation": {
                "errors": ["Custom CSS detected"],
                "warnings": ["Low type coverage"],
            },
            "accessibility_validation": {
                "issues": ["Missing alt text on images"],
                "warnings": ["Low contrast on some elements"],
            },
        },
    }

    result = await handle_validation_failure(state)

    assert result["awaiting_feedback"] is True
    assert "validation_feedback" in result
    assert "65.5/100" in result["validation_feedback"]
    assert "Grade: D" in result["validation_feedback"]
    assert "Custom CSS detected" in result["validation_feedback"]
    assert "Missing alt text" in result["validation_feedback"]


# ============================================================================
# Test: Full Pause/Resume Workflow
# ============================================================================


@pytest.mark.asyncio
async def test_full_pause_resume_workflow():
    """Test complete pause → upload → validate workflow."""

    # Step 1: User chooses to pause
    state: DesignAgentState = {
        "job_id": "test-workflow",
        "user_feedback": "pause",
        "current_phase": 4,
    }

    # Execute pause node
    state = await pause_for_google_ai(state)
    assert state["paused"] is True
    assert state["should_pause_for_google_ai"] is True

    # Check routing
    assert should_pause_or_continue(state) == "pause"

    # Step 2: User goes to Google AI Studio (simulated external step)
    # ... user creates design ...

    # Step 3: User uploads code
    state["uploaded_code"] = """
import React from 'react';

interface AppProps {
  title: string;
}

export const App: React.FC<AppProps> = ({ title }) => {
  return (
    <main className="min-h-screen bg-gray-50">
      <h1 className="text-3xl font-bold">{title}</h1>
    </main>
  );
};
"""
    state["uploaded_code_metadata"] = {
        "file_extension": ".tsx",
        "files": ["App.tsx"],
    }

    # Execute receive_code node
    state = await receive_code(state)
    assert state["paused"] is False
    assert state["uploaded_code"] is not None

    # Check routing
    assert has_code_been_uploaded(state) == "code_uploaded"

    # Step 4: Validate code
    state = await validate_code(state)
    assert "validation_results" in state
    assert "quality_score" in state

    # Check routing
    routing = should_proceed_after_validation(state)
    assert routing in ["validation_passed", "validation_failed"]


@pytest.mark.asyncio
async def test_full_skip_workflow():
    """Test skip workflow (bypass pause and code upload)."""

    # User chooses to skip
    state: DesignAgentState = {
        "job_id": "test-skip",
        "user_feedback": "skip",
        "current_phase": 4,
    }

    # Execute pause node
    state = await pause_for_google_ai(state)
    assert state["paused"] is False
    assert state["should_pause_for_google_ai"] is False
    assert state["uploaded_code"] is None

    # Check routing - should skip to Phase 6
    assert should_pause_or_continue(state) == "skip_to_phase6"

    # No code upload or validation needed
    # Workflow proceeds directly to document generation (Phase 6)
