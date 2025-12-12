"""
Shared Consciousness Web UI

A simple web interface to browse saved conversations.
Run on port 8080 alongside the MCP server on 8000.
"""
import json
from datetime import datetime
from pathlib import Path

import uvicorn
from starlette.applications import Starlette
from starlette.responses import HTMLResponse, JSONResponse
from starlette.routing import Route

ARCHIVE_DIR = Path(__file__).parent / "archive"

# Dummy data for trending/roadmap features
DUMMY_TRENDING = [
    {"id": "trending-1", "title": "Q4 Planning Strategy", "views": 342, "saves": 28, "team": "Product"},
    {"id": "trending-2", "title": "API Rate Limiting Discussion", "views": 289, "saves": 45, "team": "Engineering"},
    {"id": "trending-3", "title": "Customer Onboarding Flow", "views": 256, "saves": 19, "team": "Growth"},
    {"id": "trending-4", "title": "Brand Guidelines Update", "views": 198, "saves": 32, "team": "Design"},
    {"id": "trending-5", "title": "Incident Postmortem: Dec 5", "views": 187, "saves": 67, "team": "SRE"},
]

ROADMAP_FEATURES = [
    {"name": "Full-text Search", "status": "coming-soon", "description": "Search across all conversations"},
    {"name": "Team Workspaces", "status": "coming-soon", "description": "Organize by team or project"},
    {"name": "AI Auto-tagging", "status": "planned", "description": "Automatic categorization"},
    {"name": "Slack Integration", "status": "planned", "description": "Share directly to channels"},
    {"name": "Analytics Dashboard", "status": "planned", "description": "Usage insights and trends"},
    {"name": "Export to Notion/Confluence", "status": "exploring", "description": "Sync to your wiki"},
]


def get_all_conversations():
    """Load all conversations from archive."""
    conversations = []
    if ARCHIVE_DIR.exists():
        for date_dir in sorted(ARCHIVE_DIR.iterdir(), reverse=True):
            if date_dir.is_dir():
                for json_file in sorted(date_dir.glob("*.json"), reverse=True):
                    try:
                        with open(json_file) as f:
                            conv = json.load(f)
                            conv["_file"] = str(json_file)
                            conversations.append(conv)
                    except Exception:
                        pass
    return conversations


def get_conversation(conv_id: str):
    """Load a specific conversation by ID."""
    if ARCHIVE_DIR.exists():
        for date_dir in ARCHIVE_DIR.iterdir():
            if date_dir.is_dir():
                for json_file in date_dir.glob("*.json"):
                    if conv_id in json_file.name:
                        with open(json_file) as f:
                            return json.load(f)
    return None


