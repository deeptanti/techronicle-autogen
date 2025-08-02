"""
Fixed FastAPI WebSocket Server for Real-time Chat Display
Fixes async/await issues and API key warnings
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
    
    await manager.send_status("initializing", "Starting newsroom agents...")
    
    # Use thread pool executor for CPU-intensive work
    executor = concurrent.futures.ThreadPoolExecutor(max_workers=2)
    
    def run_newsroom():
        try:
            # Initialize newsroom
            session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
            manager.newsroom_instance = TechronicleNewsroom(session_id=session_id)
            
            # Send initialization complete (thread-safe)
            manager.send_status_sync("initialized", f"Session {session_id} ready")
            
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
    """Format message for UI display"""
    speaker = msg.get("name", "Unknown")
    content = msg.get("content", "")
    
    # Agent info mapping
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
    
    # Detect message type
    message_type = "normal"
    if any(keyword in content.lower() for keyword in ["decision", "approve", "publish", "override", "executive"]):
        message_type = "decision"
    elif any(keyword in content.lower() for keyword in ["tool", "processing", "collected", "analyzed", "scraping", "relevance"]):
        message_type = "tool"
    elif any(keyword in content.lower() for keyword in ["urgent", "breaking", "immediately", "scoop"]):
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
        "api_key_configured": bool(config.openai_api_key)
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
    
    print("🚀 Starting Techronicle AutoGen Server...")
    print("📡 WebSocket endpoint: ws://localhost:8000/ws")
    print("🌐 Dashboard: http://localhost:8000")
    print("💡 API Status: http://localhost:8000/api/status")
    
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