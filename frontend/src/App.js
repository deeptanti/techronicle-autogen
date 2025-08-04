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
  EyeOff
} from 'lucide-react';
import './App.css';

// SUPER SIMPLE Modal for debugging - MOVED OUTSIDE App component
const AgentModal = ({ agent, isOpen, onClose }) => {
  // Force log every render attempt
  console.log('=== MODAL COMPONENT CALLED ===');
  console.log('isOpen:', isOpen);
  console.log('agent:', agent);
  console.log('typeof isOpen:', typeof isOpen);
  console.log('!!agent:', !!agent);
  console.log('==============================');
  
  if (!isOpen || !agent) {
    console.log('Modal returning null because isOpen=', isOpen, 'agent=', !!agent);
    return null;
  }

  console.log('🚨🚨🚨 MODAL SHOULD RENDER NOW!!! 🚨🚨🚨');

  // Create the most basic possible modal
  const modalContent = (
    <div 
      style={{
        position: 'fixed',
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        backgroundColor: 'red', // Very visible red background
        zIndex: 999999,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        fontSize: '24px',
        color: 'white',
        fontWeight: 'bold'
      }}
      onClick={onClose}
    >
      <div 
        style={{
          backgroundColor: 'blue',
          padding: '40px',
          borderRadius: '10px',
          textAlign: 'center'
        }}
        onClick={(e) => e.stopPropagation()}
      >
        <h1>MODAL IS WORKING!</h1>
        <p>Agent: {agent.name}</p>
        <p>Role: {agent.role}</p>
        <button 
          onClick={onClose}
          style={{
            backgroundColor: 'white',
            color: 'black',
            padding: '10px 20px',
            border: 'none',
            borderRadius: '5px',
            fontSize: '16px',
            cursor: 'pointer',
            marginTop: '20px'
          }}
        >
          CLOSE
        </button>
      </div>
    </div>
  );

  console.log('About to return modal portal');
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

// Component for individual messages
const MessageComponent = ({ message, onToggleExpand, isExpanded }) => {
  const getAgentColor = (speaker) => {
    const colors = {
      gary: 'border-l-gary bg-blue-50',
      aravind: 'border-l-aravind bg-purple-50',
      tijana: 'border-l-tijana bg-orange-50',
      jerin: 'border-l-jerin bg-green-50',
      aayushi: 'border-l-aayushi bg-pink-50',
      james: 'border-l-james bg-lime-50'
    };
    return colors[speaker.toLowerCase()] || 'border-l-gray-400 bg-gray-50';
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

  const getMessageTypeStyles = (type) => {
    switch (type) {
      case 'decision':
        return 'ring-2 ring-yellow-400 bg-yellow-50';
      case 'tool':
        return 'ring-2 ring-green-400 bg-green-50';
      case 'urgent':
        return 'ring-2 ring-red-400 bg-red-50 animate-pulse-slow';
      default:
        return '';
    }
  };

  const timestamp = new Date(message.timestamp).toLocaleTimeString();
  const isLongMessage = message.content.length > 300;
  const displayContent = isLongMessage && !isExpanded 
    ? message.content.substring(0, 300) + '...' 
    : message.content;

  return (
    <div className={`p-4 rounded-lg border-l-4 ${getAgentColor(message.speaker)} ${getMessageTypeStyles(message.message_type)} transition-all duration-300 hover:shadow-md`}>
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center space-x-2">
          <span className="text-2xl">{getAgentEmoji(message.speaker)}</span>
          <div>
            <span className="font-semibold text-gray-900">{message.speaker}</span>
            <span className="ml-2 text-sm text-gray-600">{message.designation}</span>
          </div>
          {message.message_type === 'decision' && (
            <span className="px-2 py-1 text-xs font-medium bg-yellow-200 text-yellow-800 rounded-full">
              ⚖️ DECISION
            </span>
          )}
          {message.message_type === 'tool' && (
            <span className="px-2 py-1 text-xs font-medium bg-green-200 text-green-800 rounded-full">
              🔧 ANALYSIS
            </span>
          )}
        </div>
        <span className="text-xs text-gray-500">{timestamp}</span>
      </div>
      
      <div className="text-gray-800 leading-relaxed">
        <div className="whitespace-pre-wrap">{displayContent}</div>
        {isLongMessage && (
          <button
            onClick={() => onToggleExpand(message.id)}
            className="mt-2 text-sm text-blue-600 hover:text-blue-800 flex items-center space-x-1"
          >
            {isExpanded ? <EyeOff size={16} /> : <Eye size={16} />}
            <span>{isExpanded ? 'Show less' : 'Show more'}</span>
          </button>
        )}
      </div>
    </div>
  );
};

// Component for team members sidebar
const TeamMember = ({ agent, isActive, onClick }) => {
  const getAgentColor = (key) => {
    const colors = {
      gary: 'bg-gary',
      aravind: 'bg-aravind',
      tijana: 'bg-tijana',
      jerin: 'bg-jerin',
      aayushi: 'bg-aayushi',
      james: 'bg-james'
    };
    return colors[key] || 'bg-gray-500';
  };

  const handleClick = () => {
    console.log('TeamMember clicked:', agent); // Debug log
    onClick(agent);
  };

  return (
    <div
      onClick={handleClick}
      className={`p-3 rounded-lg cursor-pointer transition-all duration-300 ${
        isActive 
          ? 'bg-white shadow-lg ring-2 ring-blue-500 transform scale-105' 
          : 'bg-white/70 hover:bg-white hover:shadow-md'
      }`}
    >
      <div className="text-center">
        <div className="w-12 h-12 rounded-full overflow-hidden mx-auto mb-2 border-2 border-white shadow-lg">
          <img 
            src={`/images/${agent.key}.jpg`}
            alt={agent.name}
            className="w-full h-full object-cover"
            onError={(e) => {
              // Fallback to colored background with initial if image fails
              e.target.style.display = 'none';
              e.target.nextElementSibling.style.display = 'flex';
            }}
          />
          <div 
            className={`w-full h-full ${getAgentColor(agent.key)} flex items-center justify-center text-white text-xl font-bold`}
            style={{ display: 'none' }}
          >
            {agent.name[0]}
          </div>
        </div>
        <div className="text-sm font-semibold text-gray-900">{agent.name}</div>
        <div className="text-xs text-gray-600">{agent.role}</div>
        {isActive && (
          <div className="mt-1 flex items-center justify-center">
            <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
            <span className="ml-1 text-xs text-green-600">Speaking</span>
          </div>
        )}
      </div>
    </div>
  );
};

// Agent Profile Modal Component
const AgentModal = ({ agent, isOpen, onClose }) => {
  if (!isOpen || !agent) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-2xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        {/* Modal Header */}
        <div className="p-6 border-b border-gray-200">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <div className="w-20 h-20 rounded-full overflow-hidden border-4 border-gray-200">
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
                  className={`w-full h-full bg-${agent.key} flex items-center justify-center text-white text-2xl font-bold`}
                  style={{ display: 'none' }}
                >
                  {agent.name[0]}
                </div>
              </div>
              <div>
                <h2 className="text-2xl font-bold text-gray-900">{agent.full_name || agent.name}</h2>
                <p className="text-lg text-gray-600">{agent.role}</p>
                <span className="inline-block px-3 py-1 bg-green-100 text-green-800 rounded-full text-sm font-medium mt-2">
                  Active
                </span>
              </div>
            </div>
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-gray-600 text-2xl font-bold"
            >
              ×
            </button>
          </div>
        </div>

        {/* Agent Stats */}
        <div className="p-6 border-b border-gray-200">
          <h3 className="text-lg font-semibold mb-4">Agent Information</h3>
          <div className="grid grid-cols-2 gap-4">
            <div className="bg-gray-50 p-4 rounded-lg text-center">
              <div className="text-2xl font-bold text-gray-900">{agent.age || 'N/A'}</div>
              <div className="text-sm text-gray-600">Age</div>
            </div>
            <div className="bg-gray-50 p-4 rounded-lg text-center">
              <div className="text-2xl font-bold text-gray-900">0.7</div>
              <div className="text-sm text-gray-600">Temperature</div>
            </div>
          </div>
        </div>

        {/* System Message */}
        <div className="p-6">
          <h3 className="text-lg font-semibold mb-4">System Instructions</h3>
          <div className="bg-gray-50 p-4 rounded-lg max-h-64 overflow-y-auto">
            <pre className="text-sm text-gray-800 whitespace-pre-wrap font-mono leading-relaxed">
              {agent.system_message || 'Loading system message...'}
            </pre>
          </div>
        </div>
      </div>

      {/* Agent Profile Modal */}
      <AgentModal 
        agent={selectedAgent}
        isOpen={!!selectedAgent}
        onClose={closeAgentModal}
      />
      
      {/* Debug info */}
      {selectedAgent && (
        <div style={{
          position: 'fixed',
          top: '10px',
          left: '10px',
          background: 'yellow',
          padding: '10px',
          zIndex: 1000000,
          border: '2px solid red'
        }}>
          DEBUG: selectedAgent exists! Key: {selectedAgent.key}
        </div>
      )}
    </div>
  );
};
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
        // Always connect to Python server on port 8000
        const response = await fetch('http://localhost:8000/api/agents');
        const profiles = await response.json();
        setAgentProfiles(profiles);
      } catch (error) {
        console.error('Failed to load agent profiles:', error);
      }
    };
    
    loadAgentProfiles();
  }, []);

  // Debug effect to track selectedAgent changes
  useEffect(() => {
    console.log('selectedAgent state changed:', selectedAgent);
    console.log('Modal should be open:', !!selectedAgent);
  }, [selectedAgent]);

  // WebSocket connection
  useEffect(() => {
    const connectWebSocket = () => {
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      // Always connect to Python server on port 8000
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
        // Reconnect after 3 seconds
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

  // Handle WebSocket messages
  const handleWebSocketMessage = (data) => {
    switch (data.type) {
      case 'conversation_history':
        setMessages(data.messages.map(msg => ({ ...msg, id: Math.random().toString(36) })));
        break;
      case 'new_message':
        const newMessage = { ...data.message, id: Math.random().toString(36) };
        setMessages(prev => [...prev, newMessage]);
        
        // Set active speaker
        setActiveSpeaker(newMessage.speaker.toLowerCase());
        clearTimeout(speakerTimeoutRef.current);
        speakerTimeoutRef.current = setTimeout(() => {
          setActiveSpeaker(null);
        }, 5000);
        
        // Update progress based on message
        updateProgressFromMessage(newMessage);
        break;
      case 'status_update':
        setStatus({ type: data.status, message: data.details || data.status });
        setSessionRunning(['running', 'initializing'].includes(data.status));
        
        if (data.status === 'running') {
          setCurrentStep(0);
        } else if (data.status === 'completed') {
          setCurrentStep(5);
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
      setStepTimes(prev => ({ ...prev, collect: 15 })); // Mock timing
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
    
    ws.current.send(JSON.stringify({
      type: 'start_session',
      articles_count: articlesCount
    }));
    
    setMessages([]);
    setCurrentStep(-1);
    setStepTimes({});
  };

  // Stop session
  const stopSession = () => {
    if (!isConnected) return;
    
    ws.current.send(JSON.stringify({
      type: 'stop_session'
    }));
  };

  // Handle agent click
  const handleAgentClick = async (agent) => {
    console.log('Agent clicked:', agent); // Debug log
    
    // SIMPLE TEST - just show an alert first
    alert(`Agent clicked: ${agent.name}`);
    
    try {
      // Get detailed agent info
      const response = await fetch(`http://localhost:8000/api/agent/${agent.key}`);
      console.log('API response status:', response.status); // Debug log
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const agentDetails = await response.json();
      console.log('Agent details loaded:', agentDetails); // Debug log
      
      const fullAgent = {
        ...agent,
        ...agentDetails
      };
      
      console.log('About to set selectedAgent to:', fullAgent); // Debug log
      
      // Try setting the state
      setSelectedAgent(fullAgent);
      
      console.log('setSelectedAgent called'); // Debug log
      
      // Also show alert with the data
      alert(`Setting modal for: ${fullAgent.full_name || fullAgent.name}`);
      
    } catch (error) {
      console.error('Failed to load agent details:', error);
      alert(`Error: ${error.message}`);
    }
  };

  // Close agent modal
  const closeAgentModal = () => {
    setSelectedAgent(null);
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

  // Debug effect to track selectedAgent changes
  useEffect(() => {
    console.log('selectedAgent state changed:', selectedAgent);
    console.log('Modal should be open:', !!selectedAgent);
  }, [selectedAgent]);

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
        } else if (data.status === 'completed') {
          setCurrentStep(5);
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
    
    ws.current.send(JSON.stringify({
      type: 'start_session',
      articles_count: articlesCount
    }));
    
    setMessages([]);
    setCurrentStep(-1);
    setStepTimes({});
  };

  // Stop session
  const stopSession = () => {
    if (!isConnected) return;
    
    ws.current.send(JSON.stringify({
      type: 'stop_session'
    }));
  };

  // Handle agent click
  const handleAgentClick = async (agent) => {
    console.log('Agent clicked:', agent);
    
    try {
      const response = await fetch(`http://localhost:8000/api/agent/${agent.key}`);
      console.log('API response status:', response.status);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const agentDetails = await response.json();
      console.log('Agent details loaded:', agentDetails);
      
      const fullAgent = {
        ...agent,
        ...agentDetails
      };
      
      console.log('About to set selectedAgent to:', fullAgent);
      setSelectedAgent(fullAgent);
      console.log('setSelectedAgent called');
      
    } catch (error) {
      console.error('Failed to load agent details:', error);
    }
  };

  // Close agent modal
  const closeAgentModal = () => {
    setSelectedAgent(null);
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
        <div className="fixed top-4 right-4 z-50 bg-red-500 text-white px-3 py-1 rounded-full text-sm font-medium animate-pulse">
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
            
            {/* Debug button to test modal */}
            <button
              onClick={() => {
                console.log('Test button clicked');
                alert('Test button clicked - about to set selectedAgent');
                setSelectedAgent({
                  key: 'test',
                  name: 'Test Agent',
                  role: 'Test Role',
                  system_message: 'This is a test modal to check if modals work.',
                  age: 30
                });
                console.log('Test selectedAgent set');
              }}
              className="w-full bg-purple-500 hover:bg-purple-600 text-white font-medium py-2 px-4 rounded-lg transition-colors duration-200 text-sm"
            >
              🔧 Test Modal
            </button>
          </div>

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
                <MessageComponent
                  key={message.id}
                  message={message}
                  onToggleExpand={toggleMessageExpansion}
                  isExpanded={expandedMessages.has(message.id)}
                />
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

export default App;