import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import AdminPage from './AdminPage';
import './App.css';

// Style constants
const styles = {
  container: {
    minHeight: '100vh',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    background: 'linear-gradient(to bottom right, #eff6ff, #e0e7ff)',
  },
  loginCard: {
    backgroundColor: 'white',
    padding: '32px',
    borderRadius: '8px',
    boxShadow: '0 20px 25px -5px rgba(0, 0, 0, 0.1)',
    width: '384px',
  },
  title: {
    fontSize: '30px',
    fontWeight: 'bold',
    textAlign: 'center' as const,
    marginBottom: '32px',
    color: '#1f2937',
  },
  tabContainer: {
    display: 'flex',
    justifyContent: 'center',
    marginBottom: '24px',
  },
  tabButton: {
    padding: '8px 16px',
    cursor: 'pointer',
    transition: 'all 0.2s',
    border: 'none',
    fontSize: '14px',
    fontWeight: '500',
  },
  tabActive: {
    backgroundColor: '#3b82f6',
    color: 'white',
  },
  tabInactive: {
    backgroundColor: '#e5e7eb',
    color: '#374151',
  },
  input: {
    width: '100%',
    padding: '8px 16px',
    border: '1px solid #d1d5db',
    borderRadius: '8px',
    marginBottom: '16px',
    fontSize: '14px',
    outline: 'none',
  },
  button: {
    width: '100%',
    backgroundColor: '#3b82f6',
    color: 'white',
    padding: '8px 0',
    borderRadius: '8px',
    border: 'none',
    fontSize: '14px',
    fontWeight: '500',
    cursor: 'pointer',
    transition: 'background-color 0.2s',
  },
  errorBox: {
    backgroundColor: '#fee2e2',
    border: '1px solid #f87171',
    color: '#b91c1c',
    padding: '12px 16px',
    borderRadius: '6px',
    marginBottom: '16px',
  },
  mainContainer: {
    display: 'flex',
    height: '100vh',
    backgroundColor: '#f3f4f6',
  },
  sidebar: {
    width: '256px',
    backgroundColor: '#111827',
    color: 'white',
    display: 'flex',
    flexDirection: 'column' as const,
  },
  sidebarHeader: {
    padding: '16px',
    borderBottom: '1px solid #374151',
  },
  newChatButton: {
    width: '100%',
    backgroundColor: '#2563eb',
    color: 'white',
    padding: '8px 16px',
    borderRadius: '8px',
    border: 'none',
    fontSize: '14px',
    fontWeight: '500',
    cursor: 'pointer',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    gap: '8px',
    transition: 'background-color 0.2s',
  },
  conversationsList: {
    flex: 1,
    overflowY: 'auto' as const,
  },
  conversationItem: {
    padding: '12px',
    cursor: 'pointer',
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    transition: 'background-color 0.2s',
  },
  sidebarFooter: {
    padding: '16px',
    borderTop: '1px solid #374151',
  },
  chatArea: {
    flex: 1,
    display: 'flex',
    flexDirection: 'column' as const,
  },
  chatHeader: {
    backgroundColor: 'white',
    boxShadow: '0 1px 2px rgba(0, 0, 0, 0.05)',
    padding: '16px 24px',
    borderBottom: '1px solid #e5e7eb',
  },
  messagesArea: {
    flex: 1,
    overflowY: 'auto' as const,
    padding: '24px',
  },
  messageRow: {
    marginBottom: '16px',
    display: 'flex',
  },
  userMessage: {
    maxWidth: '768px',
    padding: '12px 16px',
    borderRadius: '8px',
    backgroundColor: '#3b82f6',
    color: 'white',
  },
  assistantMessage: {
    maxWidth: '768px',
    padding: '12px 16px',
    borderRadius: '8px',
    backgroundColor: 'white',
    border: '1px solid #d1d5db',
  },
  inputArea: {
    backgroundColor: 'white',
    borderTop: '1px solid #e5e7eb',
    padding: '16px',
  },
  inputWrapper: {
    display: 'flex',
    alignItems: 'center',
    gap: '16px',
  },
  messageInput: {
    flex: 1,
    padding: '8px 16px',
    border: '1px solid #d1d5db',
    borderRadius: '8px',
    fontSize: '14px',
    outline: 'none',
  },
  sendButton: {
    backgroundColor: '#3b82f6',
    color: 'white',
    padding: '8px 24px',
    borderRadius: '8px',
    border: 'none',
    fontSize: '14px',
    fontWeight: '500',
    cursor: 'pointer',
    transition: 'background-color 0.2s',
  },
  badge: {
    marginLeft: '8px',
    padding: '2px 6px',
    borderRadius: '4px',
    fontSize: '12px',
    backgroundColor: '#9333ea',
    color: 'white',
  },
};

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
  is_admin?: boolean;
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
  const [showAdmin, setShowAdmin] = useState(false);

  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [currentConv, setCurrentConv] = useState<Conversation | null>(null);
  const [message, setMessage] = useState('');
  const [sending, setSending] = useState(false);
  const [editingConvId, setEditingConvId] = useState<number | null>(null);
  const [editingTitle, setEditingTitle] = useState('');
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
      console.log('📡 Sending request to:', `/api/v1/auth/${endpoint}`);
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
      console.error('❌ Auth error:', err);
      console.error('❌ Error details:', {
        status: err.response?.status,
        data: err.response?.data,
        message: err.message
      });
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
    setShowAdmin(false);
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

  const updateConversationTitle = async (convId: number) => {
    if (!editingTitle.trim()) {
      setEditingConvId(null);
      return;
    }

    try {
      console.log('✏️ Updating conversation title:', convId);
      await axios.put(`/api/v1/conversations/${convId}`, {
        title: editingTitle
      });
      
      setConversations(conversations.map(c => 
        c.id === convId ? { ...c, title: editingTitle } : c
      ));
      
      if (currentConv?.id === convId) {
        setCurrentConv({ ...currentConv, title: editingTitle });
      }
      
      setEditingConvId(null);
      console.log('✅ Updated conversation title');
    } catch (err) {
      console.error('❌ Failed to update conversation title:', err);
      alert('Failed to update conversation title');
    }
  };

  const startEditingTitle = (convId: number, currentTitle: string, e: React.MouseEvent) => {
    e.stopPropagation();
    setEditingConvId(convId);
    setEditingTitle(currentTitle);
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
          use_vllm: true,  // Always use vLLM
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
      <div style={styles.container}>
        <div style={styles.loginCard}>
          <h1 style={styles.title}>
            Medical Gait RAG
          </h1>
          
          <div style={styles.tabContainer}>
            <button
              style={{
                ...styles.tabButton,
                ...(isLogin ? styles.tabActive : styles.tabInactive),
                borderTopLeftRadius: '8px',
                borderBottomLeftRadius: '8px',
              }}
              onClick={() => {
                setIsLogin(true);
                setError('');
              }}
            >
              Login
            </button>
            <button
              style={{
                ...styles.tabButton,
                ...(!isLogin ? styles.tabActive : styles.tabInactive),
                borderTopRightRadius: '8px',
                borderBottomRightRadius: '8px',
              }}
              onClick={() => {
                setIsLogin(false);
                setError('');
              }}
            >
              Register
            </button>
          </div>

          {error && (
            <div style={styles.errorBox}>
              {error}
            </div>
          )}

          <form onSubmit={handleAuth}>
            <input
              type="text"
              placeholder="Username"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              style={styles.input}
              required
              autoComplete="username"
            />
            <input
              type="password"
              placeholder="Password (min 8 characters)"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              style={styles.input}
              required
              minLength={8}
              autoComplete={isLogin ? "current-password" : "new-password"}
            />
            <button
              type="submit"
              disabled={loading}
              style={{
                ...styles.button,
                backgroundColor: loading ? '#9ca3af' : '#3b82f6',
                cursor: loading ? 'not-allowed' : 'pointer',
              }}
              onMouseOver={(e) => !loading && (e.currentTarget.style.backgroundColor = '#2563eb')}
              onMouseOut={(e) => !loading && (e.currentTarget.style.backgroundColor = '#3b82f6')}
            >
              {loading ? 'Processing...' : (isLogin ? 'Login' : 'Register')}
            </button>
          </form>

          <div style={{ marginTop: '24px', textAlign: 'center', fontSize: '14px', color: '#4b5563' }}>
            <p>Test Account:</p>
            <p>Username: <strong>demouser</strong></p>
            <p>Password: <strong>demo12345</strong></p>
          </div>
        </div>
      </div>
    );
  }

  // Admin page
  if (showAdmin) {
    return <AdminPage token={token} onLogout={handleLogout} />;
  }

  // Main app
  return (
    <div style={styles.mainContainer}>
      {/* Sidebar */}
      <div style={styles.sidebar}>
        <div style={styles.sidebarHeader}>
          <button
            onClick={createConversation}
            style={styles.newChatButton}
            onMouseOver={(e) => e.currentTarget.style.backgroundColor = '#1d4ed8'}
            onMouseOut={(e) => e.currentTarget.style.backgroundColor = '#2563eb'}
          >
            <span style={{ fontSize: '18px' }}>+</span> New Chat
          </button>
        </div>

        <div style={styles.conversationsList}>
          {conversations.map(conv => (
            <div
              key={conv.id}
              style={{
                ...styles.conversationItem,
                backgroundColor: editingConvId === conv.id 
                  ? '#1e3a8a'
                  : currentConv?.id === conv.id 
                  ? '#1f2937' 
                  : 'transparent',
                borderLeft: editingConvId === conv.id ? '4px solid #3b82f6' : 'none',
              }}
              onClick={() => editingConvId !== conv.id && selectConversation(conv)}
              onMouseOver={(e) => editingConvId !== conv.id && currentConv?.id !== conv.id && (e.currentTarget.style.backgroundColor = '#1f2937')}
              onMouseOut={(e) => editingConvId !== conv.id && currentConv?.id !== conv.id && (e.currentTarget.style.backgroundColor = 'transparent')}
            >
              <div style={{ flex: 1, minWidth: 0 }}>
                {editingConvId === conv.id ? (
                  <input
                    type="text"
                    value={editingTitle}
                    onChange={(e) => setEditingTitle(e.target.value)}
                    onBlur={() => updateConversationTitle(conv.id)}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter') {
                        updateConversationTitle(conv.id);
                      } else if (e.key === 'Escape') {
                        setEditingConvId(null);
                      }
                    }}
                    onClick={(e) => e.stopPropagation()}
                    style={{
                      width: '100%',
                      backgroundColor: 'white',
                      color: '#111827',
                      fontSize: '14px',
                      padding: '4px 8px',
                      borderRadius: '4px',
                      border: '2px solid #3b82f6',
                      outline: 'none',
                      boxShadow: '0 10px 15px -3px rgba(0, 0, 0, 0.1)',
                    }}
                    autoFocus
                  />
                ) : (
                  <div 
                    style={{
                      fontSize: '14px',
                      overflow: 'hidden',
                      textOverflow: 'ellipsis',
                      whiteSpace: 'nowrap',
                      cursor: 'text',
                      transition: 'color 0.2s',
                    }}
                    onDoubleClick={(e) => startEditingTitle(conv.id, conv.title, e)}
                    onMouseOver={(e) => e.currentTarget.style.color = '#60a5fa'}
                    onMouseOut={(e) => e.currentTarget.style.color = 'white'}
                    title="Double-click to edit"
                  >
                    {conv.title}
                  </div>
                )}
                <div style={{ fontSize: '12px', color: '#9ca3af', marginTop: '4px' }}>
                  {new Date(conv.updated_at).toLocaleDateString()}
                </div>
              </div>
              <div style={{ display: 'flex', alignItems: 'center' }}>
                {editingConvId !== conv.id && (
                  <button
                    onClick={(e) => startEditingTitle(conv.id, conv.title, e)}
                    style={{
                      marginLeft: '8px',
                      padding: '4px',
                      color: '#9ca3af',
                      backgroundColor: 'transparent',
                      border: 'none',
                      borderRadius: '4px',
                      cursor: 'pointer',
                      transition: 'all 0.2s',
                    }}
                    onMouseOver={(e) => {
                      e.currentTarget.style.color = '#60a5fa';
                      e.currentTarget.style.backgroundColor = '#374151';
                    }}
                    onMouseOut={(e) => {
                      e.currentTarget.style.color = '#9ca3af';
                      e.currentTarget.style.backgroundColor = 'transparent';
                    }}
                    title="Edit title"
                  >
                    <svg width="16" height="16" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                    </svg>
                  </button>
                )}
                <button
                  onClick={(e) => deleteConversation(conv.id, e)}
                  style={{
                    marginLeft: '4px',
                    padding: '4px',
                    color: '#9ca3af',
                    backgroundColor: 'transparent',
                    border: 'none',
                    borderRadius: '4px',
                    fontSize: '20px',
                    lineHeight: '1',
                    cursor: 'pointer',
                    transition: 'all 0.2s',
                  }}
                  onMouseOver={(e) => {
                    e.currentTarget.style.color = '#f87171';
                    e.currentTarget.style.backgroundColor = '#374151';
                  }}
                  onMouseOut={(e) => {
                    e.currentTarget.style.color = '#9ca3af';
                    e.currentTarget.style.backgroundColor = 'transparent';
                  }}
                  title="Delete conversation"
                >
                  ×
                </button>
              </div>
            </div>
          ))}
        </div>

        <div style={styles.sidebarFooter}>
          <div style={{ fontSize: '14px', color: '#9ca3af', marginBottom: '8px' }}>
            Logged in as: {user?.username}
            {user?.is_admin && (
              <span style={styles.badge}>
                Admin
              </span>
            )}
          </div>
          {user?.is_admin && (
            <button
              onClick={() => setShowAdmin(true)}
              style={{
                width: '100%',
                backgroundColor: '#9333ea',
                color: 'white',
                padding: '8px 16px',
                borderRadius: '8px',
                marginBottom: '8px',
                border: 'none',
                fontSize: '14px',
                fontWeight: '500',
                cursor: 'pointer',
                transition: 'background-color 0.2s',
              }}
              onMouseOver={(e) => e.currentTarget.style.backgroundColor = '#7e22ce'}
              onMouseOut={(e) => e.currentTarget.style.backgroundColor = '#9333ea'}
            >
              Admin Panel
            </button>
          )}
          <button
            onClick={handleLogout}
            style={{
              width: '100%',
              backgroundColor: '#ef4444',
              color: 'white',
              padding: '8px 16px',
              borderRadius: '8px',
              border: 'none',
              fontSize: '14px',
              fontWeight: '500',
              cursor: 'pointer',
              transition: 'background-color 0.2s',
            }}
            onMouseOver={(e) => e.currentTarget.style.backgroundColor = '#dc2626'}
            onMouseOut={(e) => e.currentTarget.style.backgroundColor = '#ef4444'}
          >
            Logout
          </button>
        </div>
      </div>

      {/* Main Chat Area */}
      <div style={styles.chatArea}>
        {/* Header */}
        <div style={styles.chatHeader}>
          <h2 style={{ fontSize: '20px', fontWeight: '600', color: '#1f2937' }}>
            {currentConv ? currentConv.title : 'Medical Gait RAG System'}
          </h2>
        </div>

        {/* Messages */}
        {currentConv ? (
          <>
            <div style={styles.messagesArea}>
              {currentConv.messages?.map(msg => (
                <div
                  key={msg.id}
                  style={{
                    ...styles.messageRow,
                    justifyContent: msg.role === 'user' ? 'flex-end' : 'flex-start'
                  }}
                >
                  <div
                    style={{
                      ...(msg.role === 'user' ? styles.userMessage : styles.assistantMessage)
                    }}
                  >
                    <div style={{ whiteSpace: 'pre-wrap' }}>{msg.content}</div>
                    {msg.sources && typeof msg.sources === 'string' && msg.sources !== 'null' && (
                      <div style={{ marginTop: '12px', paddingTop: '12px', borderTop: '1px solid #e5e7eb' }}>
                        <details style={{ cursor: 'pointer' }}>
                          <summary style={{ fontSize: '12px', color: '#4b5563', fontWeight: '500' }}>
                            📚 참조된 문서 보기
                          </summary>
                          <div style={{ marginTop: '8px' }}>
                            {(() => {
                              try {
                                const sources = JSON.parse(msg.sources);
                                return sources.map((source: any, idx: number) => (
                                  <div key={idx} style={{
                                    backgroundColor: '#f9fafb',
                                    padding: '8px',
                                    borderRadius: '4px',
                                    fontSize: '12px',
                                    marginBottom: '8px'
                                  }}>
                                    <div style={{ fontWeight: '500', color: '#374151' }}>
                                      문서 {idx + 1}: {source.document_id || 'Unknown'}
                                    </div>
                                    <div style={{ color: '#4b5563' }}>
                                      페이지: {source.page_number || 'N/A'} | 
                                      점수: {source.score?.toFixed(3) || 'N/A'}
                                    </div>
                                    <div style={{ marginTop: '4px', color: '#6b7280' }}>
                                      {source.content?.substring(0, 150)}...
                                    </div>
                                  </div>
                                ));
                              } catch {
                                return <div style={{ fontSize: '12px', color: '#6b7280' }}>문서 정보를 표시할 수 없습니다</div>;
                              }
                            })()}
                          </div>
                        </details>
                      </div>
                    )}
                    <div style={{
                      fontSize: '12px',
                      marginTop: '8px',
                      color: msg.role === 'user' ? '#dbeafe' : '#9ca3af'
                    }}>
                      {new Date(msg.created_at).toLocaleTimeString()}
                    </div>
                  </div>
                </div>
              ))}
              {sending && (
                <div style={{ ...styles.messageRow, justifyContent: 'flex-start' }}>
                  <div style={{
                    maxWidth: '768px',
                    padding: '12px 16px',
                    borderRadius: '8px',
                    backgroundColor: '#f3f4f6',
                    border: '1px solid #d1d5db'
                  }}>
                    <div style={{ display: 'flex', alignItems: 'center' }}>
                      <div style={{ display: 'flex', gap: '4px' }}>
                        <div style={{
                          width: '8px',
                          height: '8px',
                          backgroundColor: '#9ca3af',
                          borderRadius: '50%',
                          animation: 'pulse 1.5s infinite'
                        }}></div>
                        <div style={{
                          width: '8px',
                          height: '8px',
                          backgroundColor: '#9ca3af',
                          borderRadius: '50%',
                          animation: 'pulse 1.5s infinite 0.2s'
                        }}></div>
                        <div style={{
                          width: '8px',
                          height: '8px',
                          backgroundColor: '#9ca3af',
                          borderRadius: '50%',
                          animation: 'pulse 1.5s infinite 0.4s'
                        }}></div>
                      </div>
                      <span style={{ marginLeft: '8px', color: '#6b7280' }}>
                        Generating AI answer...
                      </span>
                    </div>
                  </div>
                </div>
              )}
              <div ref={messagesEndRef} />
            </div>

            {/* Input */}
            <div style={styles.inputArea}>
              <form onSubmit={sendMessage} style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                {/* RAG Mode Indicator */}
                {message.startsWith('@') && (
                  <div style={{
                    display: 'flex',
                    alignItems: 'center',
                    fontSize: '12px',
                    color: '#059669',
                    backgroundColor: '#ecfdf5',
                    padding: '4px 12px',
                    borderRadius: '4px'
                  }}>
                    <span style={{ marginRight: '8px' }}>🔍</span>
                    <span style={{ fontWeight: '500' }}>RAG 모드 활성화</span>
                    <span style={{ marginLeft: '8px', color: '#4b5563' }}>- 문서 검색 후 답변 생성</span>
                  </div>
                )}
                {!message.startsWith('@') && message.length > 0 && (
                  <div style={{
                    display: 'flex',
                    alignItems: 'center',
                    fontSize: '12px',
                    color: '#2563eb',
                    backgroundColor: '#eff6ff',
                    padding: '4px 12px',
                    borderRadius: '4px'
                  }}>
                    <span style={{ marginRight: '8px' }}>💬</span>
                    <span style={{ fontWeight: '500' }}>일반 대화 모드</span>
                    <span style={{ marginLeft: '8px', color: '#4b5563' }}>- AI와 직접 대화</span>
                  </div>
                )}
                <div style={styles.inputWrapper}>
                  <input
                    type="text"
                    value={message}
                    onChange={(e) => setMessage(e.target.value)}
                    placeholder="일반 대화 또는 @로 시작하여 문서 검색 (예: @보행 분석)"
                    style={{
                      ...styles.messageInput,
                      opacity: sending ? 0.5 : 1
                    }}
                    disabled={sending}
                    onFocus={(e) => e.currentTarget.style.borderColor = '#3b82f6'}
                    onBlur={(e) => e.currentTarget.style.borderColor = '#d1d5db'}
                  />
                  <button
                    type="submit"
                    disabled={sending || !message.trim()}
                    style={{
                      ...styles.sendButton,
                      backgroundColor: sending || !message.trim() ? '#9ca3af' : '#3b82f6',
                      cursor: sending || !message.trim() ? 'not-allowed' : 'pointer'
                    }}
                    onMouseOver={(e) => !sending && message.trim() && (e.currentTarget.style.backgroundColor = '#2563eb')}
                    onMouseOut={(e) => !sending && message.trim() && (e.currentTarget.style.backgroundColor = '#3b82f6')}
                  >
                    Send
                  </button>
                </div>
              </form>
            </div>
          </>
        ) : (
          <div style={{
            flex: 1,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center'
          }}>
            <div style={{ textAlign: 'center' }}>
              <h3 style={{
                fontSize: '24px',
                color: '#4b5563',
                marginBottom: '16px'
              }}>Welcome to Medical Gait RAG</h3>
              <p style={{
                color: '#6b7280',
                marginBottom: '24px'
              }}>
                Create a new chat or select an existing conversation to start
              </p>
              <button
                onClick={createConversation}
                style={{
                  backgroundColor: '#3b82f6',
                  color: 'white',
                  padding: '12px 24px',
                  borderRadius: '8px',
                  border: 'none',
                  fontSize: '16px',
                  fontWeight: '500',
                  cursor: 'pointer',
                  transition: 'background-color 0.2s'
                }}
                onMouseOver={(e) => e.currentTarget.style.backgroundColor = '#2563eb'}
                onMouseOut={(e) => e.currentTarget.style.backgroundColor = '#3b82f6'}
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