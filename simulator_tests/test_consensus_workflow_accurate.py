"""
Accurate Consensus Workflow Test

This test validates the complete consensus workflow step-by-step to ensure:
1. Step 1: Claude provides its own analysis
2. Step 2: Tool consults first model and returns response to Claude
3. Step 3: Tool consults second model and returns response to Claude
4. Step 4: Claude synthesizes all perspectives

This replaces the old faulty test that used non-workflow parameters.
"""

import json

from .conversation_base_test import ConversationBaseTest


class TestConsensusWorkflowAccurate(ConversationBaseTest):
    """Test complete consensus workflow with accurate step-by-step behavior"""

    @property
    def test_name(self) -> str:
        return "consensus_workflow_accurate"

    @property
    def test_description(self) -> str:
        return "Test NEW efficient consensus workflow: 2 models = 2 steps (Claude+model1, model2+synthesis)"

    def run_test(self) -> bool:
        """Run complete consensus workflow test"""
        # Set up the test environment
        self.setUp()

        try:
            self.logger.info("Testing concurrent consensus workflow in single step")
            self.logger.info(
                "Expected flow: Single step - Claude analysis + both models consulted concurrently + synthesis"
            )

            # ============================================================================
            # SINGLE CONCURRENT STEP: Claude analysis + both models + synthesis
            # ============================================================================
            self.logger.info("=== SINGLE STEP: Concurrent execution with flash:for and flash:against ===")

            response, _ = self.call_mcp_tool_direct(
                "consensus",
                {
                    "step": "Should we add a new AI-powered search feature to our application? Please analyze the technical feasibility, user value, and implementation complexity.",
                    "step_number": 1,
                    "total_steps": 1,  # Concurrent: both models in single step
                    "next_step_required": False,
                    "findings": "Initial assessment of AI search feature proposal considering user needs, technical constraints, and business value.",
                    "models": [
                        {
                            "model": "qwen3:0.6b",
                            "stance": "for",
                            "stance_prompt": "Focus on innovation benefits and competitive advantages.",
                        },
                        {
                            "model": "qwen3:0.6b",
                            "stance": "against",
                            "stance_prompt": "Focus on implementation complexity and resource requirements.",
                        },
                    ],
                    "model": "qwen3:0.6b",  # Claude's execution model
                },
            )

            if not response:
                self.logger.error("Concurrent step failed - no response")
                return False

            data = json.loads(response)
            self.logger.info(f"Concurrent step status: {data.get('status')}")

            # Validate concurrent completion status
            if data.get("status") != "consensus_workflow_complete":
                self.logger.error(f"Expected status 'consensus_workflow_complete', got: {data.get('status')}")
                return False

            if data.get("step_number") != 1:
                self.logger.error(f"Expected step_number 1, got: {data.get('step_number')}")
                return False

            if data.get("next_step_required"):
                self.logger.error("Expected next_step_required=False for single concurrent step")
                return False

            # Verify Claude's analysis is included
            if "agent_analysis" not in data:
                self.logger.error("Expected agent_analysis in concurrent response")
                return False

            # Verify consensus completion data
            if not data.get("consensus_complete"):
                self.logger.error("Expected consensus_complete=True in concurrent step")
                return False

            if "complete_consensus" not in data:
                self.logger.error("Expected complete_consensus data in concurrent step")
                return False

            complete_consensus = data["complete_consensus"]
            if complete_consensus.get("total_responses") != 2:
                self.logger.error(f"Expected 2 model responses, got: {complete_consensus.get('total_responses')}")
                return False

            models_consulted = complete_consensus.get("models_consulted", [])
            expected_models = ["flash:for", "flash:against"]
            if models_consulted != expected_models:
                self.logger.error(f"Expected models {expected_models}, got: {models_consulted}")
                return False

            # ============================================================================
            # VALIDATION: Check accumulated responses are available
            # ============================================================================
            self.logger.info("=== VALIDATION: Checking accumulated responses ===")

            if "accumulated_responses" not in data:
                self.logger.error("Expected accumulated_responses in concurrent step")
                return False

            accumulated = data["accumulated_responses"]
            if len(accumulated) != 2:
                self.logger.error(f"Expected 2 accumulated responses, got: {len(accumulated)}")
                return False

            # Verify first response (flash:for)
            response1 = accumulated[0]
            if response1.get("model") != "flash" or response1.get("stance") != "for":
                self.logger.error(f"First response incorrect: {response1}")
                return False

            if response1.get("status") != "success":
                self.logger.error(f"First response expected 'success', got {response1.get('status')}")
                return False

            if not response1.get("content"):
                self.logger.error("First response missing content")
                return False

            # Verify second response (flash:against)
            response2 = accumulated[1]
            if response2.get("model") != "flash" or response2.get("stance") != "against":
                self.logger.error(f"Second response incorrect: {response2}")
                return False

            if response2.get("status") != "success":
                self.logger.error(f"Second response expected 'success', got {response2.get('status')}")
                return False

            if not response2.get("content"):
                self.logger.error("Second response missing content")
                return False

            self.logger.info("✓ All accumulated responses validated")

            # Check metadata contains model name (Claude's model)
            metadata = data.get("metadata", {})
            if not metadata.get("model_name"):
                self.logger.error("Missing model_name in metadata")
                return False

            self.logger.info(f"Model name in metadata: {metadata.get('model_name')}")

            self.logger.info("✓ Concurrent consensus step completed successfully")
            self.logger.info("✓ Both models (flash:for, flash:against) consulted concurrently")
            self.logger.info("✓ All responses accumulated and validated")
            self.logger.info("✓ Claude analysis and synthesis included")
            self.logger.info("✓ Efficient workflow: 2 models = 1 concurrent step")

            return True

        except Exception as e:
            self.logger.error(f"Consensus workflow test failed with exception: {str(e)}")
            import traceback

            self.logger.error(f"Traceback: {traceback.format_exc()}")
            return False
