"""
ChatHub MCP Server

An MCP server that allows ChatGPT users to save conversations to an archive.
"""
import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional

import uvicorn
from pydantic import BaseModel, Field
from starlette.applications import Starlette
from starlette.routing import Mount
from mcp.server.fastmcp import FastMCP

# Archive directory (local S3 proxy)
ARCHIVE_DIR = Path(__file__).parent / "archive"


# Data models for the save_conversation tool
class Message(BaseModel):
    """A single message in the conversation."""
    role: str = Field(description="The role of the message author: 'user' or 'assistant'")
    content: str = Field(description="The text content of the message")


class SaveConversationInput(BaseModel):
    """Input schema for save_conversation tool."""
    title: str = Field(
        description="A descriptive title for the conversation"
    )
    summary: str = Field(
        description="A 2-3 sentence summary of what was discussed and any conclusions reached"
    )
    messages: list[Message] = Field(
        description="The conversation messages to save. Include all user and assistant messages from the conversation."
    )
    tags: Optional[list[str]] = Field(
        default=None,
        description="Optional tags to categorize the conversation (e.g., 'engineering', 'design', 'planning')"
    )
    key_points: Optional[list[str]] = Field(
        default=None,
        description="Optional list of key decisions, action items, or important points from the conversation"
    )


# Initialize the MCP server with host configuration for production
import os

# Get the host from environment or default to localhost
host = os.environ.get("MCP_HOST", "localhost")

# Set environment variable that MCP uses for transport security
os.environ["MCP_TRANSPORT_SECURITY_ALLOWED_HOSTS"] = host

mcp = FastMCP("ChatHub", host=host)


@mcp.tool()
def save_conversation(
    title: str,
    summary: str,
    messages: list[dict],
    tags: Optional[list[str]] = None,
    key_points: Optional[list[str]] = None,
) -> str:
    """
    Save the current conversation to the team archive.

    Use this tool when the user asks to save, archive, or export the conversation.

    CRITICAL REQUIREMENTS FOR MESSAGES:
    - Include the COMPLETE, VERBATIM, FULL text of EVERY message
    - Do NOT summarize, truncate, abbreviate, or paraphrase any message content
    - Do NOT use ellipsis (...) or "[continued]" or any other shortening
    - Copy the EXACT text of each message, no matter how long
    - Include ALL messages from the entire conversation, from the very first to the last

    Also include:
    - A descriptive title summarizing the conversation topic
    - A 2-3 sentence summary of what was discussed
    - Any relevant tags for categorization
    - Key decisions or action items discussed

    The conversation will be saved to the team's shared archive where it can be
    searched and referenced later. The full verbatim content is essential for
    accurate record-keeping and future reference.
    """
    # Generate unique ID and timestamp
    conversation_id = str(uuid.uuid4())
    saved_at = datetime.utcnow()
    date_str = saved_at.strftime("%Y-%m-%d")

    # Build the payload
    payload = {
        "id": conversation_id,
        "title": title,
        "summary": summary,
        "messages": messages,
        "tags": tags or [],
        "key_points": key_points or [],
        "saved_at": saved_at.isoformat(),
        "message_count": len(messages),
    }

    # Create directory structure: archive/{date}/
    save_dir = ARCHIVE_DIR / date_str
    save_dir.mkdir(parents=True, exist_ok=True)

    # Write JSON file
    file_path = save_dir / f"{conversation_id}.json"
    with open(file_path, "w") as f:
        json.dump(payload, f, indent=2, default=str)

    # Log to console
    print("\n" + "=" * 60)
    print("CONVERSATION SAVED")
    print("=" * 60)
    print(f"ID:       {conversation_id}")
    print(f"Title:    {title}")
    print(f"Messages: {len(messages)}")
    print(f"Tags:     {tags or []}")
    print(f"File:     {file_path}")
    print("=" * 60 + "\n")

    return json.dumps({
        "status": "success",
        "id": conversation_id,
        "title": title,
        "message_count": len(messages),
        "saved_at": saved_at.isoformat(),
        "file_path": str(file_path),
    })

# Create Starlette app with SSE endpoint mounted
app = Starlette(
    routes=[
        Mount("/", app=mcp.sse_app()),
    ]
)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    print(f"Starting ChatHub MCP Server on port {port}...")
    print(f"SSE endpoint available at: http://localhost:{port}/sse")
    uvicorn.run(app, host="0.0.0.0", port=port)
