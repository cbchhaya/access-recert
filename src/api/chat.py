"""
Conversational Interface for ARAS
=================================

LLM-powered chat assistant using Claude API with tool calling.

Author: Chiradeep Chhaya
"""

import json
import os
import sqlite3
from typing import List, Dict, Any, Optional
from datetime import datetime

# Load .env file if it exists
from dotenv import load_dotenv
env_path = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    ".env"
)
load_dotenv(env_path)

try:
    from anthropic import Anthropic
except ImportError:
    Anthropic = None

# Database path
DB_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "data", "aras.db"
)

# Tool definitions for Claude
TOOLS = [
    {
        "name": "search_employees",
        "description": "Search for employees by name, job title, team, or other attributes",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search query for employee name, email, or job title"
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of results to return",
                    "default": 10
                }
            },
            "required": ["query"]
        }
    },
    {
        "name": "get_employee_access",
        "description": "Get all access grants for a specific employee, including assurance scores",
        "input_schema": {
            "type": "object",
            "properties": {
                "employee_id": {
                    "type": "string",
                    "description": "The employee ID to look up"
                }
            },
            "required": ["employee_id"]
        }
    },
    {
        "name": "get_campaign_summary",
        "description": "Get summary statistics for a certification campaign",
        "input_schema": {
            "type": "object",
            "properties": {
                "campaign_id": {
                    "type": "string",
                    "description": "The campaign ID to get summary for"
                }
            },
            "required": ["campaign_id"]
        }
    },
    {
        "name": "get_low_assurance_items",
        "description": "Get review items with low assurance scores that need attention",
        "input_schema": {
            "type": "object",
            "properties": {
                "campaign_id": {
                    "type": "string",
                    "description": "The campaign ID to query"
                },
                "threshold": {
                    "type": "number",
                    "description": "Score threshold (default 50)",
                    "default": 50
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum results",
                    "default": 10
                }
            },
            "required": ["campaign_id"]
        }
    },
    {
        "name": "explain_assurance_score",
        "description": "Explain how an assurance score was calculated for a specific access grant",
        "input_schema": {
            "type": "object",
            "properties": {
                "review_item_id": {
                    "type": "string",
                    "description": "The review item ID to explain"
                }
            },
            "required": ["review_item_id"]
        }
    },
    {
        "name": "get_system_stats",
        "description": "Get overall system statistics including employee count, grants, campaigns",
        "input_schema": {
            "type": "object",
            "properties": {}
        }
    },
    {
        "name": "search_resources",
        "description": "Search for resources by name or system",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search query for resource name"
                },
                "sensitivity": {
                    "type": "string",
                    "description": "Filter by sensitivity level",
                    "enum": ["Public", "Internal", "Confidential", "Critical"]
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum results",
                    "default": 10
                }
            },
            "required": ["query"]
        }
    },
    {
        "name": "get_dormant_access",
        "description": "Find access grants that haven't been used recently",
        "input_schema": {
            "type": "object",
            "properties": {
                "days_threshold": {
                    "type": "integer",
                    "description": "Number of days without activity to be considered dormant",
                    "default": 90
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum results",
                    "default": 20
                }
            }
        }
    }
]


