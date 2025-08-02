"""
Main newsroom orchestration for Techronicle AutoGen
Manages agent interactions and editorial workflows
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
            "current_discussion": None,
            "decisions_made": [],
            "published_articles": []
        }
        
        self.logger.logger.info(f"Newsroom initialized for session {self.session_id}")
    
    def _create_agents(self) -> Dict[str, Any]:
        """Create all newsroom agents"""
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
        """Setup group chat with custom speaker selection"""
        
        def custom_speaker_selection(last_speaker, groupchat):
            """Control conversation flow for realistic editorial dynamics"""
            messages = groupchat.messages
            
            if not messages:
                return self.agents["gary"]  # Gary starts with news collection
            
            last_message = messages[-1]["content"].lower()
            last_speaker_name = last_speaker.name.lower()
            
            # Check if we've reached publication decision
            if self._has_publication_decision(messages):
                return self.agents["james"]  # James handles publication
            
            # Gary presents articles -> Aravind analyzes
            if last_speaker_name == "gary" and ("articles" in last_message or "collected" in last_message):
                return self.agents["aravind"]
            
            # After Aravind analysis -> collaborative discussion
            elif last_speaker_name == "aravind" and ("analysis" in last_message or "scores" in last_message):
                return self.agents["tijana"]  # Fact-checker reviews first
            
            # Collaborative discussion phase - ensure thorough review
            elif last_speaker_name == "tijana":
                if "approve" in last_message or "publish" in last_message:
                    return self.agents["jerin"]  # Editorial decision
                elif "concerns" in last_message or "verify" in last_message:
                    return self.agents["gary"]  # Gary responds to fact-checking
                else:
                    return self.agents["aayushi"]  # Audience perspective
            
            elif last_speaker_name == "aayushi":
                if "recommend" in last_message or "select" in last_message:
                    return self.agents["jerin"]  # Editorial decision
                elif "engagement" in last_message:
                    return self.agents["aravind"]  # Technical analysis of audience needs
                else:
                    return self.agents["tijana"]  # Back to fact-checking
            
            # Jerin makes decisions - enforce publication requirement
            elif last_speaker_name == "jerin":
                if self._count_approved_articles(messages) >= 1:
                    if "decision" in last_message or "publish" in last_message:
                        return self.agents["james"]  # Publishing logistics
                    else:
                        return None  # End if decision made
                else:
                    # Force continued discussion until at least 1 article is approved
                    if "reject" in last_message or "not approve" in last_message:
                        return self.agents["aravind"]  # Back to analysis
                    else:
                        return self.agents["aayushi"]  # Continue discussion
            
            # James handles final publication
            elif last_speaker_name == "james":
                if "published" in last_message or "live" in last_message:
                    return None  # End conversation
                else:
                    return self.agents["jerin"]  # Back to editorial decisions
            
            # Default fallback - keep discussion going
            else:
                return self.agents["jerin"]  # Jerin facilitates when unclear
        
        # Create group chat
        group_chat = GroupChat(
            agents=list(self.agents.values()),
            messages=[],
            max_round=config.max_rounds,
            speaker_selection_method=custom_speaker_selection,
            allow_repeat_speaker=True  # Allow natural back-and-forth
        )
        
        return group_chat
    
    def _has_publication_decision(self, messages: List[Dict]) -> bool:
        """Check if a publication decision has been made"""
        for msg in reversed(messages[-5:]):  # Check last 5 messages
            content = msg.get("content", "").lower()
            speaker = msg.get("name", "").lower()
            
            # Look for explicit publication decisions
            if speaker == "jerin" and any(phrase in content for phrase in [
                "we will publish", "approved for publication", "final decision to publish",
                "let's publish", "green light to publish"
            ]):
                return True
        
        return False
    
    def _count_approved_articles(self, messages: List[Dict]) -> int:
        """Count how many articles have been explicitly approved"""
        approved_count = 0
        
        for msg in messages:
            content = msg.get("content", "").lower()
            speaker = msg.get("name", "").lower()
            
            # Count approval statements
            if any(phrase in content for phrase in [
                "approve this article", "approved for publication", "select this story",
                "publish this one", "go with this article"
            ]):
                approved_count += 1
        
        return approved_count
    
    def _create_chat_manager(self) -> GroupChatManager:
        """Create chat manager for the group"""
        return GroupChatManager(
            groupchat=self.group_chat,
            llm_config=get_llm_config(temperature=0.7),
            system_message="""You are the facilitator of a crypto newsroom editorial meeting.
            
            Your role is to:
            1. Keep the conversation focused on selecting and publishing crypto news
            2. Ensure all perspectives are heard
            3. Guide the team toward editorial decisions
            4. Maintain professional but dynamic discussion
            
            The team should collaborate to:
            - Review collected crypto news articles
            - Analyze quality, credibility, and audience appeal
            - Make editorial decisions about what to publish
            - Coordinate publication logistics
            
            Encourage natural debate and discussion between team members."""
        )
    
    def run_editorial_session(self, max_articles: int = 5) -> Dict[str, Any]:
        """Run a complete editorial session"""
        self.logger.logger.info("Starting editorial session")
        
        try:
            # Collect articles for discussion
            articles = self._prepare_articles(max_articles)
            self.session_state["articles_collected"] = articles
            
            # Start the conversation
            initial_message = self._create_initial_message(articles)
            
            # Run the group chat
            chat_result = self._run_group_discussion(initial_message)
            
            # Process results
            session_results = self._process_session_results(chat_result)
            
            self.logger.logger.info("Editorial session completed")
            return session_results
            
        except Exception as e:
            self.logger.logger.error(f"Editorial session failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "session_id": self.session_id
            }
    
    def _prepare_articles(self, max_articles: int) -> List[Dict]:
        """Collect and prepare articles for editorial discussion"""
        self.logger.logger.info(f"Collecting up to {max_articles} articles")
        
        try:
            articles = collect_latest_crypto_news(max_articles)
            
            if not articles:
                # Fallback to mock articles for demo
                articles = self._create_mock_articles()
            
            self.logger.logger.info(f"Prepared {len(articles)} articles for discussion")
            return articles
            
        except Exception as e:
            self.logger.logger.warning(f"Error collecting articles: {e}, using mock articles")
            return self._create_mock_articles()
    
    def _create_mock_articles(self) -> List[Dict]:
        """Create mock articles for testing/demo purposes"""
        return [
            {
                "title": "Bitcoin ETF Sees Record $2.1B Inflows as Institutional Adoption Accelerates",
                "summary": "The largest Bitcoin ETF recorded unprecedented daily inflows, signaling growing institutional confidence in cryptocurrency investments.",
                "source": "CoinDesk",
                "link": "https://example.com/btc-etf-inflows",
                "published": datetime.now().isoformat(),
                "crypto_relevance": 0.95,
                "content": "Institutional investors poured a record $2.1 billion into Bitcoin ETFs yesterday, marking the highest single-day inflow since the funds launched..."
            },
            {
                "title": "Ethereum Layer 2 TVL Surpasses $40B as DeFi Activity Surges",
                "summary": "Total value locked in Ethereum Layer 2 solutions has reached a new milestone, driven by increased DeFi protocol adoption.",
                "source": "Decrypt",
                "link": "https://example.com/l2-tvl-surge",
                "published": datetime.now().isoformat(),
                "crypto_relevance": 0.88,
                "content": "Layer 2 scaling solutions for Ethereum have collectively surpassed $40 billion in total value locked (TVL), representing a 150% increase from the start of the year..."
            },
            {
                "title": "Major Bank Announces Crypto Custody Services for Institutional Clients",
                "summary": "A top-tier investment bank becomes the latest traditional financial institution to offer cryptocurrency custody solutions.",
                "source": "CoinTelegraph",
                "link": "https://example.com/bank-crypto-custody",
                "published": datetime.now().isoformat(),
                "crypto_relevance": 0.92,
                "content": "In a significant move toward mainstream adoption, one of the world's largest investment banks announced it will begin offering cryptocurrency custody services..."
            }
        ]
    
    def _create_initial_message(self, articles: List[Dict]) -> str:
        """Create the initial message to start editorial discussion"""
        article_summaries = "\n".join([
            f"• **Article {i+1}**: {article['title']} ({article['source']})\n  Summary: {article['summary'][:150]}..."
            for i, article in enumerate(articles)
        ])
        
        message = f"""🗞️ TECHRONICLE EDITORIAL MEETING - {datetime.now().strftime('%Y-%m-%d %H:%M')}

