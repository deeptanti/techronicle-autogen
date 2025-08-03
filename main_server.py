"""
Enhanced FastAPI Server with Agent Information API
Adds endpoint to fetch agent system prompts directly from personality files
"""

import warnings
# Suppress warnings first
warnings.filterwarnings("ignore", message="flaml.automl is not available")
warnings.filterwarnings("ignore", message=".*API key specified is not a valid OpenAI format.*")

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
import json
import asyncio
import threading
import time
from datetime import datetime
from typing import List, Dict, Any
import uuid
from pathlib import Path
import concurrent.futures

# Import your newsroom
from agents.newsroom import TechronicleNewsroom
from utils.config import config

# Import agent personalities to get their system messages
from agents.personalities.gary_poussin import create_gary_agent
from agents.personalities.aravind_rajen import create_aravind_agent
from agents.personalities.tijana_jekic import create_tijana_agent
from agents.personalities.jerin_sojan import create_jerin_agent
from agents.personalities.aayushi_patel import create_aayushi_agent
from agents.personalities.james_guerra import create_james_agent

app = FastAPI(title="Techronicle AutoGen Live Newsroom")

# Setup static files and templates
static_dir = Path("static")
templates_dir = Path("templates")

# Create directories if they don't exist
static_dir.mkdir(exist_ok=True)
templates_dir.mkdir(exist_ok=True)

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# WebSocket connections manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.newsroom_instance = None
        self.session_running = False
        self.conversation_messages = []
        self.loop = None
        self.session_start_time = None
        self.step_times = {}

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        
        # Send current conversation if available
        if self.conversation_messages:
            await websocket.send_json({
                "type": "conversation_history",
                "messages": self.conversation_messages
            })

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        dead_connections = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except:
                dead_connections.append(connection)
        
        # Remove dead connections
        for conn in dead_connections:
            if conn in self.active_connections:
                self.active_connections.remove(conn)

    async def send_status(self, status: str, details: str = ""):
        message = {
            "type": "status_update",
            "status": status,
            "details": details,
            "timestamp": datetime.now().isoformat()
        }
        await self.broadcast(message)

    def send_status_sync(self, status: str, details: str = ""):
        """Thread-safe status sending"""
        if self.loop and not self.loop.is_closed():
            try:
                asyncio.run_coroutine_threadsafe(
                    self.send_status(status, details), 
                    self.loop
                ).result(timeout=1.0)
            except:
                pass

    def broadcast_message_sync(self, message: dict):
        """Thread-safe message broadcasting"""
        if self.loop and not self.loop.is_closed():
            try:
                asyncio.run_coroutine_threadsafe(
                    self.broadcast(message), 
                    self.loop
                ).result(timeout=1.0)
            except:
                pass

manager = ConnectionManager()

@app.on_event("startup")
async def startup_event():
    """Store the event loop for thread-safe operations"""
    manager.loop = asyncio.get_event_loop()

@app.get("/", response_class=HTMLResponse)
async def get_dashboard(request: Request):
    """Serve the main dashboard"""
    return templates.TemplateResponse("dashboard.html", {"request": request})

@app.get("/api/agents")
async def get_agents_info():
    """Get information about all agents including their system prompts"""
    
    # Create temporary agent instances to get their system messages
    agent_creators = {
        "gary": create_gary_agent,
        "aravind": create_aravind_agent,
        "tijana": create_tijana_agent,
        "jerin": create_jerin_agent,
        "aayushi": create_aayushi_agent,
        "james": create_james_agent
    }
    
    agents_info = {}
    
    for agent_key, creator_func in agent_creators.items():
        try:
            # Create agent instance
            agent = creator_func()
            
            # Extract agent information
            agents_info[agent_key] = {
                "name": agent.name,
                "description": agent.description,
                "system_message": agent.system_message,
                "max_consecutive_auto_reply": agent.max_consecutive_auto_reply,
                "llm_config": {
                    "model": agent.llm_config.get("model", "unknown"),
                    "temperature": agent.llm_config.get("temperature", 0.7)
                }
            }
            
        except Exception as e:
            # Fallback info if agent creation fails
            agents_info[agent_key] = {
                "name": agent_key.title(),
                "description": f"Error loading {agent_key}: {str(e)}",
                "system_message": f"Could not load system message for {agent_key}",
                "max_consecutive_auto_reply": 0,
                "llm_config": {"model": "unknown", "temperature": 0.7}
            }
    
    return agents_info

