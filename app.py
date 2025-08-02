"""
Techronicle AutoGen - Streamlit Web Interface
Real-time conversation viewing for multi-agent newsroom
"""

import streamlit as st
import time
import threading
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

# Import the newsroom system
from agents.newsroom import TechronicleNewsroom
from utils.config import config
from utils.logger import get_logger
from utils.conversation_monitor import setup_streamlit_monitoring

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
</style>
""", unsafe_allow_html=True)

class StreamlitNewsroom:
    """Wrapper class for managing newsroom state in Streamlit"""
    
    def __init__(self):
        self.initialize_session_state()
    
    def initialize_session_state(self):
        """Initialize Streamlit session state"""
        if 'newsroom' not in st.session_state:
            st.session_state.newsroom = None
        if 'conversation_messages' not in st.session_state:
            st.session_state.conversation_messages = []
        if 'session_running' not in st.session_state:
            st.session_state.session_running = False
        if 'session_results' not in st.session_state:
            st.session_state.session_results = None
        if 'auto_refresh' not in st.session_state:
            st.session_state.auto_refresh = True
        if 'articles_collected' not in st.session_state:
            st.session_state.articles_collected = []
        if 'approved_articles' not in st.session_state:
            st.session_state.approved_articles = []
        if 'message_count' not in st.session_state:
            st.session_state.message_count = 0
        if 'last_update' not in st.session_state:
            st.session_state.last_update = time.time()
        if 'session_status' not in st.session_state:
            st.session_state.session_status = 'ready'
        if 'session_error' not in st.session_state:
            st.session_state.session_error = None

def display_header():
    """Display the application header"""
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.title("🚀 Techronicle AutoGen")
        st.markdown("**Multi-Agent Crypto News Curation - Live Newsroom**")
        
        # Enhanced status indicator with real-time info
        if st.session_state.session_running:
            st.markdown(f"""
            <div class="session-status status-active">
                🟢 Editorial Session in Progress<br>
                <small>Messages: {len(st.session_state.conversation_messages)} | 
                Last Update: {datetime.fromtimestamp(st.session_state.last_update).strftime('%H:%M:%S')}</small>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="session-status status-ready">
                🔵 Ready for New Session
            </div>
            """, unsafe_allow_html=True)

def display_session_status():
    """Display session status based on session state (thread-safe)"""
    status = st.session_state.get('session_status', 'ready')
    
    if status == "initializing":
        st.info("🔄 Initializing newsroom agents...")
    elif status == "running":
        st.info(f"🔄 Editorial discussion in progress... ({st.session_state.get('message_count', 0)} messages)")
    elif status == "completed":
        results = st.session_state.get('session_results', {})
        if results.get("success"):
            st.success(f"🎉 Session completed! {results.get('articles_published', 0)} article(s) published.")
        else:
            st.error(f"❌ Session failed: {results.get('error', 'Unknown error')}")
    elif status == "error":
        error = st.session_state.get('session_error', 'Unknown error')
        st.error(f"💥 Session error: {error}")
    elif status == "failed":
        results = st.session_state.get('session_results', {})
        st.error(f"❌ Session failed: {results.get('error', 'Unknown error')}")

def display_agent_cards():
    """Display agent status cards with enhanced real-time status"""
    st.subheader("🤖 Newsroom Team")
    
    col1, col2, col3 = st.columns(3)
    
    agents_info = [
        ("Gary Poussin", "Beat Reporter", "📰", "#2196f3", "Hustler, competitive, source-driven"),
        ("Aravind Rajen", "Market Analyst", "🔍", "#9c27b0", "PhD economist, methodical, data-obsessed"),
        ("Tijana Jekic", "Copy Editor", "✏️", "#ff9800", "Ex-Reuters, fact-checking expert"),
        ("Jerin Sojan", "Managing Editor", "⚖️", "#4caf50", "WSJ veteran, diplomatic leader"),
        ("Aayushi Patel", "Audience Editor", "📱", "#e91e63", "BuzzFeed background, growth-focused"),
        ("James Guerra", "Publishing Manager", "🚀", "#8bc34a", "Tech startup experience, optimization-focused")
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
    """Display live conversation between agents with real-time updates"""
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
    
    # Create conversation container with scrolling
    conversation_container = st.container()
    
    with conversation_container:
        if st.session_state.conversation_messages:
            # Display messages with enhanced styling
            for i, msg in enumerate(st.session_state.conversation_messages):
                display_message(msg, i)
            
            if auto_scroll and st.session_state.session_running:
                # Auto-scroll to bottom with smooth animation
                st.markdown("""
                <script>
                setTimeout(function() {
                    window.scrollTo({
                        top: document.body.scrollHeight,
                        behavior: 'smooth'
                    });
                }, 100);
                </script>
                """, unsafe_allow_html=True)
        else:
            st.info("🤖 Agents are ready. Start a session to see the live conversation!")
            
            # Show sample conversation preview
            st.markdown("""
            **💭 What to expect:**
            - Gary will collect and present crypto news articles
            - Aravind will analyze market impact and technical accuracy  
            - Tijana will fact-check and identify compliance issues
            - Jerin will facilitate decisions and ensure publication
            - Aayushi will assess audience engagement potential
            - James will handle final publication logistics
            """)

def display_message(msg: Dict, index: int):
    """Display a single conversation message with enhanced styling"""
    speaker = msg.get("name", "Unknown")
    content = msg.get("content", "")
    
    # Create more realistic timestamp
    base_time = datetime.now() - timedelta(minutes=len(st.session_state.conversation_messages) - index)
    timestamp = base_time.strftime("%H:%M:%S")
    
    # Determine message styling based on speaker
    speaker_styles = {
        "Gary": ("gary-message", "📰"),
        "Aravind": ("aravind-message", "🔍"), 
        "Tijana": ("tijana-message", "✏️"),
        "Jerin": ("jerin-message", "⚖️"),
        "Aayushi": ("aayushi-message", "📱"),
        "James": ("james-message", "🚀")
    }
    
    style_class, emoji = speaker_styles.get(speaker, ("agent-message", "🤖"))
    
    # Check if this is a decision message
    is_decision = any(keyword in content.lower() for keyword in [
        "approve", "publish", "final decision", "executive decision", "override",
        "we will publish", "approved for publication", "green light"
    ])
    
    # Check if this is a breaking news or urgent message
    is_urgent = any(keyword in content.lower() for keyword in [
        "breaking", "urgent", "immediately", "scoop", "exclusive"
    ])
    
    if is_decision:
        style_class += " decision-highlight"
        decision_icon = "⚖️ DECISION"
    elif is_urgent:
        decision_icon = "🚨 URGENT"
    else:
        decision_icon = ""
    
    # Truncate very long messages for better display
    if len(content) > 500:
        display_content = content[:500] + "..."
        show_full = st.expander(f"📖 Show full message from {speaker}")
        with show_full:
            st.write(content)
    else:
        display_content = content
    
    # Display the message with enhanced formatting
    st.markdown(f"""
    <div class="agent-message {style_class}">
        <div style="display: flex; justify-content: between; align-items: center;">
            <span class="agent-name">{emoji} {speaker}</span>
            <span class="message-timestamp">[{timestamp}] {decision_icon}</span>
        </div>
        <div class="message-content">{display_content}</div>
    </div>
    """, unsafe_allow_html=True)

def display_session_controls():
    """Display session control buttons and settings"""
    st.subheader("🎮 Session Controls")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        articles_count = st.number_input("Articles to Discuss", min_value=1, max_value=10, value=5)
    
    with col2:
        session_id = st.text_input("Custom Session ID (optional)", placeholder="auto-generated")
    
    with col3:
        st.markdown("<br>", unsafe_allow_html=True)  # Spacing
        start_session = st.button(
            "🚀 Start Editorial Session",
            disabled=st.session_state.session_running,
            use_container_width=True,
            type="primary"
        )
    
    with col4:
        st.markdown("<br>", unsafe_allow_html=True)  # Spacing
        stop_session = st.button(
            "🛑 Stop Session",
            disabled=not st.session_state.session_running,
            use_container_width=True
        )
    
    # Handle button clicks
    if start_session and not st.session_state.session_running:
        start_newsroom_session(articles_count, session_id)
    
    if stop_session and st.session_state.session_running:
        st.session_state.session_running = False
        st.session_state.session_status = "stopped"
        st.warning("⚠️ Session stopped by user")
        st.rerun()

def start_newsroom_session(articles_count: int, session_id: str):
    """Start a new newsroom session with thread-safe monitoring"""
    if not config.openai_api_key:
        st.error("❌ OpenAI API key not found. Please set OPENAI_API_KEY environment variable.")
        return
    
    try:
        # Initialize newsroom
        with st.spinner("🚀 Initializing newsroom agents..."):
            newsroom = TechronicleNewsroom(session_id=session_id if session_id else None)
            st.session_state.newsroom = newsroom
        
        # Clear previous session data
        st.session_state.conversation_messages = []
        st.session_state.session_running = True
        st.session_state.session_results = None
        st.session_state.articles_collected = []
        st.session_state.approved_articles = []
        st.session_state.message_count = 0
        st.session_state.last_update = time.time()
        st.session_state.session_status = "initializing"
        st.session_state.session_error = None
        
        st.success(f"✅ Newsroom initialized! Session ID: {newsroom.session_id}")
        
        # Start session in background thread with thread-safe monitoring
        def run_session_thread_safe():
            try:
                # Update status in session state (thread-safe)
                st.session_state.session_status = "running"
                
                # Run the session
                results = newsroom.run_editorial_session(articles_count)
                
                # Update session state (thread-safe)
                st.session_state.session_results = results
                st.session_state.session_running = False
                st.session_state.last_update = time.time()
                st.session_state.session_status = "completed" if results.get("success") else "failed"
                
                # Update conversation messages
                if hasattr(newsroom, 'group_chat') and newsroom.group_chat.messages:
                    st.session_state.conversation_messages = newsroom.group_chat.messages
                
                # Update articles
                st.session_state.articles_collected = newsroom.session_state.get("articles_collected", [])
                st.session_state.approved_articles = newsroom.session_state.get("approved_articles", [])
                
            except Exception as e:
                # Store error in session state (thread-safe)
                st.session_state.session_results = {"success": False, "error": str(e)}
                st.session_state.session_running = False
                st.session_state.session_status = "error"
                st.session_state.session_error = str(e)
        
        # Start background thread
        session_thread = threading.Thread(target=run_session_thread_safe, daemon=True)
        session_thread.start()
        
        # Setup thread-safe monitoring
        setup_threadsafe_monitoring(newsroom)
        
        st.info("🔄 Editorial session started! Watch the conversation below...")
        
        # Trigger immediate refresh to start monitoring
        time.sleep(1)
        st.rerun()
            
    except Exception as e:
        st.error(f"❌ Error starting session: {e}")
        st.session_state.session_running = False

def setup_threadsafe_monitoring(newsroom):
    """Setup thread-safe monitoring of the conversation"""
    
    def monitor_conversation_threadsafe():
        last_message_count = 0
        update_frequency = 2  # Update every 2 seconds
        
        while st.session_state.get('session_running', False):
            try:
                # Check for new messages
                if hasattr(newsroom, 'group_chat') and newsroom.group_chat.messages:
                    current_count = len(newsroom.group_chat.messages)
                    
                    if current_count > last_message_count:
                        # Update session state (thread-safe)
                        st.session_state.conversation_messages = newsroom.group_chat.messages
                        st.session_state.message_count = current_count
                        st.session_state.last_update = time.time()
                        
                        last_message_count = current_count
                
                time.sleep(update_frequency)
                
            except Exception as e:
                # Store error in session state instead of printing
                st.session_state.session_error = f"Monitoring error: {e}"
                break
    
    # Start monitoring thread
    monitor_thread = threading.Thread(target=monitor_conversation_threadsafe, daemon=True)
    monitor_thread.start()

def display_articles_section():
    """Display collected and approved articles"""
    if st.session_state.articles_collected:
        st.subheader("📰 Articles Being Discussed")
        
        for i, article in enumerate(st.session_state.articles_collected, 1):
            with st.expander(f"Article {i}: {article['title'][:60]}..."):
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.write(f"**Source:** {article.get('source', 'Unknown')}")
                    st.write(f"**Summary:** {article.get('summary', 'No summary available')}")
                    if article.get('crypto_relevance'):
                        relevance = article['crypto_relevance'] * 100
                        st.write(f"**Crypto Relevance:** {relevance:.1f}%")
                
                with col2:
                    # Show if this article was approved
                    is_approved = any(
                        approved.get('title') == article.get('title') 
                        for approved in st.session_state.approved_articles
                    )
                    if is_approved:
                        st.success("✅ Approved for Publication")
                    else:
                        st.info("⏳ Under Review")

def display_results_dashboard():
    """Display session results and analytics"""
    if st.session_state.session_results:
        results = st.session_state.session_results
        
        if results.get("success"):
            st.subheader("📊 Session Results")
            
            # Key metrics
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Articles Discussed", results.get("articles_discussed", 0))
            with col2:
                st.metric("Articles Approved", results.get("articles_approved", 0))
            with col3:
                st.metric("Total Messages", results.get("total_messages", 0))
            with col4:
                req_met = results.get("publication_requirement_met", False)
                st.metric("Publication Req.", "✅ Met" if req_met else "❌ Failed")
            
            # Published articles
            if results.get("approved_articles"):
                st.subheader("📰 Published Articles")
                for i, article in enumerate(results["approved_articles"], 1):
                    st.success(f"**{i}. {article['title']}**")
                    st.write(f"Source: {article.get('source', 'Unknown')}")
                    st.write(f"Summary: {article.get('summary', '')[:200]}...")
            
            # Conversation analytics
            if len(st.session_state.conversation_messages) > 0:
                st.subheader("📈 Conversation Analytics")
                
                # Message count by agent
                agent_counts = {}
                for msg in st.session_state.conversation_messages:
                    agent = msg.get("name", "Unknown")
                    agent_counts[agent] = agent_counts.get(agent, 0) + 1
                
                # Create bar chart
                if agent_counts:
                    df = pd.DataFrame(list(agent_counts.items()), columns=['Agent', 'Messages'])
                    fig = px.bar(df, x='Agent', y='Messages', title="Messages by Agent")
                    st.plotly_chart(fig, use_container_width=True)
        
        else:
            st.error(f"❌ Session failed: {results.get('error', 'Unknown error')}")

def display_sidebar():
    """Display sidebar with configuration and controls"""
    with st.sidebar:
        st.header("⚙️ Configuration")
        
        # API Key status
        api_key_status = "✅ Set" if config.openai_api_key else "❌ Missing"
        st.write(f"**OpenAI API Key:** {api_key_status}")
        
        if not config.openai_api_key:
            st.error("Please set OPENAI_API_KEY environment variable")
            st.code("export OPENAI_API_KEY='your-key-here'")
        
        # Model settings
        st.write(f"**Model:** {config.openai_model}")
        st.write(f"**Max Rounds:** {config.max_rounds}")
        
        st.markdown("---")
        
        # Auto-refresh settings
        st.header("🔄 Live Updates")
        st.session_state.auto_refresh = st.checkbox(
            "Auto-refresh conversation", 
            value=st.session_state.auto_refresh,
            help="Automatically update conversation during active sessions"
        )
        
        if st.session_state.auto_refresh and st.session_state.session_running:
            refresh_interval = st.slider("Refresh interval (seconds)", 1, 10, 3)
            st.info(f"Refreshing every {refresh_interval} seconds...")
        
        st.markdown("---")
        
        # Session management
        st.header("📋 Session Management")
        
        if st.button("🗑️ Clear Conversation", use_container_width=True):
            st.session_state.conversation_messages = []
            st.session_state.session_results = None
            st.session_state.articles_collected = []
            st.session_state.approved_articles = []
            st.session_state.session_status = 'ready'
            st.session_state.session_error = None
            st.rerun()
        
        # Export options
        if st.session_state.conversation_messages:
            st.subheader("📤 Export Options")
            
            export_format = st.selectbox("Export Format", ["JSON", "Markdown", "Plain Text"])
            
            if st.button("📄 Export Conversation", use_container_width=True):
                if st.session_state.newsroom:
                    export_content = st.session_state.newsroom.export_session(export_format.lower())
                    
                    st.download_button(
                        label=f"⬇️ Download {export_format}",
                        data=export_content,
                        file_name=f"conversation_{st.session_state.newsroom.session_id}.{export_format.lower()}",
                        mime="text/plain"
                    )

def display_live_metrics():
    """Display live session metrics during active session"""
    if st.session_state.session_running and st.session_state.conversation_messages:
        st.subheader("📊 Live Session Metrics")
        
        col1, col2, col3, col4 = st.columns(4)
        
        # Calculate metrics
        total_messages = len(st.session_state.conversation_messages)
        unique_speakers = len(set(msg.get("name", "Unknown") for msg in st.session_state.conversation_messages))
        
        # Session duration (estimated)
        session_duration = time.time() - st.session_state.last_update + (total_messages * 30)  # Rough estimate
        duration_minutes = int(session_duration // 60)
        
        # Recent activity
        recent_messages = st.session_state.conversation_messages[-5:] if st.session_state.conversation_messages else []
        recent_speakers = [msg.get("name", "Unknown") for msg in recent_messages]
        most_recent_speaker = recent_speakers[-1] if recent_speakers else "None"
        
        with col1:
            st.metric("Total Messages", total_messages, delta=f"+{total_messages - st.session_state.get('prev_message_count', 0)}")
        
        with col2:
            st.metric("Active Agents", unique_speakers)
        
        with col3:
            st.metric("Est. Duration", f"{duration_minutes}m")
        
        with col4:
            st.metric("Last Speaker", most_recent_speaker)
        
        # Store previous count for delta calculation
        st.session_state.prev_message_count = total_messages
        
        # Activity chart
        if len(st.session_state.conversation_messages) > 3:
            agent_counts = {}
            for msg in st.session_state.conversation_messages:
                agent = msg.get("name", "Unknown")
                agent_counts[agent] = agent_counts.get(agent, 0) + 1
            
            if agent_counts:
                df = pd.DataFrame(list(agent_counts.items()), columns=['Agent', 'Messages'])
                fig = px.bar(df, x='Agent', y='Messages', title="Real-time Message Activity",
                           color='Agent', height=300)
                fig.update_layout(showlegend=False)
                st.plotly_chart(fig, use_container_width=True)

def main():
    """Main Streamlit application (updated with thread-safe status display)"""
    # Initialize
    streamlit_newsroom = StreamlitNewsroom()
    
    # Display header
    display_header()
    
    # Display session status (thread-safe)
    display_session_status()
    
    # Main layout
    display_agent_cards()
    st.markdown("---")
    
    # Session controls
    display_session_controls()
    st.markdown("---")
    
    # Live metrics during active session
    if st.session_state.get('session_running', False):
        display_live_metrics()
        st.markdown("---")
    
    # Two column layout for conversation and content
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Live conversation - this is the main feature
        display_conversation()
    
    with col2:
        # Articles section
        display_articles_section()
        
        # Results dashboard when session completes
        display_results_dashboard()
    
    # Sidebar
    display_sidebar()
    
    # Auto-refresh logic - critical for real-time updates
    if st.session_state.get('session_running', False):
        # Show live update indicator
        st.markdown("""
        <div style="position: fixed; top: 10px; right: 10px; background: #4caf50; color: white; 
                    padding: 5px 10px; border-radius: 15px; font-size: 12px; z-index: 1000;">
            🔴 LIVE
        </div>
        """, unsafe_allow_html=True)
        
        # Auto-refresh every 3 seconds during active session
        time.sleep(3)
        st.rerun()
    
    # Footer
    st.markdown("---")
    st.markdown(
        """
        <div style='text-align: center; color: #666;'>
            <small>Techronicle AutoGen v1.0 - Multi-Agent Crypto News Curation</small><br>
            <small>Powered by AutoGen Framework & Streamlit | Real-time Conversation Monitoring</small>
        </div>
        """, 
        unsafe_allow_html=True
    )

if __name__ == "__main__":
    main()