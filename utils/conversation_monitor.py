"""
Real-time conversation monitoring for Streamlit interface
"""

import threading
import time
import queue
from typing import Dict, List, Any, Callable, Optional
from datetime import datetime
import streamlit as st

class ConversationMonitor:
    """Monitors AutoGen conversations and provides real-time updates"""
    
    def __init__(self):
        self.message_queue = queue.Queue()
        self.is_monitoring = False
        self.monitor_thread = None
        self.callbacks = []
        self.current_messages = []
        
    def start_monitoring(self, newsroom_instance):
        """Start monitoring a newsroom conversation"""
        if self.is_monitoring:
            return
        
        self.is_monitoring = True
        self.newsroom = newsroom_instance
        
        # Start monitoring thread
        self.monitor_thread = threading.Thread(
            target=self._monitor_conversation,
            daemon=True
        )
        self.monitor_thread.start()
    
    def stop_monitoring(self):
        """Stop monitoring"""
        self.is_monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=1)
    
    def _monitor_conversation(self):
        """Monitor conversation in background thread"""
        last_message_count = 0
        
        while self.is_monitoring:
            try:
                if hasattr(self.newsroom, 'group_chat') and self.newsroom.group_chat.messages:
                    current_count = len(self.newsroom.group_chat.messages)
                    
                    if current_count > last_message_count:
                        # New messages detected
                        new_messages = self.newsroom.group_chat.messages[last_message_count:]
                        
                        for msg in new_messages:
                            self.message_queue.put({
                                "type": "new_message",
                                "data": msg,
                                "timestamp": datetime.now().isoformat()
                            })
                        
                        last_message_count = current_count
                
                time.sleep(1)  # Check every second
                
            except Exception as e:
                self.message_queue.put({
                    "type": "error",
                    "data": str(e),
                    "timestamp": datetime.now().isoformat()
                })
                break
    
    def get_new_messages(self) -> List[Dict]:
        """Get new messages from the queue"""
        new_messages = []
        
        try:
            while True:
                message = self.message_queue.get_nowait()
                new_messages.append(message)
        except queue.Empty:
            pass
        
        return new_messages
    
    def add_callback(self, callback: Callable):
        """Add callback for new messages"""
        self.callbacks.append(callback)
    
    def trigger_callbacks(self, message: Dict):
        """Trigger all registered callbacks"""
        for callback in self.callbacks:
            try:
                callback(message)
            except Exception as e:
                print(f"Callback error: {e}")

# Global monitor instance for Streamlit
_global_monitor = None

def get_conversation_monitor() -> ConversationMonitor:
    """Get global conversation monitor instance"""
    global _global_monitor
    
    if _global_monitor is None:
        _global_monitor = ConversationMonitor()
    
    return _global_monitor

def setup_streamlit_monitoring():
    """Setup conversation monitoring for Streamlit"""
    if 'conversation_monitor' not in st.session_state:
        st.session_state.conversation_monitor = get_conversation_monitor()
    
    return st.session_state.conversation_monitor