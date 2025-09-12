"""
Utility functions for saving consensus responses to markdown files
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any


def save_consensus_response_to_markdown(response_data: dict[str, Any], output_dir: str = "consensus_outputs") -> str:
    """
    Save consensus response data to a markdown file with formatted output.

    Args:
        response_data: The consensus response data dictionary
        output_dir: Directory to save the markdown files (default: "consensus_outputs")

    Returns:
        str: Path to the saved markdown file
    """
    # Create output directory if it doesn't exist
    Path(output_dir).mkdir(exist_ok=True)

    # Generate filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"consensus_response_{timestamp}.md"
    filepath = os.path.join(output_dir, filename)

    # Extract key information
    initial_prompt = response_data.get("complete_consensus", {}).get("initial_prompt", "Unknown prompt")
    models_consulted = response_data.get("complete_consensus", {}).get("models_consulted", [])
    total_responses = response_data.get("complete_consensus", {}).get("total_responses", 0)

    # Create markdown content
    md_content = []
    md_content.append("# Consensus Tool Response")
    md_content.append("")
    md_content.append(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    md_content.append("")
    md_content.append("## Initial Prompt")
    md_content.append(f"> {initial_prompt}")
    md_content.append("")
    md_content.append("## Consulted Models")
    for model in models_consulted:
        md_content.append(f"- {model}")
    md_content.append("")
    md_content.append(f"**Total Responses:** {total_responses}")
    md_content.append("")

    # Add individual model responses
    md_content.append("## Individual Model Responses")
    md_content.append("")

    all_model_responses = response_data.get("all_model_responses", response_data.get("accumulated_responses", []))

    for i, response in enumerate(all_model_responses, 1):
        model_name = response.get("model", "Unknown")
        stance = response.get("stance", "Unknown")
        status = response.get("status", "Unknown")

        md_content.append(f"### Response {i}: {model_name} ({stance})")
        md_content.append(f"**Status:** {status}")
        md_content.append("")

        if status == "success":
            content = response.get("content", "")
            # Handle case where content is None
            if content is None:
                content = ""
            # If content is markdown, include it directly
            if content.strip().startswith("##"):
                md_content.append(content)
            else:
                # Format as markdown quote
                md_content.append("> " + content.replace("\n", "\n> "))
        else:
            error_msg = response.get("error_message", "Unknown error")
            md_content.append(f"**Error:** {error_msg}")

        md_content.append("")
        md_content.append("---")
        md_content.append("")

    # Add raw JSON data
    md_content.append("## Raw Response Data")
    md_content.append("```json")
    md_content.append(json.dumps(response_data, indent=2, ensure_ascii=False))
    md_content.append("```")

    # Write to file
    with open(filepath, "w", encoding="utf-8") as f:
        f.write("\n".join(md_content))

    return filepath


def save_model_response_to_markdown(model_response: dict[str, Any], output_dir: str = "model_outputs") -> str:
    """
    Save individual model response to a markdown file.

    Args:
        model_response: Individual model response dictionary
        output_dir: Directory to save the markdown files (default: "model_outputs")

    Returns:
        str: Path to the saved markdown file
    """
    # Create output directory if it doesn't exist
    Path(output_dir).mkdir(exist_ok=True)

    # Generate filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    model_name = model_response.get("model", "unknown")
    stance = model_response.get("stance", "unknown")
    filename = f"{model_name}_{stance}_{timestamp}.md"
    filepath = os.path.join(output_dir, filename)

    # Create markdown content
    md_content = []
    md_content.append(f"# {model_name} Response ({stance})")
    md_content.append("")
    md_content.append(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    md_content.append(f"**Status:** {model_response.get('status', 'Unknown')}")
    md_content.append("")

    if model_response.get("status") == "success":
        content = model_response.get("content", "")
        # Handle case where content is None
        if content is None:
            content = ""
        md_content.append("## Response Content")
        md_content.append("")
        # If content is already markdown format, include it directly
        if content.strip().startswith("##"):
            md_content.append(content)
        else:
            md_content.append(content)
    else:
        error_msg = model_response.get("error_message", "Unknown error")
        md_content.append("## Error")
        md_content.append(f"{error_msg}")

    # Add metadata if available
    if "latency_ms" in model_response:
        md_content.append("")
        md_content.append(f"**Latency:** {model_response['latency_ms']} ms")

    # Add raw data
    md_content.append("")
    md_content.append("## Raw Data")
    md_content.append("```json")
    md_content.append(json.dumps(model_response, indent=2, ensure_ascii=False))
    md_content.append("```")

    # Write to file
    with open(filepath, "w", encoding="utf-8") as f:
        f.write("\n".join(md_content))

    return filepath
