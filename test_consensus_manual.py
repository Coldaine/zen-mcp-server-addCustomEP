#!/usr/bin/env python3
"""
Manual test script for consensus tool with qwen3:0.6b in different roles
"""

import asyncio
import json
import logging
import os
import sys

# Add project root to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def setup_environment():
    """Setup the test environment"""
    # Set custom API URL for Ollama
    os.environ["CUSTOM_API_URL"] = "http://localhost:11434/v1"
    # Enable saving consensus outputs to markdown
    os.environ["SAVE_CONSENSUS_OUTPUTS"] = "true"
    logger.info("Environment configured for Ollama at http://localhost:11434/v1")
    logger.info("Markdown output saving enabled")


def test_consensus_tool():
    """Test consensus tool with qwen3:0.6b in different roles"""
    try:
        # Import required modules
        from server import TOOLS, configure_providers
        from utils.model_context import ModelContext

        # Configure providers
        configure_providers()
        logger.info("Providers configured successfully")

        # Get consensus tool
        if "consensus" not in TOOLS:
            logger.error("Consensus tool not found in available tools")
            return False

        consensus_tool = TOOLS["consensus"]
        logger.info("Consensus tool loaded successfully")

        # Create test parameters
        test_params = {
            "step": "Should we implement OAuth2 or stick with simple session-based authentication for our web application?",
            "step_number": 1,
            "total_steps": 1,
            "next_step_required": False,
            "findings": "Need to evaluate OAuth2 vs session-based authentication for our web app",
            "models": [
                {
                    "model": "qwen3:0.6b",
                    "stance": "for",
                    "stance_prompt": "Focus on OAuth2 benefits: security, scalability, and industry standards.",
                },
                {
                    "model": "qwen3:0.6b",
                    "stance": "against",
                    "stance_prompt": "Focus on OAuth2 complexity: implementation challenges and simpler alternatives.",
                },
                {
                    "model": "qwen3:0.6b",
                    "stance": "neutral",
                    "stance_prompt": "Provide balanced analysis considering both benefits and drawbacks of OAuth2 vs session-based auth.",
                },
            ],
        }

        # Add model context
        model_context = ModelContext("qwen3:0.6b")
        test_params["_model_context"] = model_context
        test_params["_resolved_model_name"] = "qwen3:0.6b"
        test_params["model"] = "qwen3:0.6b"

        logger.info("Executing consensus tool with qwen3:0.6b in 3 roles (for, against, neutral)...")

        # Execute tool
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(consensus_tool.execute(test_params))

        # Process results
        if result and len(result) > 0:
            response_text = result[0].text if hasattr(result[0], "text") else str(result[0])
            logger.info("Consensus tool executed successfully")

            # Parse and display response
            try:
                response_data = json.loads(response_text)
                print("\n" + "=" * 80)
                print("CONSENSUS TOOL RESPONSE")
                print("=" * 80)
                print(json.dumps(response_data, indent=2, ensure_ascii=False))

                # Extract individual model responses
                if "all_model_responses" in response_data:
                    print("\n" + "=" * 80)
                    print("INDIVIDUAL MODEL RESPONSES")
                    print("=" * 80)
                    for i, model_response in enumerate(response_data["all_model_responses"]):
                        print(f"\n--- Model {i+1}: {model_response['model']} ({model_response['stance']}) ---")
                        if model_response.get("status") == "success":
                            content = model_response.get("content", "")
                            if content is None:
                                content = "No content returned"
                            print(f"Content: {content[:500]}...")
                        else:
                            print(f"Error: {model_response.get('error_message', 'Unknown error')}")

                return True
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse response as JSON: {e}")
                print("Raw response:")
                print(response_text)
                return False
        else:
            logger.error("No response from consensus tool")
            return False

    except Exception as e:
        logger.error(f"Error testing consensus tool: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("Testing consensus tool with qwen3:0.6b in different roles...")
    setup_environment()

    success = test_consensus_tool()

    if success:
        print("\n" + "=" * 80)
        print("TEST COMPLETED SUCCESSFULLY")
        print("=" * 80)
    else:
        print("\n" + "=" * 80)
        print("TEST FAILED")
        print("=" * 80)
        sys.exit(1)
