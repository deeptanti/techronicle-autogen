"""
Simple Streamlit App - No Threading Issues
Shows real-time conversation by reading saved files
"""

import streamlit as st
import json
import glob
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

# Import the newsroom system
from agents.newsroom import TechronicleNewsroom
from utils.config import config

# Page configuration
st.set_page_config(
    page_title="Techronicle AutoGen - Live Newsroom",
    page_icon="📰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .agent-message {
        padding: 12px;
        margin: 8px 0;
        border-radius: 12px;
        border-left: 4px solid;
    }
    .gary-message {
        background: linear-gradient(135deg, #e3f2fd 0%, #bbdefb 100%);
        border-left-color: #2196f3;
    }
    .aravind-message {
        background: linear-gradient(135deg, #f3e5f5 0%, #e1bee7 100%);
        border-left-color: #9c27b0;
    }
    .tijana-message {
        background: linear-gradient(135deg, #fff3e0 0%, #ffcc02 100%);
        border-left-color: #ff9800;
    }
    .jerin-message {
        background: linear-gradient(135deg, #e8f5e8 0%, #c8e6c9 100%);
        border-left-color: #4caf50;
    }
    .aayushi-message {
        background: linear-gradient(135deg, #fce4ec 0%, #f8bbd9 100%);
        border-left-color: #e91e63;
    }
    .james-message {
        background: linear-gradient(135deg, #f1f8e9 0%, #dcedc1 100%);
        border-left-color: #8bc34a;
    }
    .decision-highlight {
        background: linear-gradient(135deg, #fff9c4 0%, #fff59d 100%) !important;
        border: 2px solid #ffc107 !important;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

def init_session_state():
    """Initialize session state"""
    if 'current_session_id' not in st.session_state:
        st.session_state.current_session_id = None
    if 'session_running' not in st.session_state:
        st.session_state.session_running = False
    if 'auto_refresh' not in st.session_state:
        st.session_state.auto_refresh = False

def get_latest_conversation_file():
    """Get the most recent conversation file"""
    try:
        conversation_files = glob.glob(str(config.conversations_dir / "conversation_*.json"))
        if not conversation_files:
            return None
        
        # Sort by modification time, most recent first
        conversation_files.sort(key=lambda x: Path(x).stat().st_mtime, reverse=True)
        return conversation_files[0]
    except:
        return None

def load_conversation_data(file_path):
    """Load conversation data from file"""
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
        return data
    except:
        return None

def display_message(msg, index):
    """Display a single message"""
    speaker = msg.get("name", "Unknown")
    content = msg.get("content", "")
    timestamp = msg.get("timestamp", "")
    
    # Extract time from timestamp
    try:
        dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        time_str = dt.strftime("%H:%M:%S")
    except:
        time_str = f"Msg {index + 1}"
    
    # Determine styling
    speaker_styles = {
        "Gary": ("gary-message", "📰"),
        "Aravind": ("aravind-message", "🔍"), 
        "Tijana": ("tijana-message", "✏️"),
        "Jerin": ("jerin-message", "⚖️"),
        "Aayushi": ("aayushi-message", "📱"),
        "James": ("james-message", "🚀")
    }
    
    style_class, emoji = speaker_styles.get(speaker, ("agent-message", "🤖"))
    
    # Check for decision
    is_decision = any(keyword in content.lower() for keyword in [
        "approve", "publish", "decision", "executive", "override"
    ])
    
    if is_decision:
        style_class += " decision-highlight"
        decision_icon = "⚖️ DECISION"
    else:
        decision_icon = ""
    
    # Truncate long messages
    display_content = content
    if len(content) > 600:
        display_content = content[:600] + "..."
        with st.expander(f"📖 Full message from {speaker}"):
            st.write(content)
    
    # Display
    st.markdown(f"""
    <div class="agent-message {style_class}">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
            <strong>{emoji} {speaker}</strong>
            <small style="color: #666;">[{time_str}] {decision_icon}</small>
        </div>
        <div>{display_content}</div>
    </div>
    """, unsafe_allow_html=True)

def run_cli_session_background(articles_count, session_id_input):
    """Run CLI session in background and return session ID"""
    import subprocess
    import sys
    
    # Prepare command
    cmd = [sys.executable, "main.py", "run", "--articles", str(articles_count)]
    if session_id_input:
        cmd.extend(["--session", session_id_input])
    
    try:
        # Run in background
        process = subprocess.Popen(cmd, 
                                 stdout=subprocess.PIPE, 
                                 stderr=subprocess.PIPE,
                                 text=True)
        
        # Don't wait for completion - let it run in background
        return process
    except Exception as e:
        st.error(f"Failed to start CLI session: {e}")
        return None

def main():
    """Main Streamlit application"""
    init_session_state()
    
    st.title("🚀 Techronicle AutoGen - Live Newsroom")
    st.markdown("**Multi-Agent Crypto News Curation**")
    
    # Two main sections
    col1, col2 = st.columns([3, 1])
    
    with col2:
        st.header("🎮 Controls")
        
        # Session controls
        articles_count = st.number_input("Articles to Process", min_value=1, max_value=10, value=5)
        session_id_input = st.text_input("Session ID (optional)")
        
        # Start session button
        if st.button("🚀 Start New Session", type="primary", use_container_width=True):
            if not config.openai_api_key:
                st.error("❌ Please set OPENAI_API_KEY in your .env file")
            else:
                with st.spinner("Starting session..."):
                    process = run_cli_session_background(articles_count, session_id_input)
                    if process:
                        st.success("✅ Session started! Watch the conversation →")
                        st.session_state.session_running = True
                        time.sleep(2)  # Give it time to start
                        st.rerun()
        
        # Auto-refresh toggle
        st.session_state.auto_refresh = st.checkbox("🔄 Auto-refresh", value=st.session_state.auto_refresh)
        
        # Manual refresh
        if st.button("🔄 Refresh Now", use_container_width=True):
            st.rerun()
        
        # Status
        st.markdown("---")
        st.subheader("📊 Status")
        
        # Check latest conversation
        latest_file = get_latest_conversation_file()
        if latest_file:
            file_time = datetime.fromtimestamp(Path(latest_file).stat().st_mtime)
            time_diff = datetime.now() - file_time
            
            if time_diff.total_seconds() < 60:  # Less than 1 minute old
                st.success(f"🟢 Active session\n\nLast update: {time_diff.seconds}s ago")
            else:
                st.info(f"🔵 Session available\n\nLast update: {file_time.strftime('%H:%M:%S')}")
        else:
            st.warning("⚪ No sessions found\n\nStart a session to begin")
    
    with col1:
        st.header("💬 Live Conversation")
        
        # Load and display latest conversation
        latest_file = get_latest_conversation_file()
        
        if latest_file:
            conversation_data = load_conversation_data(latest_file)
            
            if conversation_data and "messages" in conversation_data:
                messages = conversation_data["messages"]
                
                # Show session info
                session_id = conversation_data.get("session_metadata", {}).get("session_id", "Unknown")
                message_count = len(messages)
                
                st.info(f"📂 Session: `{session_id}` | 💬 Messages: {message_count}")
                
                # Display messages
                if messages:
                    for i, msg in enumerate(messages):
                        display_message(msg, i)
                    
                    # Auto-scroll to bottom
                    st.markdown("""
                    <script>
                    setTimeout(function() {
                        window.scrollTo({top: document.body.scrollHeight, behavior: 'smooth'});
                    }, 100);
                    </script>
                    """, unsafe_allow_html=True)
                else:
                    st.info("📝 Conversation starting... Messages will appear here")
            else:
                st.warning("❓ Could not load conversation data")
        else:
            st.info("""
            🤖 **No active conversation**
            
            Start a new session using the controls →
            
            **What to expect:**
            - Gary collects and processes articles using tools
            - Team collaborates on editorial decisions  
            - James publishes approved articles to Slack
            - Real-time updates appear automatically
            """)
    
    # Auto-refresh if enabled
    if st.session_state.auto_refresh:
        # Show live indicator
        st.markdown("""
        <div style="position: fixed; top: 10px; right: 10px; background: #4caf50; color: white; 
                    padding: 5px 10px; border-radius: 15px; font-size: 12px; z-index: 1000;">
            🔴 LIVE
        </div>
        """, unsafe_allow_html=True)
        
        # Refresh every 3 seconds
        time.sleep(3)
        st.rerun()

if __name__ == "__main__":
    main()