@app.get("/api/agent/{agent_key}")
async def get_agent_info(agent_key: str):
    """Get detailed information about a specific agent"""
    
    agent_creators = {
        "gary": create_gary_agent,
        "aravind": create_aravind_agent,
        "tijana": create_tijana_agent,
        "jerin": create_jerin_agent,
        "aayushi": create_aayushi_agent,
        "james": create_james_agent
    }
    
    if agent_key not in agent_creators:
        return {"error": f"Agent '{agent_key}' not found"}
    
    try:
        # Create agent instance
        agent = agent_creators[agent_key]()
        
        # Agent metadata
        agent_metadata = {
            "gary": {"full_name": "Gary Poussin", "role": "Beat Reporter", "age": 28, "color": "#2196f3", "emoji": "📰"},
            "aravind": {"full_name": "Dr. Aravind Rajen", "role": "Senior Market Analyst", "age": 34, "color": "#9c27b0", "emoji": "🔍"},
            "tijana": {"full_name": "Tijana Jekic", "role": "Copy Editor & Fact Checker", "age": 31, "color": "#ff9800", "emoji": "✏️"},
            "jerin": {"full_name": "Jerin Sojan", "role": "Managing Editor", "age": 38, "color": "#4caf50", "emoji": "⚖️"},
            "aayushi": {"full_name": "Aayushi Patel", "role": "Audience Development Editor", "age": 26, "color": "#e91e63", "emoji": "📱"},
            "james": {"full_name": "James Guerra", "role": "Digital Publishing Manager", "age": 29, "color": "#8bc34a", "emoji": "🚀"}
        }
        
        metadata = agent_metadata.get(agent_key, {
            "full_name": agent_key.title(),
            "role": "Team Member",
            "age": 30,
            "color": "#666666",
            "emoji": "🤖"
        })
        
        return {
            "key": agent_key,
            "name": agent.name,
            "full_name": metadata["full_name"],
            "role": metadata["role"],
            "age": metadata["age"],
            "color": metadata["color"],
            "emoji": metadata["emoji"],
            "description": agent.description,
            "system_message": agent.system_message,
            "max_consecutive_auto_reply": agent.max_consecutive_auto_reply,
            "llm_config": {
                "model": agent.llm_config.get("model", "unknown"),
                "temperature": agent.llm_config.get("temperature", 0.7)
            }
        }
        
    except Exception as e:
        return {"error": f"Could not load agent '{agent_key}': {str(e)}"}

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # Keep connection alive and listen for client messages
            data = await websocket.receive_json()
            
            if data["type"] == "start_session":
                if not manager.session_running:
                    await start_newsroom_session(data.get("articles_count", 5))
                else:
                    await websocket.send_json({
                        "type": "error",
                        "message": "Session already running"
                    })
            
            elif data["type"] == "stop_session":
                if manager.session_running:
                    manager.session_running = False
                    await manager.send_status("stopped", "Session stopped by user")
                    
    except WebSocketDisconnect:
        manager.disconnect(websocket)

async def start_newsroom_session(articles_count: int):
    """Start newsroom session with proper async handling"""
    if manager.session_running:
        return
    
    manager.session_running = True
    manager.conversation_messages = []
    manager.session_start_time = datetime.now()
    manager.step_times = {}
    
    await manager.send_status("initializing", "Setting up editorial meeting...")
    
    # Use thread pool executor for CPU-intensive work
    executor = concurrent.futures.ThreadPoolExecutor(max_workers=2)
    
    def run_newsroom():
        try:
            # Initialize newsroom
            session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
            manager.newsroom_instance = TechronicleNewsroom(session_id=session_id)
            
            # Send initialization complete (thread-safe)
            manager.send_status_sync("initialized", f"Editorial meeting {session_id} ready")
            
            # Start monitoring conversation
            monitor_thread = threading.Thread(target=monitor_conversation, daemon=True)
            monitor_thread.start()
            
            # Run session
            manager.send_status_sync("running", "Editorial discussion in progress...")
            results = manager.newsroom_instance.run_editorial_session(articles_count)
            
            # Session completed
            success = results.get("success", False)
            status = "completed" if success else "failed"
            details = f"Published {results.get('articles_published', 0)} articles" if success else results.get('error', 'Unknown error')
            
            manager.send_status_sync(status, details)
            manager.session_running = False
            
        except Exception as e:
            manager.send_status_sync("error", f"Session failed: {str(e)}")
            manager.session_running = False
    
    # Run in thread pool
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(executor, run_newsroom)

