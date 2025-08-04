import React, { useState, useEffect, useRef } from 'react';
import { createPortal } from 'react-dom';
import { 
  Newspaper, 
  Users, 
  Play, 
  Square, 
  MessageCircle, 
  TrendingUp,
  CheckCircle,
  Clock,
  AlertCircle,
  ChevronDown,
  Eye,
  EyeOff,
  X,
  ExternalLink,
  Globe
} from 'lucide-react';
import './App.css';

// Published Article Modal Component
const ArticleModal = ({ article, isOpen, onClose }) => {
  if (!isOpen || !article) return null;

  // Extract the actual article content from the nested structure
  const actualArticle = article.original_article || article;
  const articleTitle = actualArticle.title || article.title;
  const articleContent = actualArticle.content || actualArticle.body || article.content || article.body;
  const articleSources = actualArticle.sources || article.sources || [actualArticle.source || article.source].filter(Boolean);
  const keyPoints = actualArticle.key_points || article.key_points || actualArticle.key_topics || [];

  console.log('ArticleModal - article data:', article);
  console.log('ArticleModal - extracted content:', articleContent);

  const modalContent = (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-2xl max-w-4xl w-full max-h-[90vh] overflow-y-auto shadow-2xl">
        {/* Article Header */}
        <div className="bg-gradient-to-r from-blue-600 to-purple-600 p-6 text-white">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <Newspaper size={24} />
              <div>
                <h1 className="text-2xl font-bold">Published Article</h1>
                <p className="text-blue-100">Live from Techronicle Newsroom</p>
              </div>
            </div>
            <button
              onClick={onClose}
              className="text-white/80 hover:text-white hover:bg-white/20 rounded-full p-2 transition-colors"
            >
              <X size={24} />
            </button>
          </div>
        </div>

        {/* Article Content */}
        <div className="p-8">
          {/* Article Meta */}
          <div className="mb-6 pb-4 border-b border-gray-200">
            <h1 className="text-3xl font-bold text-gray-900 mb-3">{articleTitle}</h1>
            <div className="flex items-center space-x-4 text-sm text-gray-600">
              <span className="flex items-center space-x-1">
                <Clock size={16} />
                <span>{new Date(article.published_at || actualArticle.published || Date.now()).toLocaleDateString()}</span>
              </span>
              <span className="flex items-center space-x-1">
                <Users size={16} />
                <span>Techronicle Editorial Team</span>
              </span>
              <span className="px-2 py-1 bg-blue-100 text-blue-800 rounded-full text-xs font-medium">
                {actualArticle.category || 'Technology'}
              </span>
              {article.publication_id && (
                <span className="px-2 py-1 bg-gray-100 text-gray-600 rounded-full text-xs font-medium">
                  ID: {article.publication_id}
                </span>
              )}
            </div>
          </div>

          {/* Article Body */}
          <div className="prose prose-lg max-w-none">
            {articleContent ? (
              <div className="text-gray-800 leading-relaxed space-y-4">
                {articleContent.split('\n\n').map((paragraph, index) => (
                  <p key={index} className="mb-4 text-justify">
                    {paragraph}
                  </p>
                ))}
              </div>
            ) : (
              <div className="text-center py-12">
                <div className="text-gray-600">
                  <p className="mb-2">📰 Article content not available</p>
                  <p className="text-sm">Please check your backend configuration</p>
                  <div className="mt-4 text-xs text-gray-500">
                    <p>Debug info: {JSON.stringify({
                      hasArticle: !!article,
                      hasOriginalArticle: !!article.original_article,
                      hasContent: !!articleContent,
                      keys: Object.keys(article || {})
                    })}</p>
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Key Points Section */}
          {keyPoints && keyPoints.length > 0 && (
            <div className="mt-8 p-6 bg-blue-50 rounded-xl border border-blue-200">
              <h3 className="text-lg font-semibold text-blue-900 mb-3 flex items-center">
                <TrendingUp size={18} className="mr-2" />
                {actualArticle.key_topics ? 'Key Topics' : 'Key Points'}
              </h3>
              <ul className="space-y-2">
                {keyPoints.map((point, index) => (
                  <li key={index} className="flex items-start space-x-2 text-blue-800">
                    <span className="text-blue-500 mt-1">•</span>
                    <span>{point}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Article Stats */}
          {(actualArticle.word_count || actualArticle.sentiment || actualArticle.crypto_relevance) && (
            <div className="mt-8 p-6 bg-gray-50 rounded-xl border border-gray-200">
              <h3 className="text-lg font-semibold text-gray-900 mb-3">Article Analytics</h3>
              <div className="grid grid-cols-3 gap-4 text-center">
                {actualArticle.word_count && (
                  <div>
                    <div className="text-2xl font-bold text-gray-900">{actualArticle.word_count}</div>
                    <div className="text-sm text-gray-600">Words</div>
                  </div>
                )}
                {actualArticle.sentiment && (
                  <div>
                    <div className="text-2xl font-bold text-gray-900 capitalize">{actualArticle.sentiment}</div>
                    <div className="text-sm text-gray-600">Sentiment</div>
                  </div>
                )}
                {actualArticle.crypto_relevance && (
                  <div>
                    <div className="text-2xl font-bold text-gray-900">{Math.round(actualArticle.crypto_relevance * 100)}%</div>
                    <div className="text-sm text-gray-600">Relevance</div>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Sources Section */}
          {articleSources && articleSources.length > 0 && (
            <div className="mt-8 pt-6 border-t border-gray-200">
              <h3 className="text-lg font-semibold text-gray-900 mb-3 flex items-center">
                <ExternalLink size={18} className="mr-2" />
                Sources
              </h3>
              <div className="space-y-2">
                {articleSources.map((source, index) => (
                  <div key={index} className="flex items-center space-x-2 text-sm text-gray-600">
                    <span className="text-gray-400">•</span>
                    <span>{typeof source === 'string' ? source : source.name || source.url || source}</span>
                  </div>
                ))}
              </div>
              {actualArticle.link && (
                <div className="mt-3 p-3 bg-blue-50 rounded-lg">
                  <a 
                    href={actualArticle.link} 
                    target="_blank" 
                    rel="noopener noreferrer"
                    className="text-blue-600 hover:text-blue-800 text-sm flex items-center space-x-1"
                  >
                    <ExternalLink size={14} />
                    <span>View Original Article</span>
                  </a>
                </div>
              )}
            </div>
          )}

          {/* Article Metadata */}
          <div className="mt-8 pt-6 border-t border-gray-200 bg-gray-50 rounded-lg p-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
              <div>
                <p className="font-medium text-gray-900">Published by {article.published_by || 'Techronicle AI Newsroom'}</p>
                <p className="text-gray-600">Collaborative editorial decision by our AI team</p>
                {article.session_id && (
                  <p className="text-gray-500 mt-1">Session: {article.session_id}</p>
                )}
              </div>
              <div className="text-right">
                {actualArticle.word_count && (
                  <p className="text-gray-600">Word Count: {actualArticle.word_count}</p>
                )}
                {actualArticle.processing_status && (
                  <p className="text-gray-600">Status: {actualArticle.processing_status}</p>
                )}
                <p className="text-gray-500 text-xs mt-1">
                  Published: {new Date(article.published_at || Date.now()).toLocaleString()}
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );

  return createPortal(modalContent, document.body);
};

// Published Article Button Component
const PublishedArticleButton = ({ article, onViewArticle }) => {
  return (
    <div className="mt-6 p-4 bg-green-500/20 backdrop-blur-sm rounded-2xl border border-green-500/30">
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <div className="w-8 h-8 bg-green-500 rounded-full flex items-center justify-center">
            <CheckCircle size={16} className="text-white" />
          </div>
          <div>
            <h4 className="text-white font-semibold">Article Published!</h4>
            <p className="text-green-200 text-sm">
              {article?.title || 'The editorial decision has been made and the article is now live'}
            </p>
          </div>
        </div>
        <button
          onClick={onViewArticle}
          className="bg-green-500 hover:bg-green-600 text-white px-4 py-2 rounded-xl font-medium transition-colors duration-200 flex items-center space-x-2"
        >
          <Eye size={16} />
          <span>Read Article</span>
        </button>
      </div>
    </div>
  );
};

// Agent Profile Modal Component
const AgentModal = ({ agent, isOpen, onClose }) => {
  if (!isOpen || !agent) return null;

  const getAgentColor = (key) => {
    const colors = {
      gary: 'from-blue-500 to-blue-600',
      aravind: 'from-purple-500 to-purple-600',
      tijana: 'from-orange-500 to-orange-600',
      jerin: 'from-green-500 to-green-600',
      aayushi: 'from-pink-500 to-pink-600',
      james: 'from-lime-500 to-lime-600'
    };
    return colors[key] || 'from-gray-500 to-gray-600';
  };

  const modalContent = (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-2xl max-w-2xl w-full max-h-[90vh] overflow-y-auto shadow-2xl">
        {/* Modal Header */}
        <div className={`bg-gradient-to-r ${getAgentColor(agent.key)} p-6 text-white`}>
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <div className="w-32 h-32 rounded-full overflow-hidden border-4 border-white shadow-xl">
                <img 
                  src={`/images/${agent.key}.jpg`}
                  alt={agent.name}
                  className="w-full h-full object-cover"
                  onError={(e) => {
                    e.target.style.display = 'none';
                    e.target.nextSibling.style.display = 'flex';
                  }}
                />
                <div 
                  className="w-full h-full bg-white/20 flex items-center justify-center text-white text-4xl font-bold"
                  style={{ display: 'none' }}
                >
                  {agent.name[0]}
                </div>
              </div>
              <div>
                <h2 className="text-2xl font-bold">{agent.full_name || agent.name}</h2>
                <p className="text-white/90 text-lg">{agent.role}</p>
                <span className="inline-block px-3 py-1 bg-white/20 rounded-full text-sm font-medium mt-2">
                  🟢 Active
                </span>
              </div>
            </div>
            <button
              onClick={onClose}
              className="text-white/80 hover:text-white hover:bg-white/20 rounded-full p-2 transition-colors"
            >
              <X size={24} />
            </button>
          </div>
        </div>

        {/* Agent Stats */}
        <div className="p-6 border-b border-gray-200">
          <h3 className="text-lg font-semibold mb-4 text-gray-900">Agent Information</h3>
          <div className="grid grid-cols-3 gap-4">
            <div className="bg-gray-50 p-4 rounded-lg text-center border">
              <div className="text-2xl font-bold text-gray-900">{agent.age || 'N/A'}</div>
              <div className="text-sm text-gray-600">Age</div>
            </div>
            <div className="bg-gray-50 p-4 rounded-lg text-center border">
              <div className="text-2xl font-bold text-gray-900">0.7</div>
              <div className="text-sm text-gray-600">Temperature</div>
            </div>
            <div className="bg-gray-50 p-4 rounded-lg text-center border">
              <div className="text-2xl font-bold text-gray-900">AI</div>
              <div className="text-sm text-gray-600">Type</div>
            </div>
          </div>
        </div>

        {/* System Message */}
        <div className="p-6">
          <h3 className="text-lg font-semibold mb-4 text-gray-900">System Instructions</h3>
          <div className="bg-gray-50 border rounded-lg p-4 max-h-64 overflow-y-auto">
            <pre className="text-sm text-gray-800 whitespace-pre-wrap font-mono leading-relaxed">
              {agent.system_message || 'Loading system message...'}
            </pre>
          </div>
          
          {/* Additional Info */}
          <div className="mt-6 grid grid-cols-1 gap-4">
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
              <h4 className="font-semibold text-blue-900 mb-2">Primary Responsibilities</h4>
              <p className="text-blue-800 text-sm">
                {agent.role === 'Beat Reporter' && 'Collects and analyzes breaking news stories using AI tools and fact-checking systems.'}
                {agent.role === 'Market Analyst' && 'Provides market context and economic analysis for financial and tech stories.'}
                {agent.role === 'Copy Editor' && 'Reviews articles for accuracy, style, and editorial standards before publication.'}
                {agent.role === 'Managing Editor' && 'Makes final editorial decisions and oversees the newsroom workflow.'}
                {agent.role === 'Audience Editor' && 'Focuses on audience engagement and social media optimization.'}
                {agent.role === 'Publishing Manager' && 'Handles final publication and distribution across platforms.'}
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );

  return createPortal(modalContent, document.body);
};

// Progress Steps Component
const ProgressSteps = ({ currentStep, stepTimes }) => {
  const steps = [
    { id: 'collect', label: 'Collecting Articles', icon: '🔍' },
    { id: 'analyze', label: 'Market Analysis', icon: '📊' },
    { id: 'review', label: 'Editorial Review', icon: '✏️' },
    { id: 'decide', label: 'Editorial Decision', icon: '⚖️' },
    { id: 'publish', label: 'Publishing', icon: '🚀' }
  ];

  const getStepStatus = (stepId, index) => {
    if (currentStep > index) return 'completed';
    if (currentStep === index) return 'active';
    return 'pending';
  };

  const formatTime = (seconds) => {
    if (!seconds) return '';
    return seconds > 60 
      ? `${Math.floor(seconds / 60)}m ${seconds % 60}s`
      : `${seconds}s`;
  };

  return (
    <div className="bg-white/80 backdrop-blur-sm rounded-lg p-4 mb-4">
      <h3 className="text-sm font-semibold text-gray-700 mb-3 flex items-center">
        <Clock size={16} className="mr-2" />
        Editorial Workflow Progress
      </h3>
      <div className="space-y-2">
        {steps.map((step, index) => {
          const status = getStepStatus(step.id, index);
          const time = stepTimes[step.id];
          
          return (
            <div key={step.id} className="flex items-center space-x-3">
              <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm ${
                status === 'completed' 
                  ? 'bg-green-500 text-white' 
                  : status === 'active'
                  ? 'bg-blue-500 text-white animate-pulse'
                  : 'bg-gray-300 text-gray-600'
              }`}>
                {status === 'completed' ? '✓' : step.icon}
              </div>
              <div className="flex-1">
                <div className="text-sm font-medium text-gray-900">{step.label}</div>
                {time && (
                  <div className="text-xs text-gray-500">{formatTime(time)}</div>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};

// Article Processing Component
const ArticleProcessing = ({ articles }) => {
  if (!articles || articles.length === 0) return null;

  return (
    <div className="bg-white/90 backdrop-blur-sm rounded-lg p-4 mb-4 border border-white/20">
      <h3 className="text-sm font-semibold text-gray-700 mb-3 flex items-center">
        <Globe size={16} className="mr-2" />
        Processing Articles
      </h3>
      <div className="space-y-2 max-h-40 overflow-y-auto">
        {articles.map((article, index) => (
          <div key={index} className="flex items-center space-x-3 p-2 bg-white/50 rounded border">
            <div className="w-2 h-2 bg-blue-500 rounded-full animate-pulse"></div>
            <div className="flex-1 min-w-0">
              <div className="text-sm font-medium text-gray-900 truncate">
                {article.title || `Article ${index + 1}`}
              </div>
              <div className="text-xs text-gray-600">
                from {article.source || 'Unknown Source'}
              </div>
            </div>
            <ExternalLink size={12} className="text-gray-400" />
          </div>
        ))}
      </div>
    </div>
  );
};

// Modern Chat Message Component
const ChatMessage = ({ message, onToggleExpand, isExpanded }) => {
  const getAgentColor = (speaker) => {
    const colors = {
      gary: 'bg-blue-500',
      aravind: 'bg-purple-500',
      tijana: 'bg-orange-500',
      jerin: 'bg-green-500',
      aayushi: 'bg-pink-500',
      james: 'bg-lime-500'
    };
    return colors[speaker.toLowerCase()] || 'bg-gray-500';
  };

  const getAgentEmoji = (speaker) => {
    const emojis = {
      gary: '📰',
      aravind: '🔍',
      tijana: '✏️',
      jerin: '⚖️',
      aayushi: '📱',
      james: '🚀'
    };
    return emojis[speaker.toLowerCase()] || '🤖';
  };

  const timestamp = new Date(message.timestamp).toLocaleTimeString([], { 
    hour: '2-digit', 
    minute: '2-digit' 
  });
  
  const isLongMessage = message.content.length > 300;
  const displayContent = isLongMessage && !isExpanded 
    ? message.content.substring(0, 300) + '...' 
    : message.content;

  return (
    <div className="flex items-start space-x-3 p-4 hover:bg-white/5 rounded-2xl transition-colors message-enter">
      {/* Avatar */}
      <div className="flex-shrink-0">
        <div className={`w-10 h-10 rounded-full ${getAgentColor(message.speaker)} 
                        flex items-center justify-center text-white font-semibold shadow-lg
                        ring-2 ring-white/20`}>
          <img 
            src={`/images/${message.speaker.toLowerCase()}.jpg`}
            alt={message.speaker}
            className="w-full h-full object-cover rounded-full"
            onError={(e) => {
              e.target.style.display = 'none';
              e.target.nextSibling.style.display = 'flex';
            }}
          />
          <span style={{ display: 'none' }}>
            {message.speaker[0]}
          </span>
        </div>
      </div>

      {/* Message Content */}
      <div className="flex-1 min-w-0">
        {/* Header */}
        <div className="flex items-center space-x-2 mb-1">
          <span className="font-semibold text-white">{message.speaker}</span>
          <span className="text-white/60 text-sm">{message.designation}</span>
          <span className="text-white/40 text-xs">{timestamp}</span>
          
          {/* Message Type Badges */}
          {message.message_type === 'decision' && (
            <span className="px-2 py-1 text-xs font-medium bg-yellow-500/20 text-yellow-200 rounded-full border border-yellow-500/30">
              ⚖️ DECISION
            </span>
          )}
          {message.message_type === 'tool' && (
            <span className="px-2 py-1 text-xs font-medium bg-green-500/20 text-green-200 rounded-full border border-green-500/30">
              🔧 ANALYSIS
            </span>
          )}
        </div>

        {/* Message Text */}
        <div className="bg-white/10 backdrop-blur-sm rounded-2xl p-4 border border-white/20">
          <div className="text-white/90 leading-relaxed whitespace-pre-wrap">
            {displayContent}
          </div>
          
          {isLongMessage && (
            <button
              onClick={() => onToggleExpand(message.id)}
              className="mt-2 text-sm text-blue-300 hover:text-blue-200 flex items-center space-x-1 transition-colors"
            >
              {isExpanded ? <EyeOff size={16} /> : <Eye size={16} />}
              <span>{isExpanded ? 'Show less' : 'Show more'}</span>
            </button>
          )}
        </div>
      </div>
    </div>
  );
};

// Team Member Component
const TeamMember = ({ agent, isActive, onClick }) => {
  const getAgentColor = (key) => {
    const colors = {
      gary: 'bg-blue-500',
      aravind: 'bg-purple-500',
      tijana: 'bg-orange-500',
      jerin: 'bg-green-500',
      aayushi: 'bg-pink-500',
      james: 'bg-lime-500'
    };
    return colors[key] || 'bg-gray-500';
  };

  return (
    <div
      onClick={() => onClick(agent)}
      className={`p-3 rounded-lg cursor-pointer transition-all duration-300 ${
        isActive 
          ? 'bg-white shadow-lg ring-2 ring-blue-400 transform scale-105' 
          : 'bg-white/70 hover:bg-white hover:shadow-md'
      }`}
    >
      <div className="text-center">
        <div className="w-12 h-12 rounded-full overflow-hidden mx-auto mb-2 border-2 border-white shadow-lg relative">
          <img 
            src={`/images/${agent.key}.jpg`}
            alt={agent.name}
            className="w-full h-full object-cover"
            onError={(e) => {
              e.target.style.display = 'none';
              e.target.nextElementSibling.style.display = 'flex';
            }}
          />
          <div 
            className={`w-full h-full ${getAgentColor(agent.key)} flex items-center justify-center text-white text-xl font-bold absolute inset-0`}
            style={{ display: 'none' }}
          >
            {agent.name[0]}
          </div>
          
          {isActive && (
            <div className="absolute -top-1 -right-1 w-4 h-4 bg-green-500 rounded-full border-2 border-white animate-pulse">
              <div className="w-full h-full bg-green-400 rounded-full animate-ping"></div>
            </div>
          )}
        </div>
        
        <div className="text-sm font-semibold text-gray-900">{agent.name}</div>
        <div className="text-xs text-gray-600">{agent.role}</div>
        
        {isActive && (
          <div className="mt-1 text-xs text-green-600 font-medium">
            Speaking...
          </div>
        )}
      </div>
    </div>
  );
};

// Main App Component
function App() {
  // State management
  const [isConnected, setIsConnected] = useState(false);
  const [sessionRunning, setSessionRunning] = useState(false);
  const [messages, setMessages] = useState([]);
  const [status, setStatus] = useState({ type: 'ready', message: 'Ready for editorial meeting' });
  const [articlesCount, setArticlesCount] = useState(5);
  const [expandedMessages, setExpandedMessages] = useState(new Set());
  const [activeSpeaker, setActiveSpeaker] = useState(null);
  const [currentStep, setCurrentStep] = useState(-1);
  const [stepTimes, setStepTimes] = useState({});
  const [selectedAgent, setSelectedAgent] = useState(null);
  const [agentProfiles, setAgentProfiles] = useState({});
  const [processingArticles, setProcessingArticles] = useState([]);
  const [publishedArticle, setPublishedArticle] = useState(null);
  const [conversationEnded, setConversationEnded] = useState(false);
  const [showArticleModal, setShowArticleModal] = useState(false);
  
  // WebSocket and refs
  const ws = useRef(null);
  const chatContainerRef = useRef(null);
  const speakerTimeoutRef = useRef(null);

  // Team data
  const teamMembers = [
    { key: 'gary', name: 'Gary', role: 'Beat Reporter', full_name: 'Gary Poussin', age: 28 },
    { key: 'aravind', name: 'Aravind', role: 'Market Analyst', full_name: 'Dr. Aravind Rajen', age: 34 },
    { key: 'tijana', name: 'Tijana', role: 'Copy Editor', full_name: 'Tijana Jekic', age: 31 },
    { key: 'jerin', name: 'Jerin', role: 'Managing Editor', full_name: 'Jerin Sojan', age: 38 },
    { key: 'aayushi', name: 'Aayushi', role: 'Audience Editor', full_name: 'Aayushi Patel', age: 26 },
    { key: 'james', name: 'James', role: 'Publishing Manager', full_name: 'James Guerra', age: 29 }
  ];

  // Load agent profiles on mount
  useEffect(() => {
    const loadAgentProfiles = async () => {
      try {
        const response = await fetch('http://localhost:8000/api/agents');
        const profiles = await response.json();
        setAgentProfiles(profiles);
      } catch (error) {
        console.error('Failed to load agent profiles:', error);
      }
    };
    
    loadAgentProfiles();
  }, []);

  // WebSocket connection
  useEffect(() => {
    const connectWebSocket = () => {
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const wsUrl = `${protocol}//localhost:8000/ws`;
      
      ws.current = new WebSocket(wsUrl);
      
      ws.current.onopen = () => {
        setIsConnected(true);
        console.log('Connected to WebSocket');
      };
      
      ws.current.onmessage = (event) => {
        const data = JSON.parse(event.data);
        handleWebSocketMessage(data);
      };
      
      ws.current.onclose = () => {
        setIsConnected(false);
        setTimeout(connectWebSocket, 3000);
      };
      
      ws.current.onerror = (error) => {
        console.error('WebSocket error:', error);
      };
    };

    connectWebSocket();

    return () => {
      if (ws.current) {
        ws.current.close();
      }
    };
  }, []);

  // Load latest published article
  const loadLatestPublishedArticle = async () => {
    try {
      console.log('Attempting to load latest published article...');
      const response = await fetch('http://localhost:8000/api/latest-published-article');
      
      if (response.ok) {
        const article = await response.json();
        console.log('Article loaded successfully:', article);
        setPublishedArticle(article);
      } else {
        console.warn('Failed to load article, using fallback');
        // Fallback article if API fails
        setPublishedArticle({
          id: 'fallback-' + Date.now(),
          title: 'Article Published Successfully',
          content: 'The editorial team has completed their review and the article has been published. The actual article content will be available once the backend API is properly configured.',
          timestamp: new Date().toISOString(),
          category: 'Technology',
          sources: ['Techronicle Editorial Team'],
          key_points: ['Article has been reviewed and approved', 'Published to designated channels']
        });
      }
    } catch (error) {
      console.error('Failed to load latest published article:', error);
      // Fallback article on error
      setPublishedArticle({
        id: 'error-fallback-' + Date.now(),
        title: 'Editorial Decision Complete',
        content: 'The AI editorial team has successfully completed their collaborative decision-making process. The article has been reviewed, approved, and is now ready for publication.\n\nTo view the actual published article content, please ensure your backend API endpoint "/api/latest-published-article" is properly configured to serve files from the techronicle-autogen/data/published directory.',
        timestamp: new Date().toISOString(),
        category: 'System',
        sources: ['Techronicle AI Editorial System'],
        key_points: [
          'Editorial workflow completed successfully',
          'Article approved by managing editor',
          'Ready for publication across platforms'
        ]
      });
    }
  };

  // Handle WebSocket messages
  const handleWebSocketMessage = (data) => {
    switch (data.type) {
      case 'conversation_history':
        setMessages(data.messages.map(msg => ({ ...msg, id: Math.random().toString(36) })));
        break;
      case 'new_message':
        const newMessage = { ...data.message, id: Math.random().toString(36) };
        setMessages(prev => [...prev, newMessage]);
        
        setActiveSpeaker(newMessage.speaker.toLowerCase());
        clearTimeout(speakerTimeoutRef.current);
        speakerTimeoutRef.current = setTimeout(() => {
          setActiveSpeaker(null);
        }, 5000);
        
        updateProgressFromMessage(newMessage);
        break;
      case 'status_update':
        setStatus({ type: data.status, message: data.details || data.status });
        setSessionRunning(['running', 'initializing'].includes(data.status));
        
        if (data.status === 'running') {
          setCurrentStep(0);
          setConversationEnded(false);
          setPublishedArticle(null);
        } else if (data.status === 'completed') {
          setCurrentStep(5);
          setProcessingArticles([]);
          setConversationEnded(true);
          // Load the actual latest published article from the backend
          setTimeout(() => {
            loadLatestPublishedArticle();
          }, 1000); // Small delay to ensure article is written to disk
        }
        break;
      case 'article_processing':
        // Handle article processing updates
        if (data.articles) {
          setProcessingArticles(data.articles);
        }
        break;
      case 'article_published':
        // Handle when backend sends the actual published article
        if (data.article) {
          setPublishedArticle(data.article);
          setConversationEnded(true);
        }
        break;
      case 'error':
        console.error('WebSocket error:', data.message);
        break;
    }
  };

  // Update progress based on message content
  const updateProgressFromMessage = (message) => {
    const content = message.content.toLowerCase();
    const speaker = message.speaker.toLowerCase();

    if (speaker === 'gary' && (content.includes('collecting') || content.includes('processing'))) {
      setCurrentStep(0);
    } else if (speaker === 'aravind' && content.includes('analysis')) {
      setCurrentStep(1);
      setStepTimes(prev => ({ ...prev, collect: 15 }));
    } else if (speaker === 'tijana' && (content.includes('review') || content.includes('fact'))) {
      setCurrentStep(2);
      setStepTimes(prev => ({ ...prev, analyze: 25 }));
    } else if (speaker === 'jerin' && (content.includes('decision') || content.includes('approve'))) {
      setCurrentStep(3);
      setStepTimes(prev => ({ ...prev, review: 18 }));
    } else if (speaker === 'james' && (content.includes('publish') || content.includes('slack'))) {
      setCurrentStep(4);
      setStepTimes(prev => ({ ...prev, decide: 12 }));
    }
  };

  // Auto-scroll to bottom
  useEffect(() => {
    if (chatContainerRef.current) {
      chatContainerRef.current.scrollTop = chatContainerRef.current.scrollHeight;
    }
  }, [messages]);

  // Start session
  const startSession = () => {
    if (!isConnected) {
      console.error('WebSocket not connected');
      return;
    }
    
    console.log('Starting session with', articlesCount, 'articles');
    
    // Mock processing articles for demo (replace with real data from backend)
    setProcessingArticles([
      { title: 'Apple Reports Strong Q4 Earnings', source: 'Reuters' },
      { title: 'Meta Announces New AI Initiative', source: 'TechCrunch' },
      { title: 'Tesla Stock Surges on Delivery Numbers', source: 'Bloomberg' },
      { title: 'Google Launches New Cloud Services', source: 'The Verge' },
      { title: 'Microsoft Azure Growth Continues', source: 'Forbes' }
    ].slice(0, articlesCount));
    
    ws.current.send(JSON.stringify({
      type: 'start_session',
      articles_count: articlesCount
    }));
    
    setMessages([]);
    setCurrentStep(-1);
    setStepTimes({});
    setConversationEnded(false);
    setPublishedArticle(null);
    setShowArticleModal(false);
  };

  // Stop session
  const stopSession = () => {
    if (!isConnected) return;
    
    ws.current.send(JSON.stringify({
      type: 'stop_session'
    }));
    
    setProcessingArticles([]);
    setConversationEnded(false);
    setPublishedArticle(null);
    setShowArticleModal(false);
  };

  // Handle agent click
  const handleAgentClick = async (agent) => {
    console.log('Agent clicked:', agent);
    
    try {
      const response = await fetch(`http://localhost:8000/api/agent/${agent.key}`);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const agentDetails = await response.json();
      
      const fullAgent = {
        ...agent,
        ...agentDetails
      };
      
      setSelectedAgent(fullAgent);
      
    } catch (error) {
      console.error('Failed to load agent details:', error);
      // Still show modal with basic info if API fails
      setSelectedAgent(agent);
    }
  };

  // Close agent modal
  const closeAgentModal = () => {
    setSelectedAgent(null);
  };

  // Handle article modal
  const openArticleModal = () => {
    setShowArticleModal(true);
  };

  const closeArticleModal = () => {
    setShowArticleModal(false);
  };

  // Toggle message expansion
  const toggleMessageExpansion = (messageId) => {
    const newExpanded = new Set(expandedMessages);
    if (newExpanded.has(messageId)) {
      newExpanded.delete(messageId);
    } else {
      newExpanded.add(messageId);
    }
    setExpandedMessages(newExpanded);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-600 via-purple-600 to-blue-800">
      {/* Live indicator */}
      {sessionRunning && (
        <div className="fixed top-4 right-4 z-40 bg-red-500 text-white px-3 py-1 rounded-full text-sm font-medium animate-pulse">
          🔴 LIVE MEETING
        </div>
      )}

      <div className="max-w-7xl mx-auto p-6 grid grid-cols-1 lg:grid-cols-4 gap-6 h-screen">
        {/* Sidebar */}
        <div className="lg:col-span-1 bg-white/20 backdrop-blur-md rounded-2xl p-6 overflow-y-auto">
          <div className="mb-6">
            <h1 className="text-2xl font-bold text-white mb-2 flex items-center">
              <Newspaper className="mr-2" />
              Techronicle
            </h1>
            <p className="text-white/80 text-sm">Live Editorial Meeting</p>
            
            {/* Status indicator */}
            <div className={`mt-4 flex items-center space-x-2 px-3 py-2 rounded-lg ${
              status.type === 'ready' ? 'bg-green-500/20 text-green-100' :
              status.type === 'running' ? 'bg-blue-500/20 text-blue-100' :
              status.type === 'completed' ? 'bg-green-500/20 text-green-100' :
              'bg-red-500/20 text-red-100'
            }`}>
              {status.type === 'running' ? (
                <div className="w-2 h-2 bg-current rounded-full animate-pulse"></div>
              ) : status.type === 'completed' ? (
                <CheckCircle size={16} />
              ) : status.type === 'error' ? (
                <AlertCircle size={16} />
              ) : (
                <div className="w-2 h-2 bg-current rounded-full"></div>
              )}
              <span className="text-sm">{status.message}</span>
            </div>
          </div>

          {/* Controls */}
          <div className="mb-6 space-y-4">
            <div>
              <label className="block text-white/80 text-sm font-medium mb-2">
                Articles to Process
              </label>
              <input
                type="number"
                min="1"
                max="10"
                value={articlesCount}
                onChange={(e) => setArticlesCount(parseInt(e.target.value) || 5)}
                className="w-full px-3 py-2 bg-white/20 backdrop-blur-sm border border-white/30 rounded-lg text-white placeholder-white/50 focus:outline-none focus:ring-2 focus:ring-blue-400"
                disabled={sessionRunning}
              />
            </div>
            
            <button
              onClick={startSession}
              disabled={!isConnected || sessionRunning}
              className="w-full bg-green-500 hover:bg-green-600 disabled:bg-gray-500 disabled:cursor-not-allowed text-white font-medium py-3 px-4 rounded-lg transition-colors duration-200 flex items-center justify-center space-x-2"
            >
              <Play size={16} />
              <span>{sessionRunning ? 'Meeting in Progress...' : 'Start Editorial Meeting'}</span>
            </button>
            
            <button
              onClick={stopSession}
              disabled={!sessionRunning}
              className="w-full bg-red-500 hover:bg-red-600 disabled:bg-gray-500 disabled:cursor-not-allowed text-white font-medium py-3 px-4 rounded-lg transition-colors duration-200 flex items-center justify-center space-x-2"
            >
              <Square size={16} />
              <span>End Meeting</span>
            </button>
          </div>

          {/* Article Processing */}
          {processingArticles.length > 0 && (
            <ArticleProcessing articles={processingArticles} />
          )}

          {/* Progress Steps */}
          {sessionRunning && (
            <ProgressSteps currentStep={currentStep} stepTimes={stepTimes} />
          )}

          {/* Team Members */}
          <div className="mb-6">
            <h3 className="text-white font-semibold mb-3 flex items-center">
              <Users size={16} className="mr-2" />
              Editorial Team
            </h3>
            <div className="grid grid-cols-2 gap-3">
              {teamMembers.map((member) => (
                <TeamMember
                  key={member.key}
                  agent={member}
                  isActive={activeSpeaker === member.key}
                  onClick={handleAgentClick}
                />
              ))}
            </div>
          </div>

          {/* Connection status */}
          <div className="text-center">
            <div className={`inline-flex items-center space-x-2 px-3 py-1 rounded-full text-xs ${
              isConnected ? 'bg-green-500/20 text-green-100' : 'bg-red-500/20 text-red-100'
            }`}>
              <div className={`w-2 h-2 rounded-full ${isConnected ? 'bg-green-500' : 'bg-red-500'}`}></div>
              <span>{isConnected ? 'Connected' : 'Connecting...'}</span>
            </div>
          </div>
        </div>

        {/* Main Chat Area */}
        <div className="lg:col-span-3 bg-white/20 backdrop-blur-md rounded-2xl flex flex-col overflow-hidden">
          {/* Header */}
          <div className="p-6 border-b border-white/20">
            <h2 className="text-xl font-bold text-white mb-1 flex items-center">
              <MessageCircle className="mr-2" />
              Live Editorial Discussion
            </h2>
            <p className="text-white/80 text-sm">
              Real-time collaborative decision making • {messages.length} messages
            </p>
          </div>

          {/* Messages */}
          <div 
            ref={chatContainerRef}
            className="flex-1 overflow-y-auto p-6 space-y-4"
          >
            {messages.length === 0 ? (
              <div className="text-center py-12">
                <MessageCircle size={48} className="mx-auto text-white/40 mb-4" />
                <h3 className="text-white/80 text-lg font-medium mb-2">No active editorial meeting</h3>
                <p className="text-white/60 text-sm max-w-md mx-auto">
                  Start a new meeting to see the live editorial discussion between our AI newsroom team
                </p>
                <div className="mt-6 text-white/50 text-sm">
                  <p className="font-medium mb-2">Editorial Workflow:</p>
                  <ul className="text-left inline-block space-y-1">
                    <li>• Gary collects and analyzes stories with AI tools</li>
                    <li>• Team discusses articles like a real editorial meeting</li>
                    <li>• Collaborative decision-making process</li>
                    <li>• James publishes approved articles to Slack</li>
                  </ul>
                </div>
              </div>
            ) : (
              messages.map((message) => (
                <ChatMessage
                  key={message.id}
                  message={message}
                  onToggleExpand={toggleMessageExpansion}
                  isExpanded={expandedMessages.has(message.id)}
                />
              ))
            )}
            
            {/* Published Article Button - Show at end of conversation */}
            {conversationEnded && publishedArticle && (
              <PublishedArticleButton 
                article={publishedArticle}
                onViewArticle={openArticleModal}
              />
            )}
          </div>
        </div>
      </div>

      {/* Agent Profile Modal */}
      <AgentModal 
        agent={selectedAgent}
        isOpen={!!selectedAgent}
        onClose={closeAgentModal}
      />

      {/* Published Article Modal */}
      <ArticleModal 
        article={publishedArticle}
        isOpen={showArticleModal}
        onClose={closeArticleModal}
      />
    </div>
  );
}

export default App;