Welcome team! I've collected {len(articles)} breaking crypto stories for our editorial review:

{article_summaries}

**EDITORIAL REQUIREMENTS:**
✅ We MUST select and publish at least 1 article from today's discussion
✅ We can select multiple articles if they meet our standards
✅ All selected articles must pass fact-checking and editorial review

Gary, please present your findings and analysis of these stories. Then we'll have our collaborative discussion where:

• Aravind will provide market analysis and technical verification
• Tijana will fact-check and identify any legal/compliance issues  
• Aayushi will assess audience engagement potential
• Jerin will facilitate decisions and ensure we meet publication goals
• James will handle final publication logistics

Remember: We're not leaving this meeting without approving at least one story for publication. Let's find the best content that serves our readers!

Gary, take it away!"""

        return message
    
    def _run_group_discussion(self, initial_message: str) -> Any:
        """Run the group chat discussion with publication enforcement"""
        self.logger.logger.info("Starting group discussion")
        
        # Start the conversation
        chat_result = self.agents["gary"].initiate_chat(
            recipient=self.chat_manager,
            message=initial_message,
            clear_history=True
        )
        
        # Validate that at least one article was approved
        if not self._validate_publication_decisions():
            self.logger.logger.warning("No articles approved - enforcing publication requirement")
            self._enforce_publication_requirement()
        
        return chat_result
    
    def _validate_publication_decisions(self) -> bool:
        """Validate that at least one article has been approved for publication"""
        messages = self.group_chat.messages
        approved_articles = self._extract_approved_articles(messages)
        
        if len(approved_articles) >= 1:
            self.session_state["approved_articles"] = approved_articles
            return True
        
        return False
    
    def _extract_approved_articles(self, messages: List[Dict]) -> List[Dict]:
        """Extract approved articles from conversation"""
        approved = []
        
        for msg in messages:
            content = msg.get("content", "").lower()
            speaker = msg.get("name", "")
            
            # Look for explicit approval statements
            if any(phrase in content for phrase in [
                "approve", "publish", "select", "go with", "final decision"
            ]) and speaker in ["Jerin", "James"]:
                
                # Try to match to specific articles
                for i, article in enumerate(self.session_state["articles_collected"]):
                    article_title = article["title"].lower()
                    article_words = article_title.split()[:3]  # First 3 words
                    
                    if any(word in content for word in article_words):
                        if article not in approved:
                            approved.append(article)
                            self.logger.log_decision(
                                decision_maker=speaker,
                                decision=f"Approved: {article['title'][:60]}...",
                                reasoning=f"Extracted from: {content[:100]}...",
                                metadata={"article_index": i}
                            )
        
        return approved
    
    def _enforce_publication_requirement(self):
        """Enforce that at least one article must be published"""
        self.logger.logger.info("Enforcing publication requirement")
        
        # Have Jerin make an executive decision
        enforcement_message = f"""
        