def monitor_conversation():
    """Monitor conversation and broadcast new messages (thread-safe)"""
    last_message_count = 0
    
    while manager.session_running and manager.newsroom_instance:
        try:
            if hasattr(manager.newsroom_instance, 'group_chat') and manager.newsroom_instance.group_chat.messages:
                current_messages = manager.newsroom_instance.group_chat.messages
                current_count = len(current_messages)
                
                if current_count > last_message_count:
                    # New messages found
                    new_messages = current_messages[last_message_count:]
                    
                    for msg in new_messages:
                        formatted_message = format_message_for_ui(msg)
                        manager.conversation_messages.append(formatted_message)
                        
                        # Broadcast new message (thread-safe)
                        manager.broadcast_message_sync({
                            "type": "new_message",
                            "message": formatted_message
                        })
                    
                    last_message_count = current_count
            
            time.sleep(1)  # Check every second
            
        except Exception as e:
            print(f"Monitor error: {e}")
            break

def format_message_for_ui(msg: dict) -> dict:
    """Enhanced message formatting for UI display"""
    speaker = msg.get("name", "Unknown")
    content = msg.get("content", "")
    
    # Enhanced agent info mapping
    agent_info = {
        "Gary": {
            "designation": "Beat Reporter",
            "color": "#2196f3",
            "emoji": "📰"
        },
        "Aravind": {
            "designation": "Market Analyst", 
            "color": "#9c27b0",
            "emoji": "🔍"
        },
        "Tijana": {
            "designation": "Copy Editor",
            "color": "#ff9800", 
            "emoji": "✏️"
        },
        "Jerin": {
            "designation": "Managing Editor",
            "color": "#4caf50",
            "emoji": "⚖️"
        },
        "Aayushi": {
            "designation": "Audience Editor",
            "color": "#e91e63",
            "emoji": "📱"
        },
        "James": {
            "designation": "Publishing Manager",
            "color": "#8bc34a",
            "emoji": "🚀"
        }
    }
    
    info = agent_info.get(speaker, {
        "designation": "Team Member",
        "color": "#757575",
        "emoji": "🤖"
    })
    
    # Enhanced message type detection with meeting context
    message_type = "discussion"
    
    # Make content sound more like a meeting
    meeting_content = enhance_meeting_language(content)
    
    # Detect specific message types
    if any(keyword in content.lower() for keyword in ["decision", "approve", "publish", "override", "executive", "final call"]):
        message_type = "decision"
    elif any(keyword in content.lower() for keyword in ["tool", "processing", "collected", "analyzed", "scraping", "relevance", "data shows"]):
        message_type = "tool"
    elif any(keyword in content.lower() for keyword in ["urgent", "breaking", "immediately", "scoop", "alert"]):
        message_type = "urgent"
    elif any(keyword in content.lower() for keyword in ["concern", "issue", "problem", "risk", "warning"]):
        message_type = "concern"
    
    # Shorten long responses for better UX
    shortened_content = shorten_response(meeting_content)
    
    return {
        "id": str(uuid.uuid4()),
        "speaker": speaker,
        "content": shortened_content,
        "original_content": meeting_content,
        "timestamp": datetime.now().isoformat(),
        "designation": info["designation"],
        "color": info["color"],
        "emoji": info["emoji"],
        "message_type": message_type,
        "is_shortened": len(shortened_content) < len(meeting_content)
    }

