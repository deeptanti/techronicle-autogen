"""
Conversation logging and management for Techronicle AutoGen
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from utils.config import config

@dataclass
class ConversationMessage:
    """Represents a single message in the conversation"""
    timestamp: str
    speaker: str
    recipient: str
    content: str
    message_type: str = "chat"
    metadata: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return asdict(self)

class ConversationLogger:
    """Manages conversation logging and persistence"""
    
    def __init__(self, session_id: Optional[str] = None):
        self.session_id = session_id or datetime.now().strftime("%Y%m%d_%H%M%S")
        self.messages: List[ConversationMessage] = []
        self.session_metadata = {
            "session_id": self.session_id,
            "started_at": datetime.now().isoformat(),
            "participants": [],
            "topics": [],
            "decisions": []
        }
        
        # Setup logging
        self.setup_logging()
        
    def setup_logging(self):
        """Setup Python logging"""
        logging.basicConfig(
            level=getattr(logging, config.log_level),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(f"techronicle.{self.session_id}")
    
    def log_message(self, speaker: str, recipient: str, content: str, 
                   message_type: str = "chat", metadata: Optional[Dict] = None) -> ConversationMessage:
        """Log a message from the conversation"""
        message = ConversationMessage(
            timestamp=datetime.now().isoformat(),
            speaker=speaker,
            recipient=recipient,
            content=content,
            message_type=message_type,
            metadata=metadata or {}
        )
        
        self.messages.append(message)
        
        # Update participants
        if speaker not in self.session_metadata["participants"]:
            self.session_metadata["participants"].append(speaker)
        if recipient not in self.session_metadata["participants"] and recipient != "All":
            self.session_metadata["participants"].append(recipient)
        
        # Log to console
        self.logger.info(f"{speaker} → {recipient}: {content[:100]}...")
        
        # Save if configured
        if config.save_conversations:
            self.save_conversation()
        
        return message
    
    def log_decision(self, decision_maker: str, decision: str, 
                    reasoning: str, metadata: Optional[Dict] = None):
        """Log an editorial decision"""
        decision_entry = {
            "timestamp": datetime.now().isoformat(),
            "decision_maker": decision_maker,
            "decision": decision,
            "reasoning": reasoning,
            "metadata": metadata or {}
        }
        
        self.session_metadata["decisions"].append(decision_entry)
        
        # Log as special message
        self.log_message(
            speaker=decision_maker,
            recipient="Editorial",
            content=f"DECISION: {decision} | REASONING: {reasoning}",
            message_type="decision",
            metadata=metadata
        )
    
    def add_topic(self, topic: str):
        """Add a topic to the session"""
        if topic not in self.session_metadata["topics"]:
            self.session_metadata["topics"].append(topic)
    
    def get_conversation_summary(self) -> Dict[str, Any]:
        """Get a summary of the conversation"""
        if not self.messages:
            return {"summary": "No conversation yet", "stats": {}}
        
        # Calculate statistics
        stats = {
            "total_messages": len(self.messages),
            "participants": len(self.session_metadata["participants"]),
            "duration_minutes": self._calculate_duration(),
            "message_types": self._count_message_types(),
            "most_active_speaker": self._find_most_active_speaker()
        }
        
        # Generate summary
        summary = {
            "session_id": self.session_id,
            "metadata": self.session_metadata,
            "stats": stats,
            "key_decisions": self.session_metadata["decisions"],
            "topics_discussed": self.session_metadata["topics"]
        }
        
        return summary
    
    def save_conversation(self):
        """Save conversation to file"""
        if not config.save_conversations:
            return
        
        try:
            # Prepare data for saving
            conversation_data = {
                "session_metadata": self.session_metadata,
                "messages": [msg.to_dict() for msg in self.messages],
                "summary": self.get_conversation_summary()
            }
            
            # Save to JSON file
            filename = f"conversation_{self.session_id}.json"
            filepath = config.conversations_dir / filename
            
            with open(filepath, 'w') as f:
                json.dump(conversation_data, f, indent=2, default=str)
            
            self.logger.debug(f"Conversation saved to {filepath}")
            
        except Exception as e:
            self.logger.error(f"Error saving conversation: {e}")
    
    def load_conversation(self, session_id: str) -> bool:
        """Load a previous conversation"""
        try:
            filename = f"conversation_{session_id}.json"
            filepath = config.conversations_dir / filename
            
            if not filepath.exists():
                self.logger.warning(f"Conversation file not found: {filepath}")
                return False
            
            with open(filepath, 'r') as f:
                data = json.load(f)
            
            self.session_metadata = data["session_metadata"]
            self.messages = [
                ConversationMessage(**msg) for msg in data["messages"]
            ]
            
            self.logger.info(f"Loaded conversation {session_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error loading conversation: {e}")
            return False
    
    def _calculate_duration(self) -> float:
        """Calculate conversation duration in minutes"""
        if len(self.messages) < 2:
            return 0.0
        
        start_time = datetime.fromisoformat(self.messages[0].timestamp)
        end_time = datetime.fromisoformat(self.messages[-1].timestamp)
        duration = (end_time - start_time).total_seconds() / 60
        
        return round(duration, 1)
    
    def _count_message_types(self) -> Dict[str, int]:
        """Count messages by type"""
        counts = {}
        for msg in self.messages:
            counts[msg.message_type] = counts.get(msg.message_type, 0) + 1
        return counts
    
    def _find_most_active_speaker(self) -> str:
        """Find the most active participant"""
        if not self.messages:
            return "None"
        
        speaker_counts = {}
        for msg in self.messages:
            speaker_counts[msg.speaker] = speaker_counts.get(msg.speaker, 0) + 1
        
        return max(speaker_counts, key=speaker_counts.get)
    
    def export_conversation(self, format: str = "json") -> str:
        """Export conversation in different formats"""
        if format == "json":
            return json.dumps(self.get_conversation_summary(), indent=2, default=str)
        
        elif format == "markdown":
            return self._export_to_markdown()
        
        elif format == "plain_text":
            return self._export_to_plain_text()
        
        else:
            raise ValueError(f"Unsupported export format: {format}")
    
    def _export_to_markdown(self) -> str:
        """Export conversation as Markdown"""
        md_content = f"# Techronicle Newsroom Session {self.session_id}\n\n"
        md_content += f"**Started:** {self.session_metadata['started_at']}\n"
        md_content += f"**Participants:** {', '.join(self.session_metadata['participants'])}\n\n"
        
        if self.session_metadata["topics"]:
            md_content += f"**Topics:** {', '.join(self.session_metadata['topics'])}\n\n"
        
        md_content += "## Conversation\n\n"
        
        for msg in self.messages:
            timestamp = msg.timestamp.split('T')[1][:8]  # Extract time
            md_content += f"**{msg.speaker}** → {msg.recipient} *[{timestamp}]*: {msg.content}\n\n"
        
        if self.session_metadata["decisions"]:
            md_content += "## Editorial Decisions\n\n"
            for decision in self.session_metadata["decisions"]:
                md_content += f"- **{decision['decision_maker']}**: {decision['decision']}\n"
                md_content += f"  - *Reasoning*: {decision['reasoning']}\n\n"
        
        return md_content
    
    def _export_to_plain_text(self) -> str:
        """Export conversation as plain text"""
        content = f"Techronicle Newsroom Session {self.session_id}\n"
        content += "=" * 50 + "\n\n"
        
        for msg in self.messages:
            timestamp = msg.timestamp.split('T')[1][:8]
            content += f"[{timestamp}] {msg.speaker} → {msg.recipient}: {msg.content}\n"
        
        return content

# Global logger instance
current_session_logger: Optional[ConversationLogger] = None

def get_logger(session_id: Optional[str] = None) -> ConversationLogger:
    """Get or create conversation logger"""
    global current_session_logger
    
    if current_session_logger is None or (session_id and current_session_logger.session_id != session_id):
        current_session_logger = ConversationLogger(session_id)
    
    return current_session_logger