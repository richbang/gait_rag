import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import './App.css';

// API configuration
// Use relative URLs to work with proxy
const API_URL = '';

// Configure axios defaults
axios.defaults.baseURL = API_URL;
axios.defaults.headers.common['Content-Type'] = 'application/json';

// Add request/response interceptors for debugging
axios.interceptors.request.use(
  (config) => {
    console.log('📤 Request:', config.method?.toUpperCase(), config.url, config.data);
    return config;
  },
  (error) => {
    console.error('❌ Request Error:', error);
    return Promise.reject(error);
  }
);

axios.interceptors.response.use(
  (response) => {
    console.log('📥 Response:', response.status, response.data);
    return response;
  },
  (error) => {
    console.error('❌ Response Error:', error.response?.status, error.response?.data || error.message);
    return Promise.reject(error);
  }
);

interface User {
  id: number;
  username: string;
}

interface Message {
  id: number;
  role: 'user' | 'assistant';
  content: string;
  created_at: string;
  sources?: any[];
}

interface Conversation {
  id: number;
  title: string;
  messages?: Message[];
  updated_at: string;
}

function App() {
  const [token, setToken] = useState<string | null>(localStorage.getItem('token'));
  const [user, setUser] = useState<User | null>(null);
  const [isLogin, setIsLogin] = useState(true);
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [currentConv, setCurrentConv] = useState<Conversation | null>(null);
  const [message, setMessage] = useState('');
  const [useVllm, setUseVllm] = useState(true);
  const [sending, setSending] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [currentConv?.messages]);

  // Setup axios auth header when token changes
  useEffect(() => {
    if (token) {
      console.log('🔐 Setting auth token');
      axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
      checkAuth();
      loadConversations();
    } else {
      console.log('🔓 Removing auth token');
      delete axios.defaults.headers.common['Authorization'];
    }
  }, [token]);

  const checkAuth = async () => {
    try {
      console.log('🔍 Checking authentication...');
      const response = await axios.get('/api/v1/auth/me');
      setUser(response.data);
      console.log('✅ Auth check successful:', response.data);
    } catch (err) {
      console.error('❌ Auth check failed:', err);
      handleLogout();
    }
  };

  const handleAuth = async (e: React.FormEvent) => {
    e.preventDefault();
    console.log('🚀 Starting authentication...', { username, isLogin });
    setLoading(true);
    setError('');

    const endpoint = isLogin ? 'login' : 'register';
    
    try {
      const response = await axios.post(`/api/v1/auth/${endpoint}`, {
        username,
        password
      });

      const { access_token, user } = response.data;
      console.log('✅ Authentication successful:', user);
      
      localStorage.setItem('token', access_token);
      setToken(access_token);
      setUser(user);
      setUsername('');
      setPassword('');
      setError('');
    } catch (err: any) {
      const errorMsg = err.response?.data?.detail || err.message || 'Authentication failed';
      console.error('❌ Auth error:', errorMsg);
      setError(errorMsg);
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = () => {
    console.log('👋 Logging out...');
    localStorage.removeItem('token');
    setToken(null);
    setUser(null);
    setConversations([]);
    setCurrentConv(null);
  };

  const loadConversations = async () => {
    try {
      console.log('📚 Loading conversations...');
      const response = await axios.get('/api/v1/conversations');
      setConversations(response.data);
      console.log(`✅ Loaded ${response.data.length} conversations`);
      
      if (response.data.length > 0 && !currentConv) {
        selectConversation(response.data[0]);
      }
    } catch (err) {
      console.error('❌ Failed to load conversations:', err);
    }
  };

  const createConversation = async () => {
    try {
      console.log('➕ Creating new conversation...');
      const response = await axios.post('/api/v1/conversations', {
        title: `New Chat ${new Date().toLocaleString()}`
      });
      
      const newConv = { ...response.data, messages: [] };
      setCurrentConv(newConv);
      setConversations([newConv, ...conversations]);
      console.log('✅ Created conversation:', newConv.id);
    } catch (err) {
      console.error('❌ Failed to create conversation:', err);
    }
  };

  const selectConversation = async (conv: Conversation) => {
    try {
      console.log('📖 Loading conversation:', conv.id);
      const response = await axios.get(`/api/v1/conversations/${conv.id}`);
      setCurrentConv(response.data);
      console.log(`✅ Loaded ${response.data.messages?.length || 0} messages`);
    } catch (err) {
      console.error('❌ Failed to load conversation:', err);
    }
  };

  const deleteConversation = async (convId: number, e: React.MouseEvent) => {
    e.stopPropagation();
    if (!window.confirm('Delete this conversation?')) return;

    try {
      console.log('🗑️ Deleting conversation:', convId);
      await axios.delete(`/api/v1/conversations/${convId}`);
      setConversations(conversations.filter(c => c.id !== convId));
      if (currentConv?.id === convId) {
        setCurrentConv(null);
      }
      console.log('✅ Deleted conversation:', convId);
    } catch (err) {
      console.error('❌ Failed to delete conversation:', err);
    }
  };

  const sendMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!message.trim() || !currentConv || sending) return;

    const userMessage = message;
    console.log('💬 Sending message:', userMessage);
    setMessage('');
    setSending(true);

    // Optimistically add user message
    const tempUserMsg: Message = {
      id: Date.now(),
      role: 'user',
      content: userMessage,
      created_at: new Date().toISOString()
    };

    setCurrentConv({
      ...currentConv,
      messages: [...(currentConv.messages || []), tempUserMsg]
    });

    try {
      const response = await axios.post(
        `/api/v1/conversations/${currentConv.id}/messages`,
        {
          content: userMessage,
          use_vllm: useVllm,
          search_limit: 5,
          min_score: 0.3
        }
      );

      // Update with actual response
      const { user_message, assistant_message } = response.data;
      console.log('✅ Message sent, received response');
      
      setCurrentConv({
        ...currentConv,
        messages: [
          ...(currentConv.messages || []).filter(m => m.id !== tempUserMsg.id),
          user_message,
          assistant_message
        ]
      });

      // Reload conversations list to update timestamps
      loadConversations();
    } catch (err: any) {
      console.error('❌ Failed to send message:', err);
      // Remove optimistic message on error
      setCurrentConv({
        ...currentConv,
        messages: (currentConv.messages || []).filter(m => m.id !== tempUserMsg.id)
      });
      alert('Failed to send message. Please try again.');
    } finally {
      setSending(false);
    }
  };

  // Test connection on mount
  useEffect(() => {
    console.log('🔌 Testing API connection...');
    axios.get('/api/v1/health')
      .then(response => {
        console.log('✅ API is healthy:', response.data);
      })
      .catch(error => {
        console.error('❌ API connection failed:', error.message);
        console.error(`Please ensure the backend is running on ${API_URL}`);
      });
  }, []);

  // Login/Register screen
  if (!token) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br">
        <div className="bg-white p-8 rounded-lg shadow-xl w-96">
          <h1 className="text-3xl font-bold text-center mb-8 text-gray-800">
            Medical Gait RAG
          </h1>
          
          <div className="flex justify-center mb-6">
            <button
              className={`px-4 py-2 ${isLogin ? 'bg-blue-500 text-white' : 'bg-gray-200'} rounded-l-lg`}
              onClick={() => {
                setIsLogin(true);
                setError('');
              }}
            >
              Login
            </button>
            <button
              className={`px-4 py-2 ${!isLogin ? 'bg-blue-500 text-white' : 'bg-gray-200'} rounded-r-lg`}
              onClick={() => {
                setIsLogin(false);
                setError('');
              }}
            >
              Register
            </button>
          </div>

          {error && (
            <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
              {error}
            </div>
          )}

          <form onSubmit={handleAuth}>
            <input
              type="text"
              placeholder="Username"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              className="w-full px-4 py-2 border rounded-lg mb-4 focus:outline-none focus:ring-2 focus:ring-blue-500"
              required
              autoComplete="username"
            />
            <input
              type="password"
              placeholder="Password (min 8 characters)"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full px-4 py-2 border rounded-lg mb-6 focus:outline-none focus:ring-2 focus:ring-blue-500"
              required
              minLength={8}
              autoComplete={isLogin ? "current-password" : "new-password"}
            />
            <button
              type="submit"
              disabled={loading}
              className="w-full bg-blue-500 text-white py-2 rounded-lg hover:bg-blue-600 disabled:bg-gray-400"
            >
              {loading ? 'Processing...' : (isLogin ? 'Login' : 'Register')}
            </button>
          </form>

          <div className="mt-6 text-center text-sm text-gray-600">
            <p>Test Account:</p>
            <p>Username: <strong>demouser</strong></p>
            <p>Password: <strong>demo12345</strong></p>
          </div>
        </div>
      </div>
    );
  }

  // Main app
  return (
    <div className="flex h-screen bg-gray-100">
      {/* Sidebar */}
      <div className="w-64 bg-gray-900 text-white flex flex-col">
        <div className="p-4 border-b border-gray-700">
          <button
            onClick={createConversation}
            className="w-full bg-blue-600 hover:bg-blue-700 py-2 px-4 rounded-lg flex items-center justify-center"
          >
            <span className="mr-2">+</span> New Chat
          </button>
        </div>

        <div className="flex-1 overflow-y-auto">
          {conversations.map(conv => (
            <div
              key={conv.id}
              className={`p-3 hover:bg-gray-800 cursor-pointer flex justify-between items-center ${
                currentConv?.id === conv.id ? 'bg-gray-800' : ''
              }`}
              onClick={() => selectConversation(conv)}
            >
              <div className="flex-1 min-w-0">
                <div className="text-sm truncate">{conv.title}</div>
                <div className="text-xs text-gray-400">
                  {new Date(conv.updated_at).toLocaleDateString()}
                </div>
              </div>
              <button
                onClick={(e) => deleteConversation(conv.id, e)}
                className="ml-2 text-gray-400 hover:text-red-400"
                title="Delete conversation"
              >
                ×
              </button>
            </div>
          ))}
        </div>

        <div className="p-4 border-t border-gray-700">
          <div className="text-sm text-gray-400 mb-2">
            Logged in as: {user?.username}
          </div>
          <button
            onClick={handleLogout}
            className="w-full bg-red-600 hover:bg-red-700 py-2 px-4 rounded-lg"
          >
            Logout
          </button>
        </div>
      </div>

      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col">
        {/* Header */}
        <div className="bg-white shadow-sm px-6 py-4 border-b">
          <h2 className="text-xl font-semibold text-gray-800">
            {currentConv ? currentConv.title : 'Medical Gait RAG System'}
          </h2>
        </div>

        {/* Messages */}
        {currentConv ? (
          <>
            <div className="flex-1 overflow-y-auto p-6">
              {currentConv.messages?.map(msg => (
                <div
                  key={msg.id}
                  className={`mb-4 flex ${
                    msg.role === 'user' ? 'justify-end' : 'justify-start'
                  }`}
                >
                  <div
                    className={`max-w-3xl px-4 py-3 rounded-lg ${
                      msg.role === 'user'
                        ? 'bg-blue-500 text-white'
                        : 'bg-white border border-gray-300'
                    }`}
                  >
                    <div className="whitespace-pre-wrap">{msg.content}</div>
                    {msg.sources && typeof msg.sources === 'string' && msg.sources !== 'null' && (
                      <div className="mt-3 pt-3 border-t border-gray-200">
                        <details className="cursor-pointer">
                          <summary className="text-xs text-gray-600 font-medium hover:text-gray-800">
                            📚 참조된 문서 보기
                          </summary>
                          <div className="mt-2 space-y-2">
                            {(() => {
                              try {
                                const sources = JSON.parse(msg.sources);
                                return sources.map((source: any, idx: number) => (
                                  <div key={idx} className="bg-gray-50 p-2 rounded text-xs">
                                    <div className="font-medium text-gray-700">
                                      문서 {idx + 1}: {source.document_id || 'Unknown'}
                                    </div>
                                    <div className="text-gray-600">
                                      페이지: {source.page_number || 'N/A'} | 
                                      점수: {source.score?.toFixed(3) || 'N/A'}
                                    </div>
                                    <div className="mt-1 text-gray-500 line-clamp-2">
                                      {source.content?.substring(0, 150)}...
                                    </div>
                                  </div>
                                ));
                              } catch {
                                return <div className="text-xs text-gray-500">문서 정보를 표시할 수 없습니다</div>;
                              }
                            })()}
                          </div>
                        </details>
                      </div>
                    )}
                    <div className={`text-xs mt-2 ${
                      msg.role === 'user' ? 'text-blue-100' : 'text-gray-400'
                    }`}>
                      {new Date(msg.created_at).toLocaleTimeString()}
                    </div>
                  </div>
                </div>
              ))}
              {sending && (
                <div className="mb-4 flex justify-start">
                  <div className="max-w-3xl px-4 py-3 rounded-lg bg-gray-100 border border-gray-300">
                    <div className="flex items-center">
                      <div className="animate-pulse flex space-x-1">
                        <div className="w-2 h-2 bg-gray-400 rounded-full"></div>
                        <div className="w-2 h-2 bg-gray-400 rounded-full"></div>
                        <div className="w-2 h-2 bg-gray-400 rounded-full"></div>
                      </div>
                      <span className="ml-2 text-gray-500">
                        {useVllm ? 'Generating AI answer...' : 'Searching documents...'}
                      </span>
                    </div>
                  </div>
                </div>
              )}
              <div ref={messagesEndRef} />
            </div>

            {/* Input */}
            <div className="bg-white border-t p-4">
              <form onSubmit={sendMessage} className="flex flex-col space-y-2">
                {/* RAG Mode Indicator */}
                {message.startsWith('@') && (
                  <div className="flex items-center text-xs text-green-600 bg-green-50 px-3 py-1 rounded">
                    <span className="mr-2">🔍</span>
                    <span className="font-medium">RAG 모드 활성화</span>
                    <span className="ml-2 text-gray-600">- 문서 검색 후 답변 생성</span>
                  </div>
                )}
                {!message.startsWith('@') && message.length > 0 && (
                  <div className="flex items-center text-xs text-blue-600 bg-blue-50 px-3 py-1 rounded">
                    <span className="mr-2">💬</span>
                    <span className="font-medium">일반 대화 모드</span>
                    <span className="ml-2 text-gray-600">- AI와 직접 대화</span>
                  </div>
                )}
                <div className="flex items-center space-x-4">
                  <input
                    type="text"
                    value={message}
                    onChange={(e) => setMessage(e.target.value)}
                    placeholder="일반 대화 또는 @로 시작하여 문서 검색 (예: @보행 분석)"
                    className="flex-1 px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                    disabled={sending}
                  />
                  <label className="flex items-center cursor-pointer">
                    <input
                      type="checkbox"
                      checked={useVllm}
                      onChange={(e) => setUseVllm(e.target.checked)}
                      className="mr-2"
                    />
                    <span className="text-sm text-gray-600">AI Answer</span>
                  </label>
                  <button
                    type="submit"
                    disabled={sending || !message.trim()}
                    className="bg-blue-500 text-white px-6 py-2 rounded-lg hover:bg-blue-600 disabled:bg-gray-400"
                  >
                    Send
                  </button>
                </div>
              </form>
            </div>
          </>
        ) : (
          <div className="flex-1 flex items-center justify-center">
            <div className="text-center">
              <h3 className="text-2xl text-gray-600 mb-4">Welcome to Medical Gait RAG</h3>
              <p className="text-gray-500 mb-6">
                Create a new chat or select an existing conversation to start
              </p>
              <button
                onClick={createConversation}
                className="bg-blue-500 text-white px-6 py-3 rounded-lg hover:bg-blue-600"
              >
                Start New Chat
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default App;