def enhance_meeting_language(content: str) -> str:
    """Transform agent responses to sound more like a meeting discussion"""
    
    # Meeting conversation patterns
    meeting_replacements = [
        # Make it conversational
        ("I will", "I'll"),
        ("I am going to", "I'm going to"),
        ("Let me analyze", "Looking at this"),
        ("Based on my analysis", "From what I can see"),
        ("I recommend", "I think we should"),
        ("I suggest", "How about we"),
        ("I believe", "In my view"),
        ("I think", "I feel"),
        ("According to", "Based on"),
        ("The data shows", "What I'm seeing in the data is"),
        
        # Remove robotic language
        ("As an AI", ""),
        ("I am programmed to", "I"),
        ("My algorithms", "My analysis"),
        ("Processing complete", "I've finished reviewing"),
        ("Task completed", "Done with that"),
        
        # Make it more collaborative
        ("I will now", "Let me"),
        ("Please note", "Just to mention"),
        ("It is important to", "We should"),
        ("We must", "We need to"),
        ("It is recommended", "I'd suggest"),
        
        # Meeting-specific language
        ("Here are the results", "Here's what I found"),
        ("In conclusion", "So to wrap up"),
        ("To summarize", "Bottom line"),
        ("Furthermore", "Also"),
        ("Additionally", "And"),
        ("However", "But"),
        ("Therefore", "So"),
        ("Nevertheless", "Still"),
    ]
    
    enhanced_content = content
    for old, new in meeting_replacements:
        enhanced_content = enhanced_content.replace(old, new)
    
    # Add conversational connectors
    if not any(starter in enhanced_content[:50].lower() for starter in ["hey", "so", "well", "okay", "alright", "now"]):
        conversation_starters = ["So", "Alright", "Okay", "Now", "Well"]
        import random
        enhanced_content = f"{random.choice(conversation_starters)}, {enhanced_content.lower()}" if enhanced_content else enhanced_content
    
    return enhanced_content

def shorten_response(content: str, max_length: int = 400) -> str:
    """Shorten agent responses for better UX while preserving key information"""
    
    if len(content) <= max_length:
        return content
    
    # Try to find a natural break point
    sentences = content.split('. ')
    shortened = ""
    
    for sentence in sentences:
        if len(shortened + sentence + '. ') > max_length:
            break
        shortened += sentence + '. '
    
    # If we couldn't fit even one sentence, truncate at word boundary
    if not shortened:
        words = content.split()
        while len(' '.join(words)) > max_length and words:
            words.pop()
        shortened = ' '.join(words)
    
    # Clean up and add ellipsis
    shortened = shortened.strip()
    if not shortened.endswith('.'):
        shortened += '...'
    
    return shortened

@app.get("/api/status")
async def get_status():
    """Get current session status"""
    return {
        "session_running": manager.session_running,
        "message_count": len(manager.conversation_messages),
        "has_newsroom": manager.newsroom_instance is not None,
        "api_key_configured": bool(config.openai_api_key),
        "session_start_time": manager.session_start_time.isoformat() if manager.session_start_time else None
    }

@app.post("/api/start_session")
async def start_session_api(data: dict):
    """Start session via API"""
    if not config.openai_api_key:
        return {"success": False, "message": "OpenAI API key not configured"}
    
    if not manager.session_running:
        await start_newsroom_session(data.get("articles_count", 5))
        return {"success": True, "message": "Session started"}
    else:
        return {"success": False, "message": "Session already running"}

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "active_connections": len(manager.active_connections),
        "session_running": manager.session_running
    }

if __name__ == "__main__":
    import uvicorn
    
    print("🚀 Starting Enhanced Techronicle AutoGen Server...")
    print("📡 WebSocket endpoint: ws://localhost:8000/ws")
    print("🌐 Dashboard: http://localhost:8000")
    print("💡 API Status: http://localhost:8000/api/status")
    print("👥 Agents API: http://localhost:8000/api/agents")
    
    # Check configuration
    if not config.openai_api_key:
        print("⚠️  WARNING: OpenAI API key not found in environment variables!")
        print("   Please set OPENAI_API_KEY in your .env file")
    else:
        print("✅ OpenAI API key configured")
    
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=8000,
        log_level="info"
    )