# HTML Templates
def base_html(title: str, content: str, active: str = "home") -> str:
    nav_items = [
        ("home", "/", "Archive"),
        ("trending", "/trending", "Trending"),
        ("roadmap", "/roadmap", "Roadmap"),
    ]
    nav_html = "".join([
        f'<a href="{href}" class="nav-link {"active" if key == active else ""}">{label}</a>'
        for key, href, label in nav_items
    ])

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title} - Shared Consciousness</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #0a0a0a;
            color: #e5e5e5;
            min-height: 100vh;
        }}
        .container {{ max-width: 900px; margin: 0 auto; padding: 20px; }}

        /* Header */
        header {{
            border-bottom: 1px solid #222;
            padding: 16px 0;
            margin-bottom: 32px;
        }}
        .header-inner {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            max-width: 900px;
            margin: 0 auto;
            padding: 0 20px;
        }}
        .logo {{
            font-size: 20px;
            font-weight: 600;
            color: #fff;
            text-decoration: none;
        }}
        .logo span {{ color: #3b82f6; }}
        nav {{ display: flex; gap: 8px; }}
        .nav-link {{
            color: #888;
            text-decoration: none;
            padding: 8px 16px;
            border-radius: 6px;
            font-size: 14px;
            transition: all 0.2s;
        }}
        .nav-link:hover {{ color: #e5e5e5; background: #1a1a1a; }}
        .nav-link.active {{ color: #fff; background: #1a1a1a; }}

        /* Page titles */
        h1 {{ font-size: 28px; font-weight: 600; margin-bottom: 8px; }}
        .subtitle {{ color: #666; margin-bottom: 24px; }}

        /* Conversation cards */
        .conv-list {{ display: flex; flex-direction: column; gap: 12px; }}
        .conv-card {{
            background: #111;
            border: 1px solid #222;
            border-radius: 8px;
            padding: 16px;
            text-decoration: none;
            color: inherit;
            transition: all 0.2s;
        }}
        .conv-card:hover {{ border-color: #333; background: #151515; }}
        .conv-title {{ font-size: 16px; font-weight: 500; margin-bottom: 6px; }}
        .conv-summary {{ color: #888; font-size: 14px; line-height: 1.5; margin-bottom: 12px; }}
        .conv-meta {{ display: flex; gap: 16px; font-size: 12px; color: #555; }}
        .conv-meta span {{ display: flex; align-items: center; gap: 4px; }}
        .tag {{
            display: inline-block;
            background: #1a1a2e;
            color: #6366f1;
            padding: 2px 8px;
            border-radius: 4px;
            font-size: 11px;
            margin-right: 4px;
        }}

        /* Detail view */
        .back-link {{ color: #3b82f6; text-decoration: none; font-size: 14px; margin-bottom: 16px; display: inline-block; }}
        .back-link:hover {{ text-decoration: underline; }}
        .detail-header {{ margin-bottom: 24px; }}
        .detail-tags {{ margin: 12px 0; }}
        .key-points {{ background: #111; border-radius: 8px; padding: 16px; margin-bottom: 24px; }}
        .key-points h3 {{ font-size: 14px; color: #888; margin-bottom: 12px; }}
        .key-points ul {{ padding-left: 20px; }}
        .key-points li {{ color: #ccc; margin-bottom: 6px; font-size: 14px; }}

        /* Messages */
        .messages {{ display: flex; flex-direction: column; gap: 16px; }}
        .message {{ padding: 16px; border-radius: 8px; }}
        .message.user {{ background: #1a1a2e; border-left: 3px solid #6366f1; }}
        .message.assistant {{ background: #111; border-left: 3px solid #22c55e; }}
        .message-role {{ font-size: 11px; text-transform: uppercase; color: #666; margin-bottom: 8px; font-weight: 600; }}
        .message-content {{ font-size: 14px; line-height: 1.6; white-space: pre-wrap; }}

        /* Trending */
        .trending-card {{
            background: #111;
            border: 1px solid #222;
            border-radius: 8px;
            padding: 16px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        .trending-info h3 {{ font-size: 15px; margin-bottom: 4px; }}
        .trending-team {{ font-size: 12px; color: #666; }}
        .trending-stats {{ display: flex; gap: 16px; font-size: 13px; color: #888; }}

        /* Roadmap */
        .roadmap-item {{
            background: #111;
            border: 1px solid #222;
            border-radius: 8px;
            padding: 16px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        .roadmap-info h3 {{ font-size: 15px; margin-bottom: 4px; }}
        .roadmap-desc {{ font-size: 13px; color: #666; }}
        .status-badge {{
            font-size: 11px;
            padding: 4px 10px;
            border-radius: 12px;
            font-weight: 500;
        }}
        .status-badge.coming-soon {{ background: #1e3a2f; color: #22c55e; }}
        .status-badge.planned {{ background: #1e293b; color: #3b82f6; }}
        .status-badge.exploring {{ background: #2d2418; color: #f59e0b; }}

        /* Empty state */
        .empty {{ text-align: center; padding: 60px 20px; color: #555; }}
        .empty h2 {{ color: #888; margin-bottom: 8px; }}
    </style>
</head>
<body>
    <header>
        <div class="header-inner">
            <a href="/" class="logo">Shared <span>Consciousness</span></a>
            <nav>{nav_html}</nav>
        </div>
    </header>
    <div class="container">
        {content}
    </div>
</body>
</html>"""


async def home(request):
    conversations = get_all_conversations()

    if not conversations:
        content = """
        <h1>Conversation Archive</h1>
        <p class="subtitle">Your team's saved ChatGPT conversations</p>
        <div class="empty">
            <h2>No conversations yet</h2>
            <p>Save a conversation from ChatGPT to see it here.</p>
        </div>
        """
    else:
        cards = []
        for conv in conversations:
            tags_html = "".join([f'<span class="tag">{t}</span>' for t in conv.get("tags", [])[:3]])
            saved = conv.get("saved_at", "")[:10]
            cards.append(f"""
            <a href="/conversation/{conv['id']}" class="conv-card">
                <div class="conv-title">{conv.get('title', 'Untitled')}</div>
                <div class="conv-summary">{conv.get('summary', '')[:200]}{'...' if len(conv.get('summary', '')) > 200 else ''}</div>
                <div style="margin-bottom: 8px;">{tags_html}</div>
                <div class="conv-meta">
                    <span>{conv.get('message_count', 0)} messages</span>
                    <span>{saved}</span>
                </div>
            </a>
            """)

        content = f"""
        <h1>Conversation Archive</h1>
        <p class="subtitle">Your team's saved ChatGPT conversations</p>
        <div class="conv-list">
            {"".join(cards)}
        </div>
        """

    return HTMLResponse(base_html("Archive", content, "home"))


async def conversation_detail(request):
    conv_id = request.path_params["conv_id"]
    conv = get_conversation(conv_id)

    if not conv:
        return HTMLResponse(base_html("Not Found", "<h1>Conversation not found</h1>", "home"), status_code=404)

    tags_html = "".join([f'<span class="tag">{t}</span>' for t in conv.get("tags", [])])

    key_points_html = ""
    if conv.get("key_points"):
        points = "".join([f"<li>{p}</li>" for p in conv["key_points"]])
        key_points_html = f"""
        <div class="key-points">
            <h3>Key Points</h3>
            <ul>{points}</ul>
        </div>
        """

    messages_html = []
    for msg in conv.get("messages", []):
        role = msg.get("role", "user")
        content = msg.get("content", "")
        messages_html.append(f"""
        <div class="message {role}">
            <div class="message-role">{role}</div>
            <div class="message-content">{content}</div>
        </div>
        """)

    content = f"""
    <a href="/" class="back-link">&larr; Back to Archive</a>
    <div class="detail-header">
        <h1>{conv.get('title', 'Untitled')}</h1>
        <p class="subtitle">{conv.get('summary', '')}</p>
        <div class="detail-tags">{tags_html}</div>
        <div class="conv-meta">
            <span>{conv.get('message_count', 0)} messages</span>
            <span>Saved {conv.get('saved_at', '')[:10]}</span>
        </div>
    </div>
    {key_points_html}
    <h2 style="font-size: 18px; margin-bottom: 16px;">Conversation</h2>
    <div class="messages">
        {"".join(messages_html)}
    </div>
    """

    return HTMLResponse(base_html(conv.get("title", "Conversation"), content, "home"))


async def trending(request):
    cards = []
    for i, item in enumerate(DUMMY_TRENDING, 1):
        cards.append(f"""
        <div class="trending-card">
            <div class="trending-info">
                <h3>{i}. {item['title']}</h3>
                <div class="trending-team">{item['team']}</div>
            </div>
            <div class="trending-stats">
                <span>{item['views']} views</span>
                <span>{item['saves']} saves</span>
            </div>
        </div>
        """)

    content = f"""
    <h1>Trending Conversations</h1>
    <p class="subtitle">Most viewed across your organization this week</p>
    <div class="conv-list">
        {"".join(cards)}
    </div>
    """

    return HTMLResponse(base_html("Trending", content, "trending"))


async def roadmap(request):
    items = []
    for feature in ROADMAP_FEATURES:
        status_class = feature["status"]
        status_label = feature["status"].replace("-", " ").title()
        items.append(f"""
        <div class="roadmap-item">
            <div class="roadmap-info">
                <h3>{feature['name']}</h3>
                <div class="roadmap-desc">{feature['description']}</div>
            </div>
            <span class="status-badge {status_class}">{status_label}</span>
        </div>
        """)

    content = f"""
    <h1>Roadmap</h1>
    <p class="subtitle">What we're building next</p>
    <div class="conv-list">
        {"".join(items)}
    </div>
    """

    return HTMLResponse(base_html("Roadmap", content, "roadmap"))


async def api_conversations(request):
    """JSON API endpoint for conversations."""
    return JSONResponse(get_all_conversations())


app = Starlette(
    routes=[
        Route("/", home),
        Route("/conversation/{conv_id}", conversation_detail),
        Route("/trending", trending),
        Route("/roadmap", roadmap),
        Route("/api/conversations", api_conversations),
    ]
)

if __name__ == "__main__":
    print("Starting Shared Consciousness Web UI...")
    print("UI available at: http://localhost:8080")
    uvicorn.run(app, host="0.0.0.0", port=8080)
