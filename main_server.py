"""
Updated FastAPI Server for React Frontend
Serves React build files and provides API endpoints
"""

import warnings
# Suppress warnings first
warnings.filterwarnings("ignore", message="flaml.automl is not available")
warnings.filterwarnings("ignore", message=".*API key specified is not a valid OpenAI format.*")

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
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

# Add CORS middleware for React development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],  # React dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Setup static files for React build
react_build_dir = Path("frontend/build")
if react_build_dir.exists():
    app.mount("/static", StaticFiles(directory=react_build_dir / "static"), name="static")

# WebSocket connections manager (same as before)
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
    print("🚀 FastAPI server started")
    print("📡 WebSocket endpoint: ws://localhost:8000/ws")
    print("🌐 React Frontend: http://localhost:3000 (development)")
    print("🌐 Production Frontend: http://localhost:8000 (when built)")

# Serve React app (only for root path)
@app.get("/")
async def get_app():
    """Serve React app"""
    if react_build_dir.exists():
        return FileResponse(react_build_dir / "index.html")
    else:
        return {
            "message": "React frontend not built yet",
            "instructions": [
                "1. Navigate to frontend directory: cd frontend",
                "2. Install dependencies: npm install", 
                "3. Build for production: npm run build",
                "4. Or run in development: npm start"
            ]
        }

@app.get("/api/agents")
async def get_agents_info():
    """Get information about all agents including their system prompts"""
    
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
            agent = creator_func()
            
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
        agent = agent_creators[agent_key]()
        
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
    
    executor = concurrent.futures.ThreadPoolExecutor(max_workers=2)
    
    def run_newsroom():
        try:
            session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
            manager.newsroom_instance = TechronicleNewsroom(session_id=session_id)
            
            manager.send_status_sync("initialized", f"Editorial meeting {session_id} ready")
            
            monitor_thread = threading.Thread(target=monitor_conversation, daemon=True)
            monitor_thread.start()
            
            manager.send_status_sync("running", "Editorial discussion in progress...")
            results = manager.newsroom_instance.run_editorial_session(articles_count)
            
            success = results.get("success", False)
            status = "completed" if success else "failed"
            details = f"Published {results.get('articles_published', 0)} articles" if success else results.get('error', 'Unknown error')
            
            manager.send_status_sync(status, details)
            manager.session_running = False
            
        except Exception as e:
            manager.send_status_sync("error", f"Session failed: {str(e)}")
            manager.session_running = False
    
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
                    new_messages = current_messages[last_message_count:]
                    
                    for msg in new_messages:
                        formatted_message = format_message_for_ui(msg)
                        manager.conversation_messages.append(formatted_message)
                        
                        manager.broadcast_message_sync({
                            "type": "new_message",
                            "message": formatted_message
                        })
                    
                    last_message_count = current_count
            
            time.sleep(1)
            
        except Exception as e:
            print(f"Monitor error: {e}")
            break

def format_message_for_ui(msg: dict) -> dict:
    """Enhanced message formatting for UI display"""
    speaker = msg.get("name", "Unknown")
    content = msg.get("content", "")
    
    agent_info = {
        "Gary": {"designation": "Beat Reporter", "color": "#2196f3", "emoji": "📰"},
        "Aravind": {"designation": "Market Analyst", "color": "#9c27b0", "emoji": "🔍"},
        "Tijana": {"designation": "Copy Editor", "color": "#ff9800", "emoji": "✏️"},
        "Jerin": {"designation": "Managing Editor", "color": "#4caf50", "emoji": "⚖️"},
        "Aayushi": {"designation": "Audience Editor", "color": "#e91e63", "emoji": "📱"},
        "James": {"designation": "Publishing Manager", "color": "#8bc34a", "emoji": "🚀"}
    }
    
    info = agent_info.get(speaker, {
        "designation": "Team Member",
        "color": "#757575",
        "emoji": "🤖"
    })
    
    message_type = "discussion"
    
    if any(keyword in content.lower() for keyword in ["decision", "approve", "publish", "override", "executive", "final call"]):
        message_type = "decision"
    elif any(keyword in content.lower() for keyword in ["tool", "processing", "collected", "analyzed", "scraping", "relevance"]):
        message_type = "tool"
    elif any(keyword in content.lower() for keyword in ["urgent", "breaking", "immediately", "scoop", "alert"]):
        message_type = "urgent"
    
    return {
        "id": str(uuid.uuid4()),
        "speaker": speaker,
        "content": content,
        "timestamp": datetime.now().isoformat(),
        "designation": info["designation"],
        "color": info["color"],
        "emoji": info["emoji"],
        "message_type": message_type
    }

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
        "session_running": manager.session_running,
        "frontend_available": react_build_dir.exists()
    }

# Catch-all route for React Router (SPA) - MUST BE LAST
@app.get("/{path:path}")
async def catch_all(path: str):
    """Catch-all route for React Router - handles all non-API routes"""
    if react_build_dir.exists():
        # For any non-API route, serve React app
        return FileResponse(react_build_dir / "index.html")
    else:
        return {"message": "React frontend not built", "path": path}

if __name__ == "__main__":
    import uvicorn
    
    print("🚀 Starting Techronicle AutoGen Server with React Support...")
    print("📡 WebSocket endpoint: ws://localhost:8000/ws")
    print("🌐 API endpoints: http://localhost:8000/api/")
    print("💡 Health check: http://localhost:8000/health")
    
    if react_build_dir.exists():
        print("✅ React build found - serving production frontend at http://localhost:8000")
    else:
        print("⚠️  React build not found - run 'npm run build' in frontend directory")
        print("🔧 For development, run React dev server: npm start (will run on http://localhost:3000)")
    
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