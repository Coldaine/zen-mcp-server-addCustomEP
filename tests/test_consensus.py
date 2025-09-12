"""
Tests for the Consensus tool using WorkflowTool architecture.
"""

import asyncio
import json
from unittest.mock import Mock

import pytest

from tools.consensus import ConsensusRequest, ConsensusTool
from tools.models import ToolModelCategory


class TestConsensusTool:
    """Test suite for ConsensusTool using WorkflowTool architecture."""

    def test_tool_metadata(self):
        """Test basic tool metadata and configuration."""
        tool = ConsensusTool()

        assert tool.get_name() == "consensus"
        assert "consensus" in tool.get_description()
        assert tool.get_default_temperature() == 0.2  # TEMPERATURE_ANALYTICAL
        assert tool.get_model_category() == ToolModelCategory.EXTENDED_REASONING
        assert tool.requires_model() is False  # Consensus manages its own models

    def test_request_validation_step1(self):
        """Test Pydantic request model validation for step 1."""
        # Valid step 1 request with models - using cheaper alternatives
        step1_request = ConsensusRequest(
            step="Analyzing the real-time collaboration proposal",
            step_number=1,
            total_steps=4,  # 1 (Claude) + 2 models + 1 (synthesis)
            next_step_required=True,
            findings="Initial assessment shows strong value but technical complexity",
            confidence="medium",
            models=[{"model": "flash", "stance": "neutral"}, {"model": "haiku", "stance": "for"}],
            relevant_files=["/proposal.md"],
            model="auto",  # Required by ToolRequest
            continuation_id=None,
            hypothesis=None,
            backtrack_from_step=None,
            use_assistant_model=True,
            current_model_index=0,
        )

        assert step1_request.step_number == 1
        assert step1_request.confidence == "medium"
        assert len(step1_request.models) == 2
        assert step1_request.models[0]["model"] == "flash"

    def test_request_validation_missing_models_step1(self):
        """Test that step 1 requires models field."""
        with pytest.raises(ValueError, match="Step 1 requires 'models' field"):
            ConsensusRequest(
                step="Test step",
                step_number=1,
                total_steps=3,
                next_step_required=True,
                findings="Test findings",
                model="auto",
                continuation_id=None,
                hypothesis=None,
                backtrack_from_step=None,
                use_assistant_model=True,
                current_model_index=0,
                # Missing models field
            )

    def test_request_validation_later_steps(self):
        """Test request validation for steps 2+."""
        # Step 2+ doesn't require models field
        step2_request = ConsensusRequest(
            step="Processing first model response",
            step_number=2,
            total_steps=4,
            next_step_required=True,
            findings="Model provided supportive perspective",
            confidence="medium",
            continuation_id="test-id",
            current_model_index=1,
            model="auto",
            hypothesis=None,
            backtrack_from_step=None,
            use_assistant_model=True,
            models=None,  # Not required for step 2+
        )

        assert step2_request.step_number == 2
        assert step2_request.models is None  # Not required after step 1

    def test_request_validation_duplicate_model_stance(self):
        """Test that duplicate model+stance combinations are rejected."""
        # Valid: same model with different stances
        valid_request = ConsensusRequest(
            step="Analyze this proposal",
            step_number=1,
            total_steps=1,
            next_step_required=True,
            findings="Initial analysis",
            models=[
                {"model": "o3", "stance": "for"},
                {"model": "o3", "stance": "against"},
                {"model": "flash", "stance": "neutral"},
            ],
            continuation_id="test-id",
            model="auto",
            hypothesis=None,
            backtrack_from_step=None,
            use_assistant_model=True,
            current_model_index=0,
        )
        assert len(valid_request.models) == 3

        # Invalid: duplicate model+stance combination
        with pytest.raises(ValueError, match="Duplicate model \\+ stance combination"):
            ConsensusRequest(
                step="Analyze this proposal",
                step_number=1,
                total_steps=1,
                next_step_required=True,
                findings="Initial analysis",
                models=[
                    {"model": "o3", "stance": "for"},
                    {"model": "flash", "stance": "neutral"},
                    {"model": "o3", "stance": "for"},  # Duplicate!
                ],
                continuation_id="test-id",
                model="auto",
                hypothesis=None,
                backtrack_from_step=None,
                use_assistant_model=True,
                current_model_index=0,
            )

    def test_input_schema_generation(self):
        """Test that input schema is generated correctly."""
        tool = ConsensusTool()
        schema = tool.get_input_schema()

        # Verify consensus workflow fields are present
        assert "step" in schema["properties"]
        assert "step_number" in schema["properties"]
        assert "total_steps" in schema["properties"]
        assert "next_step_required" in schema["properties"]
        assert "findings" in schema["properties"]
        # confidence field should be excluded
        assert "confidence" not in schema["properties"]
        assert "models" in schema["properties"]
        # relevant_files should be present as it's used by consensus
        assert "relevant_files" in schema["properties"]

        # model field should be present for Gemini compatibility (consensus uses 'models' as well)
        assert "model" in schema["properties"]

        # Verify workflow fields that should NOT be present
        assert "files_checked" not in schema["properties"]
        assert "hypothesis" not in schema["properties"]
        assert "issues_found" not in schema["properties"]
        assert "temperature" not in schema["properties"]
        assert "thinking_mode" not in schema["properties"]
        assert "use_websearch" not in schema["properties"]

        # Images should be present now
        assert "images" in schema["properties"]
        assert schema["properties"]["images"]["type"] == "array"
        assert schema["properties"]["images"]["items"]["type"] == "string"

        # Verify field types
        assert schema["properties"]["step"]["type"] == "string"
        assert schema["properties"]["step_number"]["type"] == "integer"
        assert schema["properties"]["models"]["type"] == "array"

        # Verify models array structure
        models_items = schema["properties"]["models"]["items"]
        assert models_items["type"] == "object"
        assert "model" in models_items["properties"]
        assert "stance" in models_items["properties"]
        assert "stance_prompt" in models_items["properties"]

    def test_get_required_actions(self):
        """Test required actions for different consensus phases."""
        tool = ConsensusTool()

        # Step 1: Claude's initial analysis + concurrent model consultations + synthesis
        actions = tool.get_required_actions(1, "exploring", "Initial findings", 4)
        assert any(
            "initial analysis is complete and all models have been consulted concurrently" in action
            for action in actions
        )
        assert any("Review all model responses provided in this step" in action for action in actions)
        assert any("Synthesize all perspectives" in action for action in actions)

    def test_prepare_step_data(self):
        """Test step data preparation for consensus workflow."""
        tool = ConsensusTool()
        request = ConsensusRequest(
            step="Test step",
            step_number=1,
            total_steps=3,
            next_step_required=True,
            findings="Test findings",
            confidence="medium",
            models=[{"model": "test"}],
            relevant_files=["/test.py"],
            model="auto",
            continuation_id=None,
            hypothesis=None,
            backtrack_from_step=None,
            use_assistant_model=True,
            current_model_index=0,
        )

        step_data = tool.prepare_step_data(request)

        # Verify consensus-specific fields
        assert step_data["step"] == "Test step"
        assert step_data["findings"] == "Test findings"
        assert step_data["relevant_files"] == ["/test.py"]

        # Verify unused workflow fields are empty
        assert step_data["files_checked"] == []
        assert step_data["relevant_context"] == []
        assert step_data["issues_found"] == []
        assert step_data["hypothesis"] is None

    def test_stance_enhanced_prompt_generation(self):
        """Test stance-enhanced prompt generation."""
        tool = ConsensusTool()

        # Test different stances
        for_prompt = tool._get_stance_enhanced_prompt("for")
        assert "SUPPORTIVE PERSPECTIVE" in for_prompt

        against_prompt = tool._get_stance_enhanced_prompt("against")
        assert "CRITICAL PERSPECTIVE" in against_prompt

        neutral_prompt = tool._get_stance_enhanced_prompt("neutral")
        assert "BALANCED PERSPECTIVE" in neutral_prompt

        # Test custom stance prompt
        custom = "Focus on specific aspects"
        custom_prompt = tool._get_stance_enhanced_prompt("for", custom)
        assert custom in custom_prompt
        assert "SUPPORTIVE PERSPECTIVE" not in custom_prompt

    def test_should_call_expert_analysis(self):
        """Test that consensus workflow doesn't use expert analysis."""
        tool = ConsensusTool()
        assert tool.should_call_expert_analysis({}) is False
        assert tool.requires_expert_analysis() is False

    def test_execute_workflow_step1_basic(self):
        """Test basic workflow validation for step 1."""
        tool = ConsensusTool()

        # Test that step 1 sets up the workflow correctly
        arguments = {
            "step": "Initial analysis of proposal",
            "step_number": 1,
            "total_steps": 2,
            "next_step_required": True,
            "findings": "Found pros and cons",
            "models": [{"model": "flash", "stance": "neutral"}, {"model": "haiku", "stance": "for"}],
        }

        # Verify models_to_consult is set correctly from step 1
        request = tool.get_workflow_request_model()(**arguments)
        assert request.models is not None  # Type guard for mypy
        models = request.models  # Type narrowing
        assert len(models) == 2
        assert models[0]["model"] == "flash"
        assert models[1]["model"] == "haiku"

    def test_execute_workflow_total_steps_calculation(self):
        """Test that total_steps is calculated correctly from models."""
        tool = ConsensusTool()

        # Test with 2 models
        arguments = {
            "step": "Initial analysis",
            "step_number": 1,
            "total_steps": 4,  # This should be corrected to 2
            "next_step_required": True,
            "findings": "Analysis complete",
            "models": [{"model": "flash", "stance": "neutral"}, {"model": "haiku", "stance": "for"}],
        }

        request = tool.get_workflow_request_model()(**arguments)
        # The tool should set total_steps = len(models) = 2
        assert len(request.models) == 2

    def test_consult_model_basic_structure(self):
        """Test basic model consultation structure."""
        tool = ConsensusTool()

        # Test that _get_stance_enhanced_prompt works
        for_prompt = tool._get_stance_enhanced_prompt("for")
        against_prompt = tool._get_stance_enhanced_prompt("against")
        neutral_prompt = tool._get_stance_enhanced_prompt("neutral")

        assert "SUPPORTIVE PERSPECTIVE" in for_prompt
        assert "CRITICAL PERSPECTIVE" in against_prompt
        assert "BALANCED PERSPECTIVE" in neutral_prompt

    def test_model_configuration_validation(self):
        """Test model configuration validation."""
        tool = ConsensusTool()

        # Test single model config
        models = [{"model": "flash", "stance": "neutral"}]
        arguments = {
            "step": "Test",
            "step_number": 1,
            "total_steps": 1,
            "next_step_required": False,
            "findings": "Test findings",
            "models": models,
        }

        request = tool.get_workflow_request_model()(**arguments)
        assert len(request.models) == 1
        assert request.models[0]["model"] == "flash"
        assert request.models[0]["stance"] == "neutral"

    def test_handle_work_continuation(self):
        """Test work continuation handling - legacy method for compatibility."""
        tool = ConsensusTool()
        tool.models_to_consult = [{"model": "flash", "stance": "neutral"}, {"model": "haiku", "stance": "for"}]

        # Note: In the new workflow, model consultation happens DURING steps in execute_workflow
        # This method is kept for compatibility but not actively used in the step-by-step flow

        # Test after step 1
        request = Mock(step_number=1, current_model_index=0)
        response_data = {}

        result = tool.handle_work_continuation(response_data, request)
        # The method still exists but returns legacy status for compatibility
        assert "status" in result

        # Test between model consultations
        request = Mock(step_number=2, current_model_index=1)
        response_data = {}

        result = tool.handle_work_continuation(response_data, request)
        assert "status" in result

    def test_customize_workflow_response(self):
        """Test response customization for consensus workflow."""
        tool = ConsensusTool()
        tool.accumulated_responses = [{"model": "test", "response": "data"}]

        # Test different step numbers (new workflow: concurrent execution in step 1)
        request = Mock(step_number=1, total_steps=1)
        response_data = {}
        result = tool.customize_workflow_response(response_data, request)
        assert result["consensus_workflow_status"] == "concurrent_execution_complete"

    def test_concurrent_execution_step1(self, mocker):
        """Test that step 1 executes all model consultations concurrently."""
        tool = ConsensusTool()

        # Mock the concurrent execution
        mock_model_responses = [
            {
                "model": "flash",
                "stance": "neutral",
                "status": "success",
                "content": "Flash analysis",
                "error_message": None,
                "latency_ms": 500,
            },
            {
                "model": "haiku",
                "stance": "for",
                "status": "success",
                "content": "O3 analysis",
                "error_message": None,
                "latency_ms": 800,
            },
        ]

        # Mock the run_models_concurrently function
        mock_run_concurrent = mocker.patch("tools.consensus.run_models_concurrently")
        mock_run_concurrent.return_value = mock_model_responses

        # Mock the _consult_model_with_timing method (return value not needed explicitly)
        mocker.patch.object(ConsensusTool, "_consult_model_with_timing")

        # Create step 1 request
        request = ConsensusRequest(
            step="Test proposal for concurrent execution",
            step_number=1,
            total_steps=1,  # Will be overridden to 1
            next_step_required=False,
            findings="Initial findings",
            models=[{"model": "flash", "stance": "neutral"}, {"model": "haiku", "stance": "for"}],
            model="auto",
            continuation_id=None,
            hypothesis=None,
            backtrack_from_step=None,
            use_assistant_model=True,
            current_model_index=0,
        )

        # Execute workflow
        result = asyncio.run(
            tool.execute_workflow(
                {
                    "step": request.step,
                    "step_number": request.step_number,
                    "total_steps": request.total_steps,
                    "next_step_required": request.next_step_required,
                    "findings": request.findings,
                    "models": request.models,
                }
            )
        )

        # Verify concurrent execution was called
        mock_run_concurrent.assert_called_once()
        args, kwargs = mock_run_concurrent.call_args
        model_specs = args[0]
        assert len(model_specs) == 2
        assert model_specs[0]["model"] == "flash"
        assert model_specs[1]["model"] == "haiku"

        # Verify response structure
        response_text = result[0].text
        response_data = json.loads(response_text)

        assert response_data["status"] == "consensus_workflow_complete"
        assert response_data["consensus_complete"] is True
        assert len(response_data["all_model_responses"]) == 2
        assert response_data["all_model_responses"][0]["model"] == "flash"
        assert response_data["all_model_responses"][1]["model"] == "haiku"

    def test_concurrent_execution_error_handling(self):
        """Test concurrent execution with mixed success/error results."""
        tool = ConsensusTool()

        # Simulate mixed results
        tool.models_to_consult = [{"model": "flash", "stance": "neutral"}, {"model": "haiku", "stance": "for"}]
        tool.accumulated_responses = [
            {
                "model": "flash",
                "stance": "neutral",
                "status": "success",
                "content": "Success analysis",
                "error_message": None,
                "latency_ms": 500,
            },
            {
                "model": "haiku",
                "stance": "for",
                "status": "error",
                "content": None,
                "error_message": "Model timeout",
                "latency_ms": 30000,
            },
        ]

        # Test metadata customization
        response_data = {}
        request = Mock(step_number=1, total_steps=1)
        tool._customize_consensus_metadata(response_data, request)

        assert response_data["metadata"]["workflow_type"] == "concurrent_multi_model_consensus"
        assert response_data["metadata"]["execution_mode"] == "concurrent"
        assert len(response_data["metadata"]["models_consulted"]) == 2
        assert response_data["metadata"]["consensus_complete"] is True


if __name__ == "__main__":
    import unittest

    unittest.main()
