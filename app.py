"""
Fixed Streamlit Web Interface
Real-time conversation viewing with proper threading
"""

import streamlit as st
import time
import threading
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import plotly.express as px
import pandas as pd
import queue

# Import the newsroom system
from agents.newsroom import TechronicleNewsroom
from utils.config import config
from utils.logger import get_logger

# Page configuration
st.set_page_config(
    page_title="Techronicle AutoGen - Live Newsroom",
    page_icon="📰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .agent-message {
        padding: 12px;
        margin: 8px 0;
        border-radius: 12px;
        border-left: 4px solid;
        animation: fadeIn 0.5s ease-in;
    }
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(10px); }
        to { opacity: 1; transform: translateY(0); }
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
        box-shadow: 0 4px 8px rgba(255, 193, 7, 0.3);
    }
    .tool-highlight {
        background: linear-gradient(135deg, #e8f5e8 0%, #c8e6c9 100%) !important;
        border: 2px solid #4caf50 !important;
        border-left-color: #4caf50 !important;
    }
    .message-timestamp {
        color: #666;
        font-size: 11px;
        opacity: 0.7;
    }
    .agent-name {
        font-weight: bold;
        font-size: 14px;
    }
    .message-content {
        margin-top: 5px;
        line-height: 1.4;
    }
    .session-status {
        padding: 10px;
        border-radius: 8px;
        margin: 10px 0;
        text-align: center;
        font-weight: bold;
    }
    .status-active {
        background-color: #c8e6c9;
        color: #2e7d32;
        border: 2px solid #4caf50;
    }
    .status-ready {
        background-color: #e3f2fd;
        color: #1565c0;
        border: 2px solid #2196f3;
    }
    .status-error {
        background-color: #ffebee;
        color: #c62828;
        border: 2px solid #f44336;
    }
</style>
""", unsafe_allow_html=True)

class StreamlitNewsroom:
    """Enhanced wrapper class for managing newsroom state"""
    
    def __init__(self):
        self.initialize_session_state()
        self.message_queue = queue.Queue()
        self.monitoring_active = False
    
    def initialize_session_state(self):
        """Initialize Streamlit session state"""
        defaults = {
            'newsroom': None,
            'conversation_messages': [],
            'session_running': False,
            'session_results': None,
            'auto_refresh': True,
            'articles_collected': [],
            'approved_articles': [],
            'message_count': 0,
            'last_update': time.time(),
            'session_status': 'ready',
            'session_error': None,
            'monitoring_thread': None,
            'session_thread': None
        }
        
        for key, value in defaults.items():
            if key not in st.session_state:
                st.session_state[key] = value

def display_header():
    """Display the application header with enhanced status"""
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.title("🚀 Techronicle AutoGen")
        st.markdown("**Multi-Agent Crypto News Curation - Live Newsroom**")
        
        # Enhanced status indicator
        status = st.session_state.get('session_status', 'ready')
        message_count = len(st.session_state.get('conversation_messages', []))
        last_update = datetime.fromtimestamp(st.session_state.get('last_update', time.time()))
        
        if status == "running":
            st.markdown(f"""
            <div class="session-status status-active">
                🟢 Editorial Session in Progress<br>
                <small>Messages: {message_count} | Last Update: {last_update.strftime('%H:%M:%S')}</small>
            </div>
            """, unsafe_allow_html=True)
        elif status == "error":
            error_msg = st.session_state.get('session_error', 'Unknown error')
            st.markdown(f"""
            <div class="session-status status-error">
                ❌ Session Error<br>
                <small>{error_msg}</small>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="session-status status-ready">
                🔵 Ready for New Session
            </div>
            """, unsafe_allow_html=True)

def display_agent_cards():
    """Display agent status cards"""
    st.subheader("🤖 Newsroom Team")
    
    col1, col2, col3 = st.columns(3)
    
    agents_info = [
        ("Gary Poussin", "Beat Reporter", "📰", "#2196f3", "Tool-enhanced content collection"),
        ("Aravind Rajen", "Market Analyst", "🔍", "#9c27b0", "PhD economist, data-driven analysis"),
        ("Tijana Jekic", "Copy Editor", "✏️", "#ff9800", "Ex-Reuters, fact-checking expert"),
        ("Jerin Sojan", "Managing Editor", "⚖️", "#4caf50", "WSJ veteran, publication enforcer"),
        ("Aayushi Patel", "Audience Editor", "📱", "#e91e63", "Digital native, engagement focused"),
        ("James Guerra", "Publishing Manager", "🚀", "#8bc34a", "Slack publishing specialist")
    ]
    
    for i, (name, role, icon, color, description) in enumerate(agents_info):
        col = [col1, col2, col3][i % 3]
        
        with col:
            # Calculate agent activity
            agent_messages = sum(1 for msg in st.session_state.conversation_messages 
                               if msg.get("name", "").startswith(name.split()[0]))
            
            # Determine status
            if st.session_state.session_running:
                if agent_messages > 0:
                    status = f"🔄 Active ({agent_messages} msgs)"
                    status_color = "orange"
                else:
                    status = "⏳ Waiting"
                    status_color = "gray"
            else:
                status = "✅ Ready"
                status_color = "green"
            
            st.markdown(f"""
            <div style="
                border: 2px solid {color};
                border-radius: 12px;
                padding: 15px;
                margin: 10px 0;
                background: linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%);
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            ">
                <h4>{icon} {name}</h4>
                <p><strong>{role}</strong></p>
                <p style="font-size: 12px; color: #666;">{description}</p>
                <p style="color: {status_color};"><strong>{status}</strong></p>
            </div>
            """, unsafe_allow_html=True)

def display_conversation():
    """Display live conversation with enhanced message types"""
    st.subheader("💬 Live Editorial Conversation")
    
    # Conversation controls
    col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
    with col2:
        auto_scroll = st.checkbox("📜 Auto-scroll", value=True)
    with col3:
        if st.button("🔄 Refresh Now"):
            st.rerun()
    with col4:
        st.write(f"📊 {len(st.session_state.conversation_messages)} messages")
    
    # Display messages
    if st.session_state.conversation_messages:
        for i, msg in enumerate(st.session_state.conversation_messages):
            display_enhanced_message(msg, i)
        
        if auto_scroll and st.session_state.session_running:
            st.markdown("""
            <script>
            setTimeout(function() {
                window.scrollTo({top: document.body.scrollHeight, behavior: 'smooth'});
            }, 100);
            </script>
            """, unsafe_allow_html=True)
    else:
        st.info("🤖 Agents are ready. Start a session to see the live conversation!")
        
        st.markdown("""
        **💭 Enhanced Workflow:**
        - **Gary** uses tools to collect and process articles with relevance scoring
        - **Aravind** analyzes market impact and technical accuracy  
        - **Tijana** fact-checks and identifies compliance issues
        - **Jerin** facilitates decisions and enforces publication requirements
        - **Aayushi** assesses audience engagement potential
        - **James** publishes approved articles to Slack with rich formatting
        """)

def display_enhanced_message(msg: Dict, index: int):
    """Display enhanced message with tool and decision highlighting"""
    speaker = msg.get("name", "Unknown")
    content = msg.get("content", "")
    
    # Create timestamp
    base_time = datetime.now() - timedelta(minutes=len(st.session_state.conversation_messages) - index)
    timestamp = base_time.strftime("%H:%M:%S")
    
    # Determine message styling
    speaker_styles = {
        "Gary": ("gary-message", "📰"),
        "Aravind": ("aravind-message", "🔍"), 
        "Tijana": ("tijana-message", "✏️"),
        "Jerin": ("jerin-message", "⚖️"),
        "Aayushi": ("aayushi-message", "📱"),
        "James": ("james-message", "🚀")
    }
    
    style_class, emoji = speaker_styles.get(speaker, ("agent-message", "🤖"))
    
    # Enhanced message type detection
    decision_icon = ""
    
    # Check for different message types
    if any(keyword in content.lower() for keyword in [
        "approve", "publish", "final decision", "executive decision", "override"
    ]):
        style_class += " decision-highlight"
        decision_icon = "⚖️ DECISION"
    
    elif any(keyword in content.lower() for keyword in [
        "tool", "processing", "scraping", "collected", "analyzed", "relevance", "webhook", "slack"
    ]):
        style_class += " tool-highlight"
        decision_icon = "🔧 TOOLS"
    
    elif any(keyword in content.lower() for keyword in [
        "breaking", "urgent", "immediately", "scoop", "exclusive"
    ]):
        decision_icon = "🚨 URGENT"
    
    # Truncate very long messages
    display_content = content
    if len(content) > 500:
        display_content = content[:500] + "..."
        with st.expander(f"📖 Full message from {speaker}"):
            st.write(content)
    
    # Display the message
    st.markdown(f"""
    <div class="agent-message {style_class}">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <span class="agent-name">{emoji} {speaker}</span>
            <span class="message-timestamp">[{timestamp}] {decision_icon}</span>
        </div>
        <div class="message-content">{display_content}</div>
    </div>
    """, unsafe_allow_html=True)

def display_session_controls():
    """Display enhanced session control buttons"""
    st.subheader("🎮 Session Controls")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        articles_count = st.number_input("Articles to Process", min_value=1, max_value=10, value=5)
    
    with col2:
        session_id = st.text_input("Custom Session ID (optional)", placeholder="auto-generated")
    
    with col3:
        st.markdown("<br>", unsafe_allow_html=True)
        start_session = st.button(
            "🚀 Start Enhanced Session",
            disabled=st.session_state.session_running,
            use_container_width=True,
            type="primary"
        )
    
    with col4:
        st.markdown("<br>", unsafe_allow_html=True)
        stop_session = st.button(
            "🛑 Stop Session",
            disabled=not st.session_state.session_running,
            use_container_width=True
        )
    
    # Handle button clicks
    if start_session and not st.session_state.session_running:
        start_enhanced_newsroom_session(articles_count, session_id)
    
    if stop_session and st.session_state.session_running:
        stop_newsroom_session()

def start_enhanced_newsroom_session(articles_count: int, session_id: str):
    """Start enhanced newsroom session with proper error handling"""
    if not config.openai_api_key:
        st.error("❌ OpenAI API key not found. Please set OPENAI_API_KEY environment variable.")
        return
    
    try:
        # Initialize session state
        st.session_state.conversation_messages = []
        st.session_state.session_running = True
        st.session_state.session_results = None
        st.session_state.articles_collected = []
        st.session_state.approved_articles = []
        st.session_state.message_count = 0
        st.session_state.last_update = time.time()
        st.session_state.session_status = "initializing"
        st.session_state.session_error = None
        
        # Initialize newsroom
        with st.spinner("🚀 Initializing enhanced newsroom with tools..."):
            newsroom = TechronicleNewsroom(session_id=session_id if session_id else None)
            st.session_state.newsroom = newsroom
        
        st.success(f"✅ Enhanced newsroom initialized! Session ID: {newsroom.session_id}")
        
        # Start session in background with proper isolation
        def run_session_isolated():
            try:
                # Update status
                st.session_state.session_status = "running"
                
                # Run the session
                results = newsroom.run_editorial_session(articles_count)
                
                # Update session state safely
                st.session_state.session_results = results
                st.session_state.session_running = False
                st.session_state.last_update = time.time()
                st.session_state.session_status = "completed" if results.get("success") else "failed"
                
                # Update conversation messages
                if hasattr(newsroom, 'group_chat') and newsroom.group_chat.messages:
                    st.session_state.conversation_messages = newsroom.group_chat.messages
                
                # Update articles
                st.session_state.articles_collected = newsroom.session_state.get("articles_collected", [])
                st.session_state.approved_articles = newsroom.session_state.get("published_articles", [])
                
            except Exception as e:
                st.session_state.session_results = {"success": False, "error": str(e)}
                st.session_state.session_running = False
                st.session_state.session_status = "error"
                st.session_state.session_error = str(e)
        
        # Start background thread
        session_thread = threading.Thread(target=run_session_isolated, daemon=True)
        session_thread.start()
        st.session_state.session_thread = session_thread
        
        # Start monitoring
        start_conversation_monitoring(newsroom)
        
        st.info("🔄 Enhanced editorial session started! Watch the conversation below...")
        
        # Immediate refresh
        time.sleep(1)
        st.rerun()
            
    except Exception as e:
        st.error(f"❌ Error starting session: {e}")
        st.session_state.session_running = False
        st.session_state.session_status = "error"
        st.session_state.session_error = str(e)

def start_conversation_monitoring(newsroom):
    """Start conversation monitoring with proper error handling"""
    
    def monitor_conversation():
        last_message_count = 0
        st.session_state.monitoring_active = True
        
        while (st.session_state.get('session_running', False) and 
               st.session_state.get('monitoring_active', False)):
            try:
                if hasattr(newsroom, 'group_chat') and newsroom.group_chat.messages:
                    current_count = len(newsroom.group_chat.messages)
                    
                    if current_count > last_message_count:
                        # Update safely
                        st.session_state.conversation_messages = newsroom.group_chat.messages.copy()
                        st.session_state.message_count = current_count
                        st.session_state.last_update = time.time()
                        last_message_count = current_count
                
                time.sleep(2)  # Monitor every 2 seconds
                
            except Exception as e:
                st.session_state.session_error = f"Monitoring error: {e}"
                break
        
        st.session_state.monitoring_active = False
    
    # Start monitoring thread
    monitor_thread = threading.Thread(target=monitor_conversation, daemon=True)
    monitor_thread.start()
    st.session_state.monitoring_thread = monitor_thread

def stop_newsroom_session():
    """Stop the newsroom session cleanly"""
    st.session_state.session_running = False
    st.session_state.monitoring_active = False
    st.session_state.session_status = "stopped"
    st.warning("⚠️ Session stopped by user")
    st.rerun()

def display_enhanced_sidebar():
    """Display enhanced sidebar with tool status"""
    with st.sidebar:
        st.header("⚙️ Enhanced Configuration")
        
        # API Key status
        api_key_status = "✅ Set" if config.openai_api_key else "❌ Missing"
        st.write(f"**OpenAI API Key:** {api_key_status}")
        
        # Tool status
        st.write("**🔧 Tool Status:**")
        st.write(f"• Web Scraping: {'✅ Enabled' if config.scraping_enabled else '❌ Disabled'}")
        st.write(f"• Slack Publishing: {'✅ Enabled' if config.slack_enable else '❌ Disabled'}")
        st.write(f"• Content Processing: ✅ Active")
        
        if not config.openai_api_key:
            st.error("Please set OPENAI_API_KEY environment variable")
        
        st.markdown("---")
        
        # Live Updates
        st.header("🔄 Live Updates")
        st.session_state.auto_refresh = st.checkbox(
            "Auto-refresh conversation", 
            value=st.session_state.auto_refresh
        )
        
        # Session Management
        st.header("📋 Session Management")
        
        if st.button("🗑️ Clear All Data", use_container_width=True):
            # Stop any running processes
            st.session_state.session_running = False
            st.session_state.monitoring_active = False
            
            # Clear data
            for key in ['conversation_messages', 'session_results', 'articles_collected', 
                       'approved_articles', 'session_error']:
                st.session_state[key] = []
            
            st.session_state.session_status = 'ready'
            st.rerun()

def main():
    """Enhanced main Streamlit application"""
    # Initialize
    streamlit_newsroom = StreamlitNewsroom()
    
    # Display header
    display_header()
    
    # Main layout
    display_agent_cards()
    st.markdown("---")
    
    # Session controls
    display_session_controls()
    st.markdown("---")
    
    # Two column layout
    col1, col2 = st.columns([2, 1])
    
    with col1:
        display_conversation()
    
    with col2:
        # Session results
        if st.session_state.session_results:
            st.subheader("📊 Session Results")
            results = st.session_state.session_results
            
            if results.get("success"):
                st.success(f"✅ Session completed successfully!")
                
                # Metrics
                col_a, col_b = st.columns(2)
                with col_a:
                    st.metric("Articles Processed", results.get("articles_discussed", 0))
                    st.metric("Articles Published", results.get("articles_published", 0))
                with col_b:
                    st.metric("Total Messages", results.get("total_messages", 0))
                    st.metric("Tools Used", len(results.get("tools_used", [])))
                
                # Published articles
                if results.get("approved_articles"):
                    st.write("**📰 Published Articles:**")
                    for article in results["approved_articles"]:
                        st.success(f"• {article['title'][:50]}...")
            else:
                st.error(f"❌ Session failed: {results.get('error', 'Unknown error')}")
    
    # Sidebar
    display_enhanced_sidebar()
    
    # Auto-refresh for active sessions
    if (st.session_state.session_running and 
        st.session_state.auto_refresh):
        
        st.markdown("""
        <div style="position: fixed; top: 10px; right: 10px; background: #4caf50; color: white; 
                    padding: 5px 10px; border-radius: 15px; font-size: 12px; z-index: 1000;">
            🔴 LIVE
        </div>
        """, unsafe_allow_html=True)
        
        time.sleep(3)
        st.rerun()

if __name__ == "__main__":
    main()