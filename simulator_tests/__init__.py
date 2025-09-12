"""
Communication Simulator Tests Package

This package contains individual test modules for the Zen MCP Communication Simulator.
Each test is in its own file for better organization and maintainability.
"""

from .base_test import BaseSimulatorTest
from .test_analyze_validation import AnalyzeValidationTest
from .test_basic_conversation import BasicConversationTest
from .test_chat_simple_validation import ChatSimpleValidationTest
from .test_codereview_validation import CodeReviewValidationTest
from .test_consensus_comprehensive import TestConsensusComprehensive
from .test_content_validation import ContentValidationTest
from .test_conversation_chain_validation import ConversationChainValidationTest
from .test_cross_tool_comprehensive import CrossToolComprehensiveTest
from .test_cross_tool_continuation import CrossToolContinuationTest
from .test_debug_certain_confidence import DebugCertainConfidenceTest
from .test_debug_validation import DebugValidationTest
from .test_line_number_validation import LineNumberValidationTest
from .test_logs_validation import LogsValidationTest
from .test_model_thinking_config import TestModelThinkingConfig
from .test_ollama_custom_url import OllamaCustomUrlTest
from .test_openrouter_fallback import OpenRouterFallbackTest
from .test_openrouter_models import OpenRouterModelsTest
from .test_per_tool_deduplication import PerToolDeduplicationTest
from .test_planner_continuation_history import PlannerContinuationHistoryTest
from .test_planner_validation import PlannerValidationTest
from .test_precommitworkflow_validation import PrecommitWorkflowValidationTest
from .test_prompt_size_limit_bug import PromptSizeLimitBugTest

# Redis validation test removed - no longer needed for standalone server
from .test_refactor_validation import RefactorValidationTest
from .test_secaudit_validation import SecauditValidationTest
from .test_testgen_validation import TestGenValidationTest
from .test_thinkdeep_validation import ThinkDeepWorkflowValidationTest
from .test_token_allocation_validation import TokenAllocationValidationTest
from .test_vision_capability import VisionCapabilityTest
from .test_xai_models import XAIModelsTest

# Test registry for dynamic loading
TEST_REGISTRY = {
    "basic_conversation": BasicConversationTest,
    "chat_validation": ChatSimpleValidationTest,
    "codereview_validation": CodeReviewValidationTest,
    "content_validation": ContentValidationTest,
    "per_tool_deduplication": PerToolDeduplicationTest,
    "cross_tool_continuation": CrossToolContinuationTest,
    "cross_tool_comprehensive": CrossToolComprehensiveTest,
    "line_number_validation": LineNumberValidationTest,
    "logs_validation": LogsValidationTest,
    # "redis_validation": RedisValidationTest,  # Removed - no longer needed for standalone server
    "model_thinking_config": TestModelThinkingConfig,
    "ollama_custom_url": OllamaCustomUrlTest,
    "openrouter_fallback": OpenRouterFallbackTest,
    "openrouter_models": OpenRouterModelsTest,
    "planner_validation": PlannerValidationTest,
    "planner_continuation_history": PlannerContinuationHistoryTest,
    "precommit_validation": PrecommitWorkflowValidationTest,
    "token_allocation_validation": TokenAllocationValidationTest,
    "testgen_validation": TestGenValidationTest,
    "thinkdeep_validation": ThinkDeepWorkflowValidationTest,
    "refactor_validation": RefactorValidationTest,
    "secaudit_validation": SecauditValidationTest,
    "debug_validation": DebugValidationTest,
    "debug_certain_confidence": DebugCertainConfidenceTest,
    "conversation_chain_validation": ConversationChainValidationTest,
    "vision_capability": VisionCapabilityTest,
    "xai_models": XAIModelsTest,
    # Consolidated comprehensive consensus test (aliases removed)
    "consensus_comprehensive": TestConsensusComprehensive,
    "analyze_validation": AnalyzeValidationTest,
    "prompt_size_limit_bug": PromptSizeLimitBugTest,
    # "o3_pro_expensive": O3ProExpensiveTest,  # COMMENTED OUT - too expensive to run by default
}

__all__ = [
    "BaseSimulatorTest",
    "BasicConversationTest",
    "ChatSimpleValidationTest",
    "CodeReviewValidationTest",
    "ContentValidationTest",
    "PerToolDeduplicationTest",
    "CrossToolContinuationTest",
    "CrossToolComprehensiveTest",
    "LineNumberValidationTest",
    "LogsValidationTest",
    "TestModelThinkingConfig",
    "OllamaCustomUrlTest",
    "OpenRouterFallbackTest",
    "OpenRouterModelsTest",
    "PlannerValidationTest",
    "PlannerContinuationHistoryTest",
    "PrecommitWorkflowValidationTest",
    "TokenAllocationValidationTest",
    "TestGenValidationTest",
    "ThinkDeepWorkflowValidationTest",
    "RefactorValidationTest",
    "SecauditValidationTest",
    "DebugValidationTest",
    "DebugCertainConfidenceTest",
    "ConversationChainValidationTest",
    "VisionCapabilityTest",
    "XAIModelsTest",
    "TestConsensusComprehensive",
    "AnalyzeValidationTest",
    "PromptSizeLimitBugTest",
    "TEST_REGISTRY",
]
