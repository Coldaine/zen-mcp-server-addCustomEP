"""
Test consensus tool with three models demonstrating sequential processing
"""

import json

from .base_test import BaseSimulatorTest


class TestConsensusThreeModels(BaseSimulatorTest):
    """Test consensus tool functionality with three models (testing sequential processing)"""

    @property
    def test_name(self) -> str:
        return "consensus_three_models"

    @property
    def test_description(self) -> str:
        return "Test consensus tool with three models using flash:against, flash:for, local-llama:neutral"

    def run_test(self) -> bool:
        """Run three-model consensus test"""
        try:
            self.logger.info("Testing consensus tool with three models: flash:against, flash:for, local-llama:neutral")

            # Send request with three objects using concurrent single-step workflow
            response, continuation_id = self.call_mcp_tool(
                "consensus",
                {
                    "step": "Is a sync manager class a good idea for my CoolTodos app?",
                    "step_number": 1,
                    "total_steps": 1,  # Concurrent: all 3 models in single step
                    "next_step_required": False,
                    "findings": "Initial analysis needed on sync manager class architecture decision for CoolTodos app",
                    "models": [
                        {
                            "model": "qwen3:0.6b",
                            "stance": "against",
                            "stance_prompt": "You are a software architecture critic. Focus on the potential downsides of adding a sync manager class: complexity overhead, maintenance burden, potential for over-engineering, and whether simpler alternatives exist. Consider if this adds unnecessary abstraction layers.",
                        },
                        {
                            "model": "qwen3:0.6b",
                            "stance": "for",
                            "stance_prompt": "You are a software architecture advocate. Focus on the benefits of a sync manager class: separation of concerns, testability, maintainability, and how it can improve the overall architecture. Consider scalability and code organization advantages.",
                        },
                        {
                            "model": "qwen3:0.6b",
                            "stance": "neutral",
                            "stance_prompt": "You are a pragmatic software engineer. Provide a balanced analysis considering both the benefits and drawbacks. Focus on the specific context of a CoolTodos app and what factors would determine if this is the right choice.",
                        },
                    ],
                    "model": "qwen3:0.6b",  # Default model for Claude's execution
                },
            )

            # Validate response
            if not response:
                self.logger.error("Failed to get response from three-model consensus tool")
                return False

            self.logger.info(f"Three-model consensus response preview: {response[:500]}...")

            # Parse the JSON response
            try:
                consensus_data = json.loads(response)
            except json.JSONDecodeError:
                self.logger.error(f"Failed to parse three-model consensus response as JSON: {response}")
                return False

            # Validate consensus structure
            if "status" not in consensus_data:
                self.logger.error("Missing 'status' field in three-model consensus response")
                return False

            # Check for concurrent completion status
            expected_status = "consensus_workflow_complete"
            if consensus_data["status"] != expected_status:
                self.logger.error(
                    f"Three-model consensus concurrent step failed with status: {consensus_data['status']}, expected: {expected_status}"
                )

                # Log additional error details for debugging
                if "error" in consensus_data:
                    self.logger.error(f"Error message: {consensus_data['error']}")
                if "models_errored" in consensus_data:
                    self.logger.error(f"Models that errored: {consensus_data['models_errored']}")
                if "models_skipped" in consensus_data:
                    self.logger.error(f"Models skipped: {consensus_data['models_skipped']}")
                if "next_steps" in consensus_data:
                    self.logger.error(f"Suggested next steps: {consensus_data['next_steps']}")

                return False

            # Validate concurrent response structure with 3 accumulated responses
            accumulated_responses = consensus_data.get("accumulated_responses") or consensus_data.get(
                "all_model_responses"
            )
            if not accumulated_responses or len(accumulated_responses) != 3:
                self.logger.error(
                    f"Expected 3 accumulated responses, got {len(accumulated_responses) if accumulated_responses else 0}"
                )
                return False

            expected_models_stances = [("flash", "against"), ("flash", "for"), ("qwen3:0.6b", "neutral")]

            for i, (expected_model, expected_stance) in enumerate(expected_models_stances):
                if i >= len(accumulated_responses):
                    self.logger.error(f"Missing response {i+1}")
                    return False

                response = accumulated_responses[i]
                if response.get("model") != expected_model or response.get("stance") != expected_stance:
                    self.logger.error(
                        f"Response {i+1} expected {expected_model}:{expected_stance}, got {response.get('model')}:{response.get('stance')}"
                    )
                    return False

                if response.get("status") != "success":
                    self.logger.error(f"Response {i+1} expected 'success', got {response.get('status')}")
                    return False

                if not response.get("content"):
                    self.logger.error(f"Response {i+1} missing content")
                    return False

            # Check step information for single step
            if consensus_data.get("step_number") != 1:
                self.logger.error(f"Expected step_number 1, got: {consensus_data.get('step_number')}")
                return False

            if consensus_data.get("next_step_required"):
                self.logger.error("Expected next_step_required=False for single concurrent step")
                return False

            # Check metadata contains model name (Claude's model)
            metadata = consensus_data.get("metadata", {})
            if not metadata.get("model_name"):
                self.logger.error("Missing model_name in metadata")
                return False

            self.logger.info(f"Model name in metadata: {metadata.get('model_name')}")

            # Verify we have analysis from Claude
            agent_analysis = consensus_data.get("agent_analysis")
            if not agent_analysis:
                self.logger.error("Missing Claude's analysis in concurrent step")
                return False

            analysis_text = agent_analysis.get("initial_analysis", "")
            self.logger.info(f"Claude analysis length: {len(analysis_text)} characters")

            # Verify complete_consensus
            complete_consensus = consensus_data.get("complete_consensus")
            if not complete_consensus:
                self.logger.error("Missing complete_consensus in response")
                return False

            if complete_consensus.get("total_responses") != 3:
                self.logger.error(f"Expected total_responses 3, got {complete_consensus.get('total_responses')}")
                return False

            self.logger.info("✓ Three-model concurrent consensus tool test completed successfully")
            self.logger.info("✓ Concurrent step completed with 3 models consulted")
            self.logger.info("✓ All responses validated: flash:against, flash:for, qwen3:0.6b:neutral")
            self.logger.info(f"✓ Analysis provided: {len(analysis_text)} characters")
            self.logger.info(f"✓ Model metadata properly included: {metadata.get('model_name')}")
            self.logger.info("✓ Consensus complete in single step")

            return True

        except Exception as e:
            self.logger.error(f"Three-model consensus test failed with exception: {str(e)}")
            return False
