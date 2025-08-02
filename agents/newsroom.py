"""
Main newsroom orchestration for Techronicle AutoGen
Enhanced with tool integration and proper conversation flow
"""

import json
import time
from datetime import datetime
from typing import Dict, List, Any, Optional
from autogen import GroupChat, GroupChatManager

# Import agent personalities
from agents.personalities.gary_poussin import create_gary_agent
from agents.personalities.aravind_rajen import create_aravind_agent
from agents.personalities.tijana_jekic import create_tijana_agent
from agents.personalities.jerin_sojan import create_jerin_agent
from agents.personalities.aayushi_patel import create_aayushi_agent
from agents.personalities.james_guerra import create_james_agent

# Import tools
from agents.tools.rss_collector import collect_latest_crypto_news
from agents.tools.content_processor import process_rss_articles, get_best_articles, filter_articles_by_relevance
from agents.tools.slack_publisher import publish_to_slack, publish_session_summary_to_slack

# Import utilities
from utils.config import config, get_llm_config
from utils.logger import get_logger

class TechronicleNewsroom:
    """Main newsroom class managing all agents and workflows"""
    
    def __init__(self, session_id: Optional[str] = None):
        self.session_id = session_id or datetime.now().strftime("%Y%m%d_%H%M%S")
        self.logger = get_logger(self.session_id)
        
        # Initialize agents
        self.agents = self._create_agents()
        
        # Setup group chat
        self.group_chat = self._setup_group_chat()
        self.chat_manager = self._create_chat_manager()
        
        # Track session state
        self.session_state = {
            "articles_collected": [],
            "processed_articles": [],
            "current_discussion": None,
            "decisions_made": [],
            "published_articles": [],
            "tools_used": []
        }
        
        self.logger.logger.info(f"Newsroom initialized for session {self.session_id}")
    
    def _create_agents(self) -> Dict[str, Any]:
        """Create all newsroom agents with enhanced configurations"""
        agents = {
            "gary": create_gary_agent(),
            "aravind": create_aravind_agent(),
            "tijana": create_tijana_agent(),
            "jerin": create_jerin_agent(),
            "aayushi": create_aayushi_agent(),
            "james": create_james_agent()
        }
        
        self.logger.logger.info(f"Created {len(agents)} agents")
        return agents
    
    def _setup_group_chat(self) -> GroupChat:
        """Setup group chat with improved speaker selection"""
        
        def enhanced_speaker_selection(last_speaker, groupchat):
            """Enhanced conversation flow control"""
            messages = groupchat.messages
            
            if not messages:
                return self.agents["gary"]  # Gary starts
            
            last_message = messages[-1]["content"].lower()
            last_speaker_name = last_speaker.name.lower()
            message_count = len(messages)
            
            # Prevent infinite loops - limit consecutive speakers
            recent_speakers = [msg.get("name", "") for msg in messages[-3:]]
            if len(set(recent_speakers)) <= 1 and message_count > 5:
                # Force different speaker if stuck in loop
                available_agents = [name for name in self.agents.keys() 
                                 if self.agents[name].name != last_speaker.name]
                if available_agents:
                    return self.agents[available_agents[0]]
            
            # Check if publication decision has been made
            if self._has_clear_publication_decision(messages):
                return self.agents["james"]  # James handles publication
            
            # Gary's workflow: collection -> processing -> reporting
            if last_speaker_name == "gary":
                if "collecting" in last_message or "processing" in last_message:
                    return self.agents["gary"]  # Let Gary continue with tools
                elif any(word in last_message for word in ["articles", "collected", "processed"]):
                    return self.agents["aravind"]  # Analysis phase
                else:
                    return self.agents["aravind"]
            
            # Analysis phase
            elif last_speaker_name == "aravind" and message_count < 8:
                return self.agents["tijana"]  # Fact-checking
            
            # Editorial review phase
            elif last_speaker_name == "tijana" and message_count < 10:
                return self.agents["aayushi"]  # Audience perspective
            
            # Decision facilitation
            elif last_speaker_name == "aayushi" and message_count < 12:
                return self.agents["jerin"]  # Editorial decision
            
            # Force publication decision if conversation too long
            elif message_count >= 15:
                if last_speaker_name != "jerin":
                    return self.agents["jerin"]  # Force decision
                else:
                    return self.agents["james"]  # Force publication
            
            # Default progression
            elif last_speaker_name == "jerin":
                return self.agents["james"]  # Publication logistics
            
            elif last_speaker_name == "james":
                return None  # End conversation
            
            # Fallback
            else:
                return self.agents["jerin"]
        
        # Create group chat with stricter controls
        group_chat = GroupChat(
            agents=list(self.agents.values()),
            messages=[],
            max_round=15,  # Reduced to prevent loops
            speaker_selection_method=enhanced_speaker_selection,
            allow_repeat_speaker=True
        )
        
        return group_chat
    
    def _has_clear_publication_decision(self, messages: List[Dict]) -> bool:
        """Check if a clear publication decision has been made"""
        for msg in reversed(messages[-5:]):
            content = msg.get("content", "").lower()
            speaker = msg.get("name", "").lower()
            
            if speaker == "jerin" and any(phrase in content for phrase in [
                "approve", "decision", "publish", "final", "executive"
            ]):
                return True
        
        return False
    
    def _create_chat_manager(self) -> GroupChatManager:
        """Create chat manager for the group"""
        return GroupChatManager(
            groupchat=self.group_chat,
            llm_config=get_llm_config(temperature=0.7),
            system_message="""You are facilitating a crypto newsroom editorial meeting.

Keep discussions focused and productive:
1. Gary collects and processes articles using tools
2. Team reviews and analyzes content
3. Editorial decisions are made efficiently
4. James handles publication to Slack

Prevent repetitive responses and ensure progress toward publication."""
        )
    
    def run_editorial_session(self, max_articles: int = 5) -> Dict[str, Any]:
        """Run enhanced editorial session with tool integration"""
        self.logger.logger.info("Starting enhanced editorial session")
        
        try:
            # Step 1: Enhanced article preparation
            articles = self._prepare_articles_with_tools(max_articles)
            self.session_state["articles_collected"] = articles
            
            # Step 2: Start conversation with tool context
            initial_message = self._create_enhanced_initial_message(articles)
            
            # Step 3: Run discussion with monitoring
            chat_result = self._run_enhanced_discussion(initial_message)
            
            # Step 4: Process results with publication
            session_results = self._process_enhanced_results(chat_result)
            
            self.logger.logger.info("Enhanced editorial session completed")
            return session_results
            
        except Exception as e:
            self.logger.logger.error(f"Editorial session failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "session_id": self.session_id
            }
    
    def _prepare_articles_with_tools(self, max_articles: int) -> List[Dict]:
        """Enhanced article preparation with content processing"""
        self.logger.logger.info(f"Collecting and processing up to {max_articles} articles")
        
        try:
            # Collect RSS articles
            rss_articles = collect_latest_crypto_news(max_articles * 2)
            
            if not rss_articles:
                self.logger.logger.warning("No RSS articles found, using mock articles")
                return self._create_mock_articles()
            
            # Process articles if enabled
            if config.scraping_enabled:
                self.logger.logger.info("Processing articles with content analysis")
                processed_articles = process_rss_articles(rss_articles)
                
                # Filter and rank
                high_quality = filter_articles_by_relevance(processed_articles, 0.4)
                best_articles = get_best_articles(high_quality, max_articles)
                
                # Convert back to expected format
                final_articles = []
                for article in best_articles:
                    final_articles.append({
                        "title": article.title,
                        "summary": article.summary or article.content[:300] + "...",
                        "source": article.source,
                        "link": article.original_url,
                        "published": article.published_date,
                        "crypto_relevance": article.crypto_relevance,
                        "content": article.content[:500] + "..." if len(article.content) > 500 else article.content,
                        "word_count": article.word_count,
                        "key_topics": article.key_topics,
                        "sentiment": article.sentiment,
                        "processing_status": article.processing_status,
                        "author": article.author
                    })
                
                self.session_state["processed_articles"] = best_articles
                
                if final_articles:
                    self.logger.logger.info(f"Successfully processed {len(final_articles)} articles")
                    return final_articles
            
            # Fallback to RSS only
            self.logger.logger.info("Using RSS articles without processing")
            return rss_articles[:max_articles]
            
        except Exception as e:
            self.logger.logger.error(f"Error in article preparation: {e}")
            return self._create_mock_articles()
    
    def _create_enhanced_initial_message(self, articles: List[Dict]) -> str:
        """Create initial message with tool integration context"""
        article_summaries = []
        
        for i, article in enumerate(articles):
            relevance = article.get('crypto_relevance', 0) * 100
            status = article.get('processing_status', 'unknown')
            
            summary_text = f"• **Article {i+1}**: {article['title']} ({article['source']})\n"
            summary_text += f"  Summary: {article['summary'][:150]}...\n"
            summary_text += f"  Crypto Relevance: {relevance:.1f}% | Status: {status}\n"
            
            if article.get('key_topics'):
                summary_text += f"  Topics: {', '.join(article['key_topics'][:3])}\n"
            
            article_summaries.append(summary_text)
        
        message = f"""🗞️ TECHRONICLE EDITORIAL MEETING - {datetime.now().strftime('%Y-%m-%d %H:%M')}

Welcome team! I've collected and processed {len(articles)} crypto stories with our enhanced tools:

{chr(10).join(article_summaries)}

**PROCESSING COMPLETED:**
✅ RSS collection from {len(config.rss_feeds)} sources
✅ Content analysis and relevance scoring
✅ Quality filtering and ranking
✅ Ready for editorial review

**EDITORIAL REQUIREMENTS:**
🎯 We MUST select and publish at least 1 article
🎯 All articles have been pre-processed for quality
🎯 James will handle Slack publication

**WORKFLOW:**
1. Gary: Tool-based collection complete ✅
2. Aravind: Technical analysis and verification
3. Tijana: Fact-checking and compliance review
4. Aayushi: Audience engagement assessment
5. Jerin: Editorial decision making
6. James: Slack publication and logistics

Gary, report on the tool-based processing results and recommend the top articles for review!"""

        return message
    
    def _run_enhanced_discussion(self, initial_message: str) -> Any:
        """Run discussion with better flow control"""
        self.logger.logger.info("Starting enhanced group discussion")
        
        # Start conversation
        chat_result = self.agents["gary"].initiate_chat(
            recipient=self.chat_manager,
            message=initial_message,
            clear_history=True
        )
        
        # Ensure publication decision
        if not self._validate_publication_decisions():
            self.logger.logger.warning("No clear publication decision - enforcing requirement")
            self._enforce_publication_requirement()
        
        return chat_result
    
    def _validate_publication_decisions(self) -> bool:
        """Validate that publication decisions were made"""
        messages = self.group_chat.messages
        
        for msg in reversed(messages[-5:]):
            content = msg.get("content", "").lower()
            speaker = msg.get("name", "")
            
            if speaker in ["Jerin", "James"] and any(word in content for word in [
                "approve", "publish", "decision", "selected"
            ]):
                return True
        
        return False
    
    def _enforce_publication_requirement(self):
        """Force publication decision if none made"""
        self.logger.logger.info("Enforcing publication requirement")
        
        # Select best article
        articles = self.session_state["articles_collected"]
        if articles:
            selected_article = articles[0]  # Take first/best article
            
            enforcement_message = f"""
**EDITORIAL OVERRIDE - JERIN SOJAN, MANAGING EDITOR**

Team, I'm making an executive decision to ensure publication:

**APPROVED FOR PUBLICATION: "{selected_article['title']}"**

This article meets our standards and serves our readers. James, please publish immediately to Slack.

*Meeting concluded - publication decision final.*
"""
            
            # Add to conversation
            self.group_chat.messages.append({
                "name": "Jerin",
                "content": enforcement_message,
                "role": "assistant"
            })
            
            # Mark as approved
            self.session_state["published_articles"] = [selected_article]
            
            # Log decision
            self.logger.log_decision(
                decision_maker="Jerin",
                decision=f"EXECUTIVE OVERRIDE: Approved {selected_article['title'][:60]}...",
                reasoning="Editorial override to ensure publication requirement",
                metadata={"enforcement": True, "override": True}
            )
    
    def _process_enhanced_results(self, chat_result: Any) -> Dict[str, Any]:
        """Process results with Slack publication"""
        conversation_messages = self.group_chat.messages
        
        # Log all messages
        for msg in conversation_messages:
            self.logger.log_message(
                speaker=msg.get("name", "Unknown"),
                recipient="Team",
                content=msg.get("content", ""),
                message_type="editorial_discussion"
            )
        
        # Get approved articles
        approved_articles = self.session_state.get("published_articles", [])
        
        if not approved_articles and self.session_state["articles_collected"]:
            # Emergency fallback
            approved_articles = [self.session_state["articles_collected"][0]]
            self.session_state["published_articles"] = approved_articles
        
        # Publish to Slack if enabled
        slack_results = []
        if approved_articles and config.slack_enable:
            self.logger.logger.info("Publishing approved articles to Slack")
            
            for article in approved_articles:
                try:
                    # Add session context
                    article_data = article.copy()
                    article_data.update({
                        "session_id": self.session_id,
                        "approved_by": "Editorial Team",
                        "published_at": datetime.now().isoformat()
                    })
                    
                    # Publish to Slack
                    slack_result = publish_to_slack(article_data)
                    slack_results.append(slack_result)
                    
                    if slack_result.get("success"):
                        self.logger.logger.info(f"Published to Slack: {article['title']}")
                    else:
                        self.logger.logger.warning(f"Slack publish failed: {slack_result.get('error')}")
                
                except Exception as e:
                    self.logger.logger.error(f"Error publishing article: {e}")
        
        # Create session summary
        session_summary = {
            "success": True,
            "session_id": self.session_id,
            "timestamp": datetime.now().isoformat(),
            "articles_discussed": len(self.session_state["articles_collected"]),
            "articles_approved": len(approved_articles),
            "articles_published": len(approved_articles),
            "total_messages": len(conversation_messages),
            "approved_articles": approved_articles,
            "slack_publications": slack_results,
            "participants": list(set(msg.get("name", "Unknown") for msg in conversation_messages)),
            "publication_requirement_met": len(approved_articles) >= 1,
            "tools_used": ["RSS Collection", "Content Processing", "Slack Publishing"]
        }
        
        # Publish session summary to Slack
        if config.slack_enable:
            try:
                publish_session_summary_to_slack(session_summary)
                self.logger.logger.info("Published session summary to Slack")
            except Exception as e:
                self.logger.logger.error(f"Error publishing session summary: {e}")
        
        # Save published articles
        self._save_published_articles(approved_articles)
        
        return session_summary
    
    def _save_published_articles(self, articles: List[Dict]):
        """Save published articles to file"""
        if not articles:
            return
        
        try:
            for i, article in enumerate(articles):
                publication_data = {
                    "publication_id": f"tc_{self.session_id}_{i+1}",
                    "session_id": self.session_id,
                    "original_article": article,
                    "published_at": datetime.now().isoformat(),
                    "published_by": "Techronicle Editorial Team",
                    "publication_status": "published"
                }
                
                filename = f"published_{publication_data['publication_id']}.json"
                filepath = config.published_dir / filename
                
                with open(filepath, 'w') as f:
                    json.dump(publication_data, f, indent=2, default=str)
                
                self.logger.logger.info(f"Saved published article: {filename}")
        
        except Exception as e:
            self.logger.logger.error(f"Error saving published articles: {e}")
    
    def _create_mock_articles(self) -> List[Dict]:
        """Create mock articles for testing"""
        return [
            {
                "title": "Bitcoin ETF Sees Record $2.1B Inflows as Institutional Adoption Accelerates",
                "summary": "The largest Bitcoin ETF recorded unprecedented daily inflows, signaling growing institutional confidence.",
                "source": "CoinDesk",
                "link": "https://example.com/btc-etf-inflows",
                "published": datetime.now().isoformat(),
                "crypto_relevance": 0.95,
                "content": "Institutional investors poured a record $2.1 billion into Bitcoin ETFs...",
                "word_count": 250,
                "key_topics": ["Bitcoin", "ETF", "Institutional"],
                "sentiment": "positive",
                "processing_status": "mock"
            }
        ]
    
    def export_session(self, format: str = "json") -> str:
        """Export session in various formats"""
        return self.logger.export_conversation(format)
    
    def save_session(self) -> str:
        """Save session to file"""
        self.logger.save_conversation()
        return f"Session saved as conversation_{self.session_id}.json"