def get_db():
    """Get database connection."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def execute_tool(tool_name: str, arguments: Dict[str, Any]) -> str:
    """Execute a tool and return the result."""
    conn = get_db()
    cursor = conn.cursor()

    try:
        if tool_name == "search_employees":
            query = f"%{arguments.get('query', '')}%"
            limit = arguments.get('limit', 10)
            cursor.execute("""
                SELECT id, employee_number, full_name, email, job_title, job_family
                FROM employees
                WHERE full_name LIKE ? OR email LIKE ? OR job_title LIKE ?
                LIMIT ?
            """, (query, query, query, limit))
            rows = cursor.fetchall()
            return json.dumps([dict(r) for r in rows], indent=2)

        elif tool_name == "get_employee_access":
            emp_id = arguments.get('employee_id')
            # Get employee info
            cursor.execute("SELECT * FROM employees WHERE id = ?", (emp_id,))
            emp = cursor.fetchone()
            if not emp:
                return json.dumps({"error": "Employee not found"})

            # Get access grants with resources
            cursor.execute("""
                SELECT ag.id, ag.granted_at, r.name as resource_name,
                       r.sensitivity, r.resource_type, s.name as system_name
                FROM access_grants ag
                JOIN resources r ON ag.resource_id = r.id
                JOIN systems s ON r.system_id = s.id
                WHERE ag.employee_id = ?
                ORDER BY r.sensitivity DESC
            """, (emp_id,))
            grants = cursor.fetchall()

            return json.dumps({
                "employee": dict(emp),
                "total_grants": len(grants),
                "grants": [dict(g) for g in grants]
            }, indent=2)

        elif tool_name == "get_campaign_summary":
            camp_id = arguments.get('campaign_id')
            cursor.execute("SELECT * FROM campaigns WHERE id = ?", (camp_id,))
            campaign = cursor.fetchone()
            if not campaign:
                return json.dumps({"error": "Campaign not found"})

            cursor.execute("""
                SELECT
                    COUNT(*) as total,
                    SUM(CASE WHEN status = 'Auto-Approved' THEN 1 ELSE 0 END) as auto_approved,
                    SUM(CASE WHEN status = 'Pending' THEN 1 ELSE 0 END) as pending,
                    SUM(CASE WHEN status = 'Decided' THEN 1 ELSE 0 END) as decided,
                    AVG(assurance_score) as avg_score
                FROM review_items WHERE campaign_id = ?
            """, (camp_id,))
            stats = cursor.fetchone()

            return json.dumps({
                "campaign": dict(campaign),
                "statistics": dict(stats)
            }, indent=2)

        elif tool_name == "get_low_assurance_items":
            camp_id = arguments.get('campaign_id')
            threshold = arguments.get('threshold', 50)
            limit = arguments.get('limit', 10)

            cursor.execute("""
                SELECT ri.*, e.full_name, e.job_title, r.name as resource_name, r.sensitivity
                FROM review_items ri
                JOIN employees e ON ri.employee_id = e.id
                JOIN access_grants ag ON ri.access_grant_id = ag.id
                JOIN resources r ON ag.resource_id = r.id
                WHERE ri.campaign_id = ? AND ri.assurance_score < ? AND ri.status != 'Decided'
                ORDER BY ri.assurance_score ASC
                LIMIT ?
            """, (camp_id, threshold, limit))
            items = cursor.fetchall()

            return json.dumps([dict(i) for i in items], indent=2)

        elif tool_name == "explain_assurance_score":
            item_id = arguments.get('review_item_id')
            cursor.execute("""
                SELECT ri.*, e.full_name, e.job_title, e.job_code,
                       r.name as resource_name, r.sensitivity, r.resource_type
                FROM review_items ri
                JOIN employees e ON ri.employee_id = e.id
                JOIN access_grants ag ON ri.access_grant_id = ag.id
                JOIN resources r ON ag.resource_id = r.id
                WHERE ri.id = ?
            """, (item_id,))
            item = cursor.fetchone()

            if not item:
                return json.dumps({"error": "Review item not found"})

            item_dict = dict(item)

            # Get peer comparison
            cursor.execute("""
                SELECT COUNT(DISTINCT ag.employee_id) as peers_with_access
                FROM access_grants ag
                JOIN employees e ON ag.employee_id = e.id
                WHERE ag.resource_id = (SELECT resource_id FROM access_grants WHERE id = ?)
                  AND e.job_code = ?
            """, (item_dict['access_grant_id'], item_dict['job_code']))
            peer_info = cursor.fetchone()

            cursor.execute("""
                SELECT COUNT(*) as total_peers
                FROM employees WHERE job_code = ?
            """, (item_dict['job_code'],))
            total_peers = cursor.fetchone()

            explanation = {
                "review_item": item_dict,
                "score_breakdown": {
                    "overall_score": item_dict['assurance_score'],
                    "classification": item_dict['classification'],
                    "auto_eligible": bool(item_dict['auto_certify_eligible']),
                    "clustering_consensus": item_dict['clustering_consensus'],
                    "needs_clustering_review": bool(item_dict['needs_clustering_review'])
                },
                "peer_context": {
                    "peers_with_same_access": peer_info['peers_with_access'] if peer_info else 0,
                    "total_peers_in_role": total_peers['total_peers'] if total_peers else 0
                },
                "sensitivity_impact": f"Resource sensitivity is {item_dict['sensitivity']}, which affects the maximum possible score."
            }

            return json.dumps(explanation, indent=2)

        elif tool_name == "get_system_stats":
            stats = {}
            for table in ['employees', 'resources', 'access_grants', 'campaigns', 'review_items']:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                stats[table] = cursor.fetchone()[0]

            # Get active campaigns
            cursor.execute("SELECT COUNT(*) FROM campaigns WHERE status = 'Active'")
            stats['active_campaigns'] = cursor.fetchone()[0]

            return json.dumps(stats, indent=2)

        elif tool_name == "search_resources":
            query = f"%{arguments.get('query', '')}%"
            sensitivity = arguments.get('sensitivity')
            limit = arguments.get('limit', 10)

            if sensitivity:
                cursor.execute("""
                    SELECT r.*, s.name as system_name
                    FROM resources r
                    JOIN systems s ON r.system_id = s.id
                    WHERE r.name LIKE ? AND r.sensitivity = ?
                    LIMIT ?
                """, (query, sensitivity, limit))
            else:
                cursor.execute("""
                    SELECT r.*, s.name as system_name
                    FROM resources r
                    JOIN systems s ON r.system_id = s.id
                    WHERE r.name LIKE ?
                    LIMIT ?
                """, (query, limit))

            rows = cursor.fetchall()
            return json.dumps([dict(r) for r in rows], indent=2)

        elif tool_name == "get_dormant_access":
            days = arguments.get('days_threshold', 90)
            limit = arguments.get('limit', 20)

            cursor.execute("""
                SELECT ag.id, ag.employee_id, e.full_name,
                       r.name as resource_name, r.sensitivity,
                       a.last_activity_date
                FROM access_grants ag
                JOIN employees e ON ag.employee_id = e.id
                JOIN resources r ON ag.resource_id = r.id
                LEFT JOIN activity_summaries a ON ag.employee_id = a.employee_id AND ag.resource_id = a.resource_id
                WHERE a.last_activity_date < date('now', ? || ' days')
                   OR a.last_activity_date IS NULL
                ORDER BY r.sensitivity DESC
                LIMIT ?
            """, (f'-{days}', limit))
            rows = cursor.fetchall()
            return json.dumps([dict(r) for r in rows], indent=2)

        else:
            return json.dumps({"error": f"Unknown tool: {tool_name}"})

    finally:
        conn.close()


class ChatAssistant:
    """Chat assistant using Claude with tool calling."""

    def __init__(self, api_key: Optional[str] = None):
        if Anthropic is None:
            raise ImportError("anthropic package not installed. Run: pip install anthropic")

        self.api_key = api_key or os.environ.get('ANTHROPIC_API_KEY')
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY not set")

        self.client = Anthropic(api_key=self.api_key)
        self.conversation_history: List[Dict] = []

        self.system_prompt = """You are ARAS Assistant, an AI helper for the Access Recertification Assurance System.

You help users understand and manage access certification reviews. You can:
- Search for employees and view their access
- Explain assurance scores and how they're calculated
- Find items that need attention (low scores, dormant access)
- Provide campaign statistics and progress
- Answer questions about access patterns

When explaining assurance scores:
- High assurance (>80): Access is typical for this role, used recently, not highly sensitive
- Medium assurance (50-80): May need verification but not urgent
- Low assurance (<50): Needs careful review - could be outlier access, dormant, or highly sensitive

Key concepts:
- Peer typicality: How common is this access among similar employees
- Sensitivity ceiling: Critical/Confidential access caps the maximum score
- Usage factor: Recent activity increases confidence
- Clustering consensus: Multi-algorithm agreement on peer grouping

Be concise but helpful. If asked about specific employees or access, use the tools to look up real data."""

    def chat(self, user_message: str) -> str:
        """Process a chat message and return the response."""
        self.conversation_history.append({
            "role": "user",
            "content": user_message
        })

        # Initial API call
        response = self.client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=4096,
            system=self.system_prompt,
            tools=TOOLS,
            messages=self.conversation_history
        )

        # Handle tool use
        while response.stop_reason == "tool_use":
            # Extract tool calls
            tool_results = []
            for content in response.content:
                if content.type == "tool_use":
                    result = execute_tool(content.name, content.input)
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": content.id,
                        "content": result
                    })

            # Add assistant response and tool results
            self.conversation_history.append({
                "role": "assistant",
                "content": response.content
            })
            self.conversation_history.append({
                "role": "user",
                "content": tool_results
            })

            # Continue conversation
            response = self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=4096,
                system=self.system_prompt,
                tools=TOOLS,
                messages=self.conversation_history
            )

        # Extract final text response
        final_text = ""
        for content in response.content:
            if hasattr(content, 'text'):
                final_text += content.text

        # Add to history
        self.conversation_history.append({
            "role": "assistant",
            "content": response.content
        })

        return final_text

    def clear_history(self):
        """Clear conversation history."""
        self.conversation_history = []


# API endpoints
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter()

# Global assistant instance
_assistant: Optional[ChatAssistant] = None


class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    response: str
    timestamp: str


def get_assistant() -> ChatAssistant:
    """Get or create chat assistant."""
    global _assistant
    if _assistant is None:
        try:
            # Debug: print env status
            api_key = os.environ.get('ANTHROPIC_API_KEY')
            print(f"[Chat] ENV file path: {env_path}")
            print(f"[Chat] ENV file exists: {os.path.exists(env_path)}")
            print(f"[Chat] API key found: {'Yes' if api_key else 'No'}")
            if api_key:
                print(f"[Chat] API key starts with: {api_key[:10]}...")
            print(f"[Chat] Anthropic module loaded: {Anthropic is not None}")
            _assistant = ChatAssistant()
            print(f"[Chat] ChatAssistant created successfully")
        except Exception as e:
            import traceback
            print(f"[Chat] ERROR creating assistant: {type(e).__name__}: {str(e)}")
            traceback.print_exc()
            raise HTTPException(
                status_code=503,
                detail=f"Chat assistant not available: {type(e).__name__}: {str(e)}"
            )
    return _assistant


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Send a message to the chat assistant."""
    assistant = get_assistant()
    response = assistant.chat(request.message)
    return ChatResponse(
        response=response,
        timestamp=datetime.utcnow().isoformat()
    )


@router.post("/chat/clear")
async def clear_chat():
    """Clear chat history."""
    global _assistant
    if _assistant:
        _assistant.clear_history()
    return {"status": "cleared"}