**EDITORIAL OVERRIDE - JERIN SOJAN, MANAGING EDITOR**

Team, we've had a thorough discussion, but we haven't reached a clear publication decision. 

As Managing Editor, I need to ensure we publish content today. Based on our discussion, I'm making an executive decision:

**I'm approving the first article for publication: "{self.session_state['articles_collected'][0]['title']}"**

This story meets our basic standards and serves our readers' need for current crypto market information. While it may not be perfect, it's our responsibility to maintain consistent publication.

James, please prepare this article for immediate publication.

*Meeting adjourned - publication decision final.*
        """
        
        # Add enforcement message to conversation
        self.group_chat.messages.append({
            "name": "Jerin",
            "content": enforcement_message,
            "role": "assistant"
        })
        
        # Log the forced decision
        self.logger.log_decision(
            decision_maker="Jerin",
            decision=f"EXECUTIVE OVERRIDE: Approved {self.session_state['articles_collected'][0]['title'][:60]}...",
            reasoning="Editorial override to ensure publication requirement is met",
            metadata={"enforcement": True, "override": True}
        )
        
        # Mark article as approved
        self.session_state["approved_articles"] = [self.session_state["articles_collected"][0]]
    
    def _process_session_results(self, chat_result: Any) -> Dict[str, Any]:
        """Process and analyze the session results"""
        conversation_messages = self.group_chat.messages
        
        # Log all messages
        for msg in conversation_messages:
            self.logger.log_message(
                speaker=msg.get("name", "Unknown"),
                recipient="Team",
                content=msg.get("content", ""),
                message_type="editorial_discussion"
            )
        
        # Analyze conversation for decisions
        decisions = self._extract_decisions(conversation_messages)
        
        # Get approved articles
        approved_articles = self.session_state.get("approved_articles", [])
        
        # Ensure we have at least one publication
        if not approved_articles:
            self.logger.logger.error("No articles approved - this should not happen!")
            # Emergency fallback
            approved_articles = [self.session_state["articles_collected"][0]] if self.session_state["articles_collected"] else []
        
        # Create session summary
        session_summary = {
            "success": True,
            "session_id": self.session_id,
            "timestamp": datetime.now().isoformat(),
            "articles_discussed": len(self.session_state["articles_collected"]),
            "articles_approved": len(approved_articles),
            "articles_published": len(approved_articles),  # In our system, approved = published
            "total_messages": len(conversation_messages),
            "decisions_made": decisions,
            "approved_articles": approved_articles,
            "conversation_summary": self.logger.get_conversation_summary(),
            "participants": [agent.name for agent in self.agents.values()],
            "publication_requirement_met": len(approved_articles) >= 1
        }
        
        # Save approved articles as "published"
        self.session_state["published_articles"] = approved_articles
        self._save_published_articles(approved_articles)
        
        return session_summary
    
    def _save_published_articles(self, articles: List[Dict]):
        """Save approved articles as published content"""
        if not articles:
            return
        
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            for i, article in enumerate(articles):
                publication_data = {
                    "publication_id": f"tc_{self.session_id}_{i+1}",
                    "session_id": self.session_id,
                    "original_article": article,
                    "published_at": datetime.now().isoformat(),
                    "published_by": "Techronicle Editorial Team",
                    "publication_status": "published",
                    "editorial_process": {
                        "collected_by": "Gary",
                        "analyzed_by": "Aravind", 
                        "fact_checked_by": "Tijana",
                        "approved_by": "Jerin",
                        "published_by": "James"
                    }
                }
                
                filename = f"published_{publication_data['publication_id']}.json"
                filepath = config.published_dir / filename
                
                with open(filepath, 'w') as f:
                    json.dump(publication_data, f, indent=2, default=str)
                
                self.logger.logger.info(f"Saved published article: {filename}")
        
        except Exception as e:
            self.logger.logger.error(f"Error saving published articles: {e}")
    
    def _extract_decisions(self, messages: List[Dict]) -> List[Dict]:
        """Extract editorial decisions from conversation"""
        decisions = []
        
        for msg in messages:
            content = msg.get("content", "").lower()
            speaker = msg.get("name", "Unknown")
            
            # Look for decision keywords
            if any(keyword in content for keyword in ["decide", "publish", "approve", "select", "choose"]):
                decision = {
                    "decision_maker": speaker,
                    "timestamp": datetime.now().isoformat(),
                    "content": msg.get("content", ""),
                    "type": "editorial_decision"
                }
                decisions.append(decision)
                
                # Log as formal decision
                self.logger.log_decision(
                    decision_maker=speaker,
                    decision=content[:100] + "..." if len(content) > 100 else content,
                    reasoning="Extracted from conversation",
                    metadata={"message_index": len(decisions)}
                )
        
        return decisions
    
    def get_session_analytics(self) -> Dict[str, Any]:
        """Get analytics for the current session"""
        conversation_summary = self.logger.get_conversation_summary()
        
        return {
            "session_metrics": conversation_summary["stats"],
            "agent_participation": self._calculate_agent_participation(),
            "decision_timeline": self.session_state["decisions_made"],
            "content_metrics": self._analyze_content_metrics()
        }
    
    def _calculate_agent_participation(self) -> Dict[str, int]:
        """Calculate message count per agent"""
        participation = {}
        
        for msg in self.group_chat.messages:
            speaker = msg.get("name", "Unknown")
            participation[speaker] = participation.get(speaker, 0) + 1
        
        return participation
    
    def _analyze_content_metrics(self) -> Dict[str, Any]:
        """Analyze content and engagement metrics"""
        articles = self.session_state["articles_collected"]
        
        if not articles:
            return {}
        
        return {
            "total_articles": len(articles),
            "avg_crypto_relevance": sum(a.get("crypto_relevance", 0) for a in articles) / len(articles),
            "sources": list(set(a.get("source", "Unknown") for a in articles)),
            "topics_covered": self._extract_topics(articles)
        }
    
    def _extract_topics(self, articles: List[Dict]) -> List[str]:
        """Extract main topics from articles"""
        topics = []
        
        for article in articles:
            title = article.get("title", "").lower()
            
            # Simple keyword extraction
            if "bitcoin" in title or "btc" in title:
                topics.append("Bitcoin")
            if "ethereum" in title or "eth" in title:
                topics.append("Ethereum")
            if "defi" in title:
                topics.append("DeFi")
            if "nft" in title:
                topics.append("NFT")
            if "regulation" in title or "sec" in title:
                topics.append("Regulation")
            if "etf" in title:
                topics.append("ETF")
        
        return list(set(topics))
    
    def export_session(self, format: str = "json") -> str:
        """Export the session in various formats"""
        return self.logger.export_conversation(format)
    
    def save_session(self) -> str:
        """Save the session to file"""
        self.logger.save_conversation()
        return f"Session saved as conversation_{self.session_id}.json"