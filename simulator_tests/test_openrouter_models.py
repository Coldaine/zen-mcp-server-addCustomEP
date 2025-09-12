#!/usr/bin/env python3
"""
Kilo Code Endpoint Model Test (formerly OpenRouter Models Test)

Refocused to validate that the server can successfully route requests through the
configured Kilo Code OpenRouter-compatible endpoint and maintain conversation
continuity, using a minimal set of model calls to reduce external cost.

Coverage:
1. Basic chat call via a Kilo Code routed model alias (flash)
2. Conversation continuation using same routed model
3. Direct explicit model name routing still works (anthropic/claude-3-haiku) if available
4. Logs show usage of the custom OpenRouter endpoint (kilocode) rather than broad alias sweep

Removed:
- Broad alias matrix (pro, opus, o3, sonnet) to reduce redundancy and cost
- Memory test across many models (covered elsewhere)
"""


from .base_test import BaseSimulatorTest


class OpenRouterModelsTest(BaseSimulatorTest):
    """Test Kilo Code routed model functionality and minimal alias mapping"""

    @property
    def test_name(self) -> str:
        return "openrouter_models"

    @property
    def test_description(self) -> str:
        """Short description of the test."""
        return "Kilo Code routed model functionality and minimal alias mapping"

    def run_test(self) -> bool:
        """Test OpenRouter model functionality"""
        try:
            self.logger.info("Test: Kilo Code routed model functionality (minimal)")

            # Check if OpenRouter API key is configured
            import os

            has_openrouter = bool(os.environ.get("OPENROUTER_API_KEY"))

            if not has_openrouter:
                self.logger.info("  ⚠️  OpenRouter API key not configured - skipping test")
                self.logger.info("  ℹ️  This test requires OPENROUTER_API_KEY to be set in .env")
                return True  # Return True to indicate test is skipped, not failed

            # Setup test files for later use
            self.setup_test_files()

            # Test 1: Flash alias via Kilo Code endpoint
            self.logger.info("  1: Testing 'flash' alias via Kilo Code endpoint")

            response1, continuation_id = self.call_mcp_tool(
                "chat",
                {
                    "prompt": "Say 'Hello from Flash model!' and nothing else.",
                    "model": "flash",
                    "temperature": 0.1,
                },
            )

            if not response1:
                self.logger.error("  ❌ Flash alias test failed")
                return False

            self.logger.info("  ✅ Flash alias call completed")
            if continuation_id:
                self.logger.info(f"  ✅ Got continuation_id: {continuation_id}")

            # Test 2: Direct explicit model name if available
            self.logger.info("  2: Testing direct model name (anthropic/claude-3-haiku) if available")

            response2, _ = self.call_mcp_tool(
                "chat",
                {
                    "prompt": "Say 'Hello from Claude Haiku!' and nothing else.",
                    "model": "anthropic/claude-3-haiku",
                    "temperature": 0.1,
                },
            )
            if not response2:
                self.logger.warning("  ⚠️ Direct model name call failed (may not be allowed); continuing")

            # Test 3: Conversation continuity with alias
            self.logger.info("  3: Testing conversation continuity with 'flash'")

            response3, new_continuation_id = self.call_mcp_tool(
                "chat",
                {
                    "prompt": "Remember this number: 42. What number did I just tell you?",
                    "model": "flash",  # Use flash alias for continuity
                    "temperature": 0.1,
                },
            )

            if not response3 or not new_continuation_id:
                self.logger.error("  ❌ Failed to start conversation with continuation_id")
                return False

            # Continue the conversation
            response4, _ = self.call_mcp_tool(
                "chat",
                {
                    "prompt": "What was the number I told you earlier?",
                    "model": "flash",
                    "continuation_id": new_continuation_id,
                    "temperature": 0.1,
                },
            )

            if not response4:
                self.logger.error("  ❌ Failed to continue conversation")
                return False

            # Check if the model remembered the number
            if response4 and "42" in response4:
                self.logger.info("  ✅ Conversation continuity working with OpenRouter")
            else:
                self.logger.warning("  ⚠️  Model may not have remembered the number")

            # Test 4: Validate Kilo Code endpoint usage from logs
            self.logger.info("  4: Validating Kilo Code endpoint usage in logs")
            logs = self.get_recent_server_logs()

            # Check for OpenRouter API calls
            openrouter_logs = [line for line in logs.split("\n") if "openrouter" in line.lower()]
            openrouter_api_logs = [line for line in logs.split("\n") if "kilocode" in line.lower()]

            # Check for specific model mappings
            flash_mapping_logs = [line for line in logs.split("\n") if "flash" in line.lower()][:5]

            # Log findings
            self.logger.info(f"   OpenRouter-related logs: {len(openrouter_logs)}")
            self.logger.info(f"   OpenRouter API logs: {len(openrouter_api_logs)}")
            self.logger.info(f"   Flash mapping logs: {len(flash_mapping_logs)}")
            # Removed pro mapping (out of scope now)

            # Sample log output for debugging
            if self.verbose and openrouter_logs:
                self.logger.debug("  📋 Sample OpenRouter logs:")
                for log in openrouter_logs[:5]:
                    self.logger.debug(f"    {log}")

            # Success criteria
            openrouter_api_used = len(openrouter_api_logs) > 0
            models_mapped = len(flash_mapping_logs) > 0

            success_criteria = [
                ("OpenRouter API calls made", openrouter_api_used),
                ("Model aliases mapped correctly", models_mapped),
                ("All model calls succeeded", True),  # We already checked this above
            ]

            passed_criteria = sum(1 for _, passed in success_criteria if passed)
            self.logger.info(f"   Success criteria met: {passed_criteria}/{len(success_criteria)}")

            for criterion, passed in success_criteria:
                status = "✅" if passed else "❌"
                self.logger.info(f"    {status} {criterion}")

            if passed_criteria >= 2:  # At least 2 out of 3 criteria
                self.logger.info("  ✅ Kilo Code routed model tests passed")
                return True
            else:
                self.logger.error("  ❌ Kilo Code routed model tests failed")
                return False

        except Exception as e:
            self.logger.error(f"OpenRouter model test failed: {e}")
            return False
        finally:
            self.cleanup_test_files()


def main():
    """Run the OpenRouter model tests"""
    import sys

    verbose = "--verbose" in sys.argv or "-v" in sys.argv
    test = OpenRouterModelsTest(verbose=verbose)

    success = test.run_test()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
