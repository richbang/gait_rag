import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';

interface User {
  id: number;
  username: string;
  full_name: string | null;
  department: string | null;
  is_active: boolean;
  is_admin: boolean;
  created_at: string;
}

interface RAGStats {
  total_chunks: number;
  total_documents: number;
  text_chunks: number;
  table_chunks: number;
  chunks_with_gait_params: number;
  documents: string[];
}

interface RAGDocument {
  document_id: string;
  file_name: string;
  chunks: number;
  indexed_at: string;
}

interface IndexingProgress {
  status: 'idle' | 'indexing' | 'completed' | 'error';
  current_file: string | null;
  processed_files: string[];
  failed_files: string[];
  total_files: number;
  completed_files: number;
  chunks_created: number;
  start_time: string | null;
  messages: Array<{ time: string; text: string }>;
}

interface AdminPageProps {
  token: string;
  onLogout: () => void;
}

// Style constants
const styles = {
  container: {
    minHeight: '100vh',
    backgroundColor: '#f3f4f6',
  },
  header: {
    backgroundColor: 'white',
    boxShadow: '0 1px 3px rgba(0, 0, 0, 0.1)',
  },
  headerContent: {
    maxWidth: '1280px',
    margin: '0 auto',
    padding: '24px',
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  title: {
    fontSize: '30px',
    fontWeight: 'bold',
    color: '#111827',
    margin: 0,
  },
  mainContent: {
    maxWidth: '1280px',
    margin: '0 auto',
    padding: '24px',
  },
  statsGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))',
    gap: '16px',
    marginBottom: '24px',
  },
  statCard: {
    backgroundColor: 'white',
    borderRadius: '8px',
    padding: '24px',
    boxShadow: '0 1px 3px rgba(0, 0, 0, 0.1)',
  },
  statLabel: {
    fontSize: '14px',
    fontWeight: '500',
    color: '#6b7280',
    marginBottom: '8px',
  },
  statValue: {
    fontSize: '30px',
    fontWeight: 'bold',
    color: '#111827',
  },
  filterSection: {
    backgroundColor: 'white',
    borderRadius: '8px',
    padding: '16px',
    boxShadow: '0 1px 3px rgba(0, 0, 0, 0.1)',
    marginBottom: '24px',
  },
  filterGrid: {
    display: 'grid',
    gridTemplateColumns: '2fr 1fr 1fr',
    gap: '16px',
  },
  searchInput: {
    width: '100%',
    padding: '8px 12px',
    border: '1px solid #d1d5db',
    borderRadius: '6px',
    fontSize: '14px',
    outline: 'none',
  },
  select: {
    width: '100%',
    padding: '8px 12px',
    border: '1px solid #d1d5db',
    borderRadius: '6px',
    fontSize: '14px',
    backgroundColor: 'white',
    cursor: 'pointer',
    outline: 'none',
  },
  button: {
    padding: '8px 16px',
    borderRadius: '6px',
    fontSize: '14px',
    fontWeight: '500',
    cursor: 'pointer',
    transition: 'all 0.2s',
    border: 'none',
    display: 'inline-flex',
    alignItems: 'center',
    gap: '8px',
  },
  primaryButton: {
    backgroundColor: '#3b82f6',
    color: 'white',
  },
  dangerButton: {
    backgroundColor: '#ef4444',
    color: 'white',
  },
  successButton: {
    backgroundColor: '#10b981',
    color: 'white',
  },
  tableContainer: {
    backgroundColor: 'white',
    borderRadius: '8px',
    boxShadow: '0 1px 3px rgba(0, 0, 0, 0.1)',
    overflow: 'hidden',
  },
  table: {
    width: '100%',
    borderCollapse: 'collapse' as const,
  },
  tableHeader: {
    backgroundColor: '#f9fafb',
    borderBottom: '1px solid #e5e7eb',
  },
  tableHeaderCell: {
    padding: '12px 16px',
    textAlign: 'left' as const,
    fontSize: '12px',
    fontWeight: '600',
    color: '#6b7280',
    textTransform: 'uppercase' as const,
    letterSpacing: '0.05em',
  },
  tableRow: {
    borderBottom: '1px solid #e5e7eb',
  },
  tableCell: {
    padding: '12px 16px',
    fontSize: '14px',
    color: '#111827',
  },
  badge: {
    display: 'inline-block',
    padding: '4px 8px',
    borderRadius: '9999px',
    fontSize: '12px',
    fontWeight: '600',
  },
  input: {
    padding: '4px 8px',
    border: '1px solid #d1d5db',
    borderRadius: '4px',
    fontSize: '14px',
    outline: 'none',
  },
  formGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(2, 1fr)',
    gap: '16px',
  },
  formGroup: {
    marginBottom: '16px',
  },
  label: {
    display: 'block',
    fontSize: '14px',
    fontWeight: '500',
    color: '#374151',
    marginBottom: '4px',
  },
  formInput: {
    width: '100%',
    padding: '8px 12px',
    border: '1px solid #d1d5db',
    borderRadius: '6px',
    fontSize: '14px',
    outline: 'none',
  },
  checkbox: {
    marginRight: '8px',
  },
  error: {
    backgroundColor: '#fee2e2',
    border: '1px solid #f87171',
    color: '#b91c1c',
    padding: '12px',
    borderRadius: '6px',
    marginBottom: '16px',
  },
};

const AdminPage: React.FC<AdminPageProps> = ({ token, onLogout }) => {
  const [activeTab, setActiveTab] = useState<'users' | 'rag'>('users');
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(false);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [editingUser, setEditingUser] = useState<User | null>(null);
  const [formData, setFormData] = useState({
    username: '',
    password: '',
    full_name: '',
    department: '',
    is_admin: false
  });
  const [error, setError] = useState('');
  const [searchTerm, setSearchTerm] = useState('');
  const [filterStatus, setFilterStatus] = useState<'all' | 'active' | 'inactive'>('all');
  const [filterRole, setFilterRole] = useState<'all' | 'admin' | 'user'>('all');
  const [showPasswordReset, setShowPasswordReset] = useState<number | null>(null);
  const [newPassword, setNewPassword] = useState('');
  
  // RAG management states
  const [ragStats, setRagStats] = useState<RAGStats | null>(null);
  const [ragDocuments, setRagDocuments] = useState<RAGDocument[]>([]);
  const [uploadFile, setUploadFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [embeddingStatus, setEmbeddingStatus] = useState<any>(null);
  
  // Indexing progress states
  const [indexingProgress, setIndexingProgress] = useState<IndexingProgress>({
    status: 'idle',
    current_file: null,
    processed_files: [],
    failed_files: [],
    total_files: 0,
    completed_files: 0,
    chunks_created: 0,
    start_time: null,
    messages: []
  });
  const wsRef = useRef<WebSocket | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const [vllmStatus, setVllmStatus] = useState<any>(null);

  // Setup axios defaults
  useEffect(() => {
    axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
  }, [token]);

  // WebSocket connection for indexing progress
  useEffect(() => {
    if (activeTab === 'rag') {
      // Connect to WebSocket
      const ws = new WebSocket('ws://localhost:8003/api/v1/rag/ws/progress');
      
      ws.onopen = () => {
        console.log('WebSocket connected');
      };
      
      ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        setIndexingProgress(data);
        
        // 인덱싱 완료시 문서 목록 새로고침
        if (data.status === 'completed') {
          setTimeout(() => {
            loadRAGStats();
            loadRAGDocuments();
          }, 1000);
        }
      };
      
      ws.onerror = (error) => {
        console.error('WebSocket error:', error);
      };
      
      ws.onclose = () => {
        console.log('WebSocket disconnected');
      };
      
      wsRef.current = ws;
      
      return () => {
        if (wsRef.current) {
          wsRef.current.close();
        }
      };
    }
  }, [activeTab]);
  
  // Auto-scroll messages
  useEffect(() => {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [indexingProgress.messages]);

  // RAG Management Functions
  const loadRAGStats = async () => {
    try {
      const response = await axios.get('/api/v1/rag/stats');
      setRagStats(response.data);
    } catch (error) {
      console.error('Failed to load RAG stats:', error);
    }
  };

  const loadRAGDocuments = async () => {
    try {
      const response = await axios.get('/api/v1/rag/documents');
      setRagDocuments(response.data.documents || []);
    } catch (error) {
      console.error('Failed to load RAG documents:', error);
    }
  };

  const loadServiceStatus = async () => {
    try {
      const [embeddingRes, vllmRes] = await Promise.all([
        axios.get('/api/v1/rag/embedding/status'),
        axios.get('/api/v1/rag/vllm/status')
      ]);
      setEmbeddingStatus(embeddingRes.data);
      setVllmStatus(vllmRes.data);
    } catch (error) {
      console.error('Failed to load service status:', error);
    }
  };

  const handleFileUpload = async () => {
    if (!uploadFile) return;
    
    setUploading(true);
    const formData = new FormData();
    formData.append('file', uploadFile);
    
    try {
      await axios.post('/api/v1/rag/documents/upload', formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      });
      alert('문서가 성공적으로 업로드되었습니다');
      setUploadFile(null);
      loadRAGDocuments();
      loadRAGStats();
    } catch (error) {
      console.error('Upload failed:', error);
      alert('문서 업로드에 실패했습니다');
    } finally {
      setUploading(false);
    }
  };

  const handleDeleteDocument = async (documentId: string) => {
    if (!window.confirm('이 문서를 인덱스에서 삭제하시겠습니까?')) return;
    
    try {
      // Properly encode the document ID to handle Korean characters and special characters
      const encodedDocumentId = encodeURIComponent(documentId);
      await axios.delete(`/api/v1/rag/documents/${encodedDocumentId}`);
      alert('문서가 성공적으로 삭제되었습니다');
      loadRAGDocuments();
      loadRAGStats();
    } catch (error) {
      console.error('Delete failed:', error);
      alert('문서 삭제에 실패했습니다');
    }
  };

  const handleReindex = async () => {
    if (!window.confirm('모든 문서를 재인덱싱하시겠습니까? 시간이 걸릴 수 있습니다.')) return;
    
    try {
      await axios.post('/api/v1/rag/reindex');
      alert('재인덱싱이 시작되었습니다');
    } catch (error) {
      console.error('Reindex failed:', error);
      alert('재인덱싱 시작에 실패했습니다');
    }
  };

  const handleClearVectorStore = async () => {
    if (!window.confirm('경고: 모든 인덱스된 문서가 삭제됩니다! 계속하시겠습니까?')) return;
    if (!window.confirm('이 작업은 되돌릴 수 없습니다. 계속하시겠습니까?')) return;
    
    try {
      await axios.post('/api/v1/rag/clear');
      alert('벡터 저장소가 초기화되었습니다');
      loadRAGStats();
      loadRAGDocuments();
    } catch (error) {
      console.error('Clear failed:', error);
      alert('벡터 저장소 초기화에 실패했습니다');
    }
  };

  // Load users
  const loadUsers = async () => {
    setLoading(true);
    try {
      const response = await axios.get('/api/v1/admin/users');
      setUsers(response.data);
    } catch (err: any) {
      console.error('Failed to load users:', err);
      if (err.response?.status === 403) {
        alert('Admin access required');
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (activeTab === 'users') {
      loadUsers();
    } else if (activeTab === 'rag') {
      loadRAGStats();
      loadRAGDocuments();
      loadServiceStatus();
    }
  }, [activeTab]);

  // Create user
  const handleCreateUser = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    
    try {
      await axios.post('/api/v1/admin/users', formData);
      setShowCreateForm(false);
      setFormData({
        username: '',
        password: '',
        full_name: '',
        department: '',
        is_admin: false
      });
      loadUsers();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to create user');
    }
  };

  // Update user
  const handleUpdateUser = async (userId: number) => {
    try {
      const updateData: any = {
        full_name: editingUser?.full_name,
        department: editingUser?.department,
        is_admin: editingUser?.is_admin,
        is_active: editingUser?.is_active
      };
      
      await axios.put(`/api/v1/admin/users/${userId}`, updateData);
      setEditingUser(null);
      loadUsers();
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to update user');
    }
  };

  // Toggle user active status
  const handleToggleActive = async (userId: number) => {
    try {
      await axios.post(`/api/v1/admin/users/${userId}/toggle-active`);
      loadUsers();
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to toggle user status');
    }
  };

  // Delete user
  const handleDeleteUser = async (userId: number, username: string) => {
    if (!window.confirm(`Are you sure you want to delete user "${username}"?`)) {
      return;
    }
    
    try {
      await axios.delete(`/api/v1/admin/users/${userId}`);
      loadUsers();
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to delete user');
    }
  };

  // Reset password
  const handlePasswordReset = async (userId: number) => {
    if (!newPassword || newPassword.length < 8) {
      alert('Password must be at least 8 characters');
      return;
    }
    
    try {
      await axios.put(`/api/v1/admin/users/${userId}`, {
        password: newPassword
      });
      setShowPasswordReset(null);
      setNewPassword('');
      alert('Password reset successfully');
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to reset password');
    }
  };

  // Filter users
  const filteredUsers = users.filter(user => {
    const matchesSearch = user.username.toLowerCase().includes(searchTerm.toLowerCase()) ||
                          user.full_name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
                          user.department?.toLowerCase().includes(searchTerm.toLowerCase());
    
    const matchesStatus = filterStatus === 'all' || 
                         (filterStatus === 'active' && user.is_active) ||
                         (filterStatus === 'inactive' && !user.is_active);
    
    const matchesRole = filterRole === 'all' || 
                       (filterRole === 'admin' && user.is_admin) ||
                       (filterRole === 'user' && !user.is_admin);
    
    return matchesSearch && matchesStatus && matchesRole;
  });

  // Stats
  const stats = {
    total: users.length,
    active: users.filter(u => u.is_active).length,
    admins: users.filter(u => u.is_admin).length,
    inactive: users.filter(u => !u.is_active).length
  };

  return (
    <div style={styles.container}>
      {/* Header */}
      <div style={styles.header}>
        <div style={styles.headerContent}>
          <h1 style={styles.title}>Admin Panel</h1>
          <div style={{ display: 'flex', gap: '16px' }}>
            <button
              onClick={() => window.location.reload()}
              style={{
                ...styles.button,
                backgroundColor: '#2563eb',
                color: 'white',
              }}
              onMouseOver={(e) => e.currentTarget.style.backgroundColor = '#1d4ed8'}
              onMouseOut={(e) => e.currentTarget.style.backgroundColor = '#2563eb'}
            >
              <svg width="16" height="16" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" d="M10 19l-7-7m0 0l7-7m-7 7h18"></path>
              </svg>
              Back to Chat
            </button>
            <button
              onClick={onLogout}
              style={{
                ...styles.button,
                backgroundColor: '#dc2626',
                color: 'white',
              }}
              onMouseOver={(e) => e.currentTarget.style.backgroundColor = '#b91c1c'}
              onMouseOut={(e) => e.currentTarget.style.backgroundColor = '#dc2626'}
            >
              <svg width="16" height="16" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1"></path>
              </svg>
              Logout
            </button>
          </div>
        </div>
      </div>

      {/* Tab Navigation */}
      <div style={styles.mainContent}>
        <div style={{
          display: 'flex',
          gap: '8px',
          marginBottom: '24px',
          borderBottom: '2px solid #e5e7eb',
          paddingBottom: '8px'
        }}>
          <button
            onClick={() => setActiveTab('users')}
            style={{
              padding: '8px 16px',
              border: 'none',
              backgroundColor: activeTab === 'users' ? '#3b82f6' : 'transparent',
              color: activeTab === 'users' ? 'white' : '#6b7280',
              borderRadius: '6px',
              cursor: 'pointer',
              fontSize: '16px',
              fontWeight: '500',
              transition: 'all 0.2s'
            }}
          >
            사용자 관리
          </button>
          <button
            onClick={() => setActiveTab('rag')}
            style={{
              padding: '8px 16px',
              border: 'none',
              backgroundColor: activeTab === 'rag' ? '#3b82f6' : 'transparent',
              color: activeTab === 'rag' ? 'white' : '#6b7280',
              borderRadius: '6px',
              cursor: 'pointer',
              fontSize: '16px',
              fontWeight: '500',
              transition: 'all 0.2s'
            }}
          >
            RAG 시스템 관리
          </button>
        </div>

      {/* Content based on active tab */}
      {activeTab === 'users' ? (
        <>
          {/* User Stats Cards */}
          <div style={styles.statsGrid}>
          <div style={styles.statCard}>
            <div style={styles.statLabel}>Total Users</div>
            <div style={styles.statValue}>{stats.total}</div>
          </div>
          <div style={{ ...styles.statCard, backgroundColor: '#f0fdf4' }}>
            <div style={{ ...styles.statLabel, color: '#16a34a' }}>Active Users</div>
            <div style={{ ...styles.statValue, color: '#16a34a' }}>{stats.active}</div>
          </div>
          <div style={{ ...styles.statCard, backgroundColor: '#faf5ff' }}>
            <div style={{ ...styles.statLabel, color: '#9333ea' }}>Admins</div>
            <div style={{ ...styles.statValue, color: '#9333ea' }}>{stats.admins}</div>
          </div>
          <div style={{ ...styles.statCard, backgroundColor: '#fef2f2' }}>
            <div style={{ ...styles.statLabel, color: '#dc2626' }}>Inactive</div>
            <div style={{ ...styles.statValue, color: '#dc2626' }}>{stats.inactive}</div>
          </div>
        </div>

        {/* Search and Filters */}
        <div style={styles.filterSection}>
          <div style={styles.filterGrid}>
            <input
              type="text"
              placeholder="Search users..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              style={styles.searchInput}
            />
            <select
              value={filterStatus}
              onChange={(e) => setFilterStatus(e.target.value as any)}
              style={styles.select}
            >
              <option value="all">All Status</option>
              <option value="active">Active Only</option>
              <option value="inactive">Inactive Only</option>
            </select>
            <select
              value={filterRole}
              onChange={(e) => setFilterRole(e.target.value as any)}
              style={styles.select}
            >
              <option value="all">All Roles</option>
              <option value="admin">Admins Only</option>
              <option value="user">Users Only</option>
            </select>
          </div>
        </div>

        {/* Create User Button */}
        <div style={{ marginBottom: '24px' }}>
          <button
            onClick={() => setShowCreateForm(!showCreateForm)}
            style={{
              ...styles.button,
              ...styles.primaryButton,
            }}
            onMouseOver={(e) => e.currentTarget.style.backgroundColor = '#2563eb'}
            onMouseOut={(e) => e.currentTarget.style.backgroundColor = '#3b82f6'}
          >
            + Create New User
          </button>
        </div>

        {/* Create User Form */}
        {showCreateForm && (
          <div style={{ ...styles.tableContainer, marginBottom: '24px', padding: '24px' }}>
            <h2 style={{ fontSize: '20px', fontWeight: '600', marginBottom: '16px' }}>Create New User</h2>
            {error && <div style={styles.error}>{error}</div>}
            <form onSubmit={handleCreateUser}>
              <div style={styles.formGrid}>
                <div>
                  <label style={styles.label}>Username *</label>
                  <input
                    type="text"
                    required
                    value={formData.username}
                    onChange={(e) => setFormData({...formData, username: e.target.value})}
                    style={styles.formInput}
                  />
                </div>
                <div>
                  <label style={styles.label}>Password *</label>
                  <input
                    type="password"
                    required
                    minLength={8}
                    value={formData.password}
                    onChange={(e) => setFormData({...formData, password: e.target.value})}
                    style={styles.formInput}
                  />
                </div>
                <div>
                  <label style={styles.label}>Full Name</label>
                  <input
                    type="text"
                    value={formData.full_name}
                    onChange={(e) => setFormData({...formData, full_name: e.target.value})}
                    style={styles.formInput}
                  />
                </div>
                <div>
                  <label style={styles.label}>Department</label>
                  <input
                    type="text"
                    value={formData.department}
                    onChange={(e) => setFormData({...formData, department: e.target.value})}
                    style={styles.formInput}
                  />
                </div>
              </div>
              <div style={{ marginTop: '16px' }}>
                <label style={{ display: 'flex', alignItems: 'center' }}>
                  <input
                    type="checkbox"
                    checked={formData.is_admin}
                    onChange={(e) => setFormData({...formData, is_admin: e.target.checked})}
                    style={styles.checkbox}
                  />
                  <span style={{ fontSize: '14px', fontWeight: '500', color: '#374151' }}>Admin User</span>
                </label>
              </div>
              <div style={{ marginTop: '24px', display: 'flex', gap: '12px' }}>
                <button
                  type="submit"
                  style={{
                    ...styles.button,
                    ...styles.primaryButton,
                  }}
                >
                  Create User
                </button>
                <button
                  type="button"
                  onClick={() => {
                    setShowCreateForm(false);
                    setError('');
                  }}
                  style={{
                    ...styles.button,
                    backgroundColor: '#9ca3af',
                    color: 'white',
                  }}
                >
                  Cancel
                </button>
              </div>
            </form>
          </div>
        )}

        {/* Users Table */}
        <div style={styles.tableContainer}>
          {loading ? (
            <div style={{ padding: '32px', textAlign: 'center' }}>
              <div style={{
                display: 'inline-block',
                width: '32px',
                height: '32px',
                border: '3px solid #e5e7eb',
                borderTop: '3px solid #3b82f6',
                borderRadius: '50%',
                animation: 'spin 1s linear infinite',
              }}>
              </div>
              <div style={{ marginTop: '8px', color: '#6b7280' }}>Loading users...</div>
            </div>
          ) : filteredUsers.length === 0 ? (
            <div style={{ padding: '32px', textAlign: 'center', color: '#6b7280' }}>
              {searchTerm || filterStatus !== 'all' || filterRole !== 'all' 
                ? 'No users found matching your filters' 
                : 'No users registered yet'}
            </div>
          ) : (
            <table style={styles.table}>
              <thead style={styles.tableHeader}>
                <tr>
                  <th style={styles.tableHeaderCell}>Username</th>
                  <th style={styles.tableHeaderCell}>Full Name</th>
                  <th style={styles.tableHeaderCell}>Department</th>
                  <th style={styles.tableHeaderCell}>Status</th>
                  <th style={styles.tableHeaderCell}>Role</th>
                  <th style={styles.tableHeaderCell}>Created</th>
                  <th style={{ ...styles.tableHeaderCell, textAlign: 'right', minWidth: '300px' }}>Actions</th>
                </tr>
              </thead>
              <tbody>
                {filteredUsers.map((user) => (
                  <tr key={user.id} style={styles.tableRow}>
                    <td style={styles.tableCell}>
                      <span style={{ fontWeight: '500' }}>{user.username}</span>
                    </td>
                    <td style={styles.tableCell}>
                      {editingUser?.id === user.id ? (
                        <input
                          type="text"
                          value={editingUser.full_name || ''}
                          onChange={(e) => setEditingUser({...editingUser, full_name: e.target.value})}
                          style={styles.input}
                        />
                      ) : (
                        <span>{user.full_name || '-'}</span>
                      )}
                    </td>
                    <td style={styles.tableCell}>
                      {editingUser?.id === user.id ? (
                        <input
                          type="text"
                          value={editingUser.department || ''}
                          onChange={(e) => setEditingUser({...editingUser, department: e.target.value})}
                          style={styles.input}
                        />
                      ) : (
                        <span>{user.department || '-'}</span>
                      )}
                    </td>
                    <td style={styles.tableCell}>
                      <span style={{
                        ...styles.badge,
                        backgroundColor: user.is_active ? '#dcfce7' : '#fee2e2',
                        color: user.is_active ? '#16a34a' : '#dc2626',
                      }}>
                        {user.is_active ? 'Active' : 'Inactive'}
                      </span>
                    </td>
                    <td style={styles.tableCell}>
                      {editingUser?.id === user.id ? (
                        <label style={{ display: 'flex', alignItems: 'center' }}>
                          <input
                            type="checkbox"
                            checked={editingUser.is_admin}
                            onChange={(e) => setEditingUser({...editingUser, is_admin: e.target.checked})}
                            style={{ marginRight: '4px' }}
                          />
                          <span style={{ fontSize: '14px' }}>Admin</span>
                        </label>
                      ) : (
                        <span style={{
                          ...styles.badge,
                          backgroundColor: user.is_admin ? '#f3e8ff' : '#f3f4f6',
                          color: user.is_admin ? '#9333ea' : '#6b7280',
                        }}>
                          {user.is_admin ? 'Admin' : 'User'}
                        </span>
                      )}
                    </td>
                    <td style={styles.tableCell}>
                      {new Date(user.created_at).toLocaleDateString()}
                    </td>
                    <td style={{ ...styles.tableCell, textAlign: 'right' }}>
                      {showPasswordReset === user.id ? (
                        <div style={{ display: 'flex', justifyContent: 'flex-end', alignItems: 'center', gap: '8px' }}>
                          <input
                            type="password"
                            placeholder="New password"
                            value={newPassword}
                            onChange={(e) => setNewPassword(e.target.value)}
                            style={{ ...styles.input, width: '150px' }}
                            minLength={8}
                          />
                          <button
                            onClick={() => handlePasswordReset(user.id)}
                            style={{ color: '#16a34a', cursor: 'pointer', background: 'none', border: 'none' }}
                          >
                            ✓
                          </button>
                          <button
                            onClick={() => {
                              setShowPasswordReset(null);
                              setNewPassword('');
                            }}
                            style={{ color: '#6b7280', cursor: 'pointer', background: 'none', border: 'none' }}
                          >
                            ✕
                          </button>
                        </div>
                      ) : editingUser?.id === user.id ? (
                        <>
                          <button
                            onClick={() => handleUpdateUser(user.id)}
                            style={{ color: '#16a34a', marginRight: '12px', cursor: 'pointer', background: 'none', border: 'none' }}
                          >
                            Save
                          </button>
                          <button
                            onClick={() => setEditingUser(null)}
                            style={{ color: '#6b7280', cursor: 'pointer', background: 'none', border: 'none' }}
                          >
                            Cancel
                          </button>
                        </>
                      ) : (
                        <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '8px' }}>
                          <button
                            onClick={() => setEditingUser(user)}
                            style={{
                              ...styles.button,
                              padding: '6px 12px',
                              fontSize: '13px',
                              backgroundColor: '#e0e7ff',
                              color: '#4f46e5',
                            }}
                          >
                            Edit
                          </button>
                          <button
                            onClick={() => setShowPasswordReset(user.id)}
                            style={{
                              ...styles.button,
                              padding: '6px 12px',
                              fontSize: '13px',
                              backgroundColor: '#dbeafe',
                              color: '#2563eb',
                            }}
                          >
                            Reset
                          </button>
                          <button
                            onClick={() => handleToggleActive(user.id)}
                            style={{
                              ...styles.button,
                              padding: '6px 12px',
                              fontSize: '13px',
                              backgroundColor: user.is_active ? '#fef3c7' : '#dcfce7',
                              color: user.is_active ? '#d97706' : '#16a34a',
                            }}
                          >
                            {user.is_active ? 'Deactivate' : 'Activate'}
                          </button>
                          <button
                            onClick={() => handleDeleteUser(user.id, user.username)}
                            style={{
                              ...styles.button,
                              padding: '6px 12px',
                              fontSize: '13px',
                              backgroundColor: '#fee2e2',
                              color: '#dc2626',
                            }}
                          >
                            Delete
                          </button>
                        </div>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>

        {/* Footer */}
        <div style={{ marginTop: '24px', textAlign: 'center', fontSize: '14px', color: '#6b7280' }}>
          <p>Total: {filteredUsers.length} users {searchTerm && `(filtered from ${users.length})`}</p>
        </div>
        </>
      ) : (
        <>
          {/* RAG Management Section */}
          {/* RAG Stats Cards */}
          <div style={styles.statsGrid}>
            <div style={styles.statCard}>
              <div style={styles.statLabel}>총 문서</div>
              <div style={styles.statValue}>{ragStats?.total_documents || 0}</div>
            </div>
            <div style={{ ...styles.statCard, backgroundColor: '#fef3c7' }}>
              <div style={styles.statLabel}>총 청크</div>
              <div style={styles.statValue}>{ragStats?.total_chunks || 0}</div>
            </div>
            <div style={{ ...styles.statCard, backgroundColor: '#dbeafe' }}>
              <div style={styles.statLabel}>텍스트 청크</div>
              <div style={styles.statValue}>{ragStats?.text_chunks || 0}</div>
            </div>
            <div style={{ ...styles.statCard, backgroundColor: '#f3e8ff' }}>
              <div style={styles.statLabel}>보행 파라미터 포함</div>
              <div style={styles.statValue}>{ragStats?.chunks_with_gait_params || 0}</div>
            </div>
          </div>

          {/* Service Status */}
          <div style={{ 
            backgroundColor: 'white',
            borderRadius: '8px',
            padding: '16px',
            marginBottom: '24px',
            boxShadow: '0 1px 3px rgba(0, 0, 0, 0.1)'
          }}>
            <h3 style={{ fontSize: '18px', fontWeight: '600', marginBottom: '16px' }}>서비스 상태</h3>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
              <div>
                <h4 style={{ fontSize: '14px', fontWeight: '500', color: '#6b7280', marginBottom: '8px' }}>임베딩 서비스</h4>
                <div style={{ fontSize: '14px' }}>
                  <div>상태: <span style={{ color: embeddingStatus?.status === 'active' ? '#10b981' : '#ef4444' }}>
                    {embeddingStatus?.status || 'unknown'}
                  </span></div>
                  <div>모델: {embeddingStatus?.model}</div>
                  <div>차원: {embeddingStatus?.dimension}</div>
                  <div>디바이스: {embeddingStatus?.device}</div>
                </div>
              </div>
              <div>
                <h4 style={{ fontSize: '14px', fontWeight: '500', color: '#6b7280', marginBottom: '8px' }}>vLLM 서비스</h4>
                <div style={{ fontSize: '14px' }}>
                  <div>상태: <span style={{ color: vllmStatus?.status === 'active' ? '#10b981' : '#ef4444' }}>
                    {vllmStatus?.status || 'unknown'}
                  </span></div>
                  <div>모델: Nemotron-Mini-128k</div>
                  <div>최대 토큰: {vllmStatus?.max_tokens}</div>
                  <div>온도: {vllmStatus?.temperature}</div>
                </div>
              </div>
            </div>
          </div>

          {/* Document Upload */}
          <div style={{ 
            backgroundColor: 'white',
            borderRadius: '8px',
            padding: '16px',
            marginBottom: '24px',
            boxShadow: '0 1px 3px rgba(0, 0, 0, 0.1)'
          }}>
            <h3 style={{ fontSize: '18px', fontWeight: '600', marginBottom: '16px' }}>문서 업로드</h3>
            <div style={{ display: 'flex', gap: '16px', alignItems: 'center' }}>
              <input
                type="file"
                accept=".pdf"
                onChange={(e) => setUploadFile(e.target.files?.[0] || null)}
                style={{ flex: 1 }}
              />
              <button
                onClick={handleFileUpload}
                disabled={!uploadFile || uploading}
                style={{
                  padding: '8px 16px',
                  backgroundColor: uploadFile && !uploading ? '#3b82f6' : '#9ca3af',
                  color: 'white',
                  border: 'none',
                  borderRadius: '6px',
                  cursor: uploadFile && !uploading ? 'pointer' : 'not-allowed'
                }}
              >
                {uploading ? '업로드 중...' : '업로드'}
              </button>
            </div>
          </div>

          {/* Document List */}
          <div style={{ 
            backgroundColor: 'white',
            borderRadius: '8px',
            padding: '16px',
            marginBottom: '24px',
            boxShadow: '0 1px 3px rgba(0, 0, 0, 0.1)'
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
              <h3 style={{ fontSize: '18px', fontWeight: '600' }}>인덱스된 문서</h3>
              <div style={{ display: 'flex', gap: '8px' }}>
                <button
                  onClick={handleReindex}
                  style={{
                    padding: '8px 16px',
                    backgroundColor: '#f59e0b',
                    color: 'white',
                    border: 'none',
                    borderRadius: '6px',
                    cursor: 'pointer'
                  }}
                >
                  전체 재인덱싱
                </button>
                <button
                  onClick={handleClearVectorStore}
                  style={{
                    padding: '8px 16px',
                    backgroundColor: '#ef4444',
                    color: 'white',
                    border: 'none',
                    borderRadius: '6px',
                    cursor: 'pointer'
                  }}
                >
                  벡터 스토어 초기화
                </button>
              </div>
            </div>
            
            {/* Indexing Progress Display */}
            {indexingProgress.status !== 'idle' && (
              <div style={{
                marginTop: '24px',
                padding: '16px',
                backgroundColor: indexingProgress.status === 'error' ? '#fee2e2' : '#f0f9ff',
                borderRadius: '8px',
                border: `1px solid ${indexingProgress.status === 'error' ? '#fecaca' : '#bfdbfe'}`
              }}>
                <h4 style={{ 
                  fontSize: '16px', 
                  fontWeight: '600', 
                  marginBottom: '12px',
                  color: indexingProgress.status === 'error' ? '#dc2626' : '#1e40af'
                }}>
                  인덱싱 진행 상황
                </h4>
                
                {/* Progress Bar */}
                {indexingProgress.total_files > 0 && (
                  <div style={{ marginBottom: '16px' }}>
                    <div style={{ 
                      display: 'flex', 
                      justifyContent: 'space-between', 
                      marginBottom: '4px',
                      fontSize: '14px'
                    }}>
                      <span>진행률: {indexingProgress.completed_files} / {indexingProgress.total_files} 파일</span>
                      <span>{Math.round((indexingProgress.completed_files / indexingProgress.total_files) * 100)}%</span>
                    </div>
                    <div style={{
                      width: '100%',
                      height: '8px',
                      backgroundColor: '#e5e7eb',
                      borderRadius: '4px',
                      overflow: 'hidden'
                    }}>
                      <div style={{
                        width: `${(indexingProgress.completed_files / indexingProgress.total_files) * 100}%`,
                        height: '100%',
                        backgroundColor: indexingProgress.status === 'error' ? '#ef4444' : '#3b82f6',
                        transition: 'width 0.3s ease'
                      }} />
                    </div>
                  </div>
                )}
                
                {/* Current File */}
                {indexingProgress.current_file && (
                  <div style={{ marginBottom: '8px', fontSize: '14px' }}>
                    <strong>처리 중:</strong> {indexingProgress.current_file}
                  </div>
                )}
                
                {/* Statistics */}
                <div style={{ 
                  display: 'grid', 
                  gridTemplateColumns: 'repeat(4, 1fr)', 
                  gap: '16px',
                  marginBottom: '16px'
                }}>
                  <div>
                    <div style={{ fontSize: '12px', color: '#6b7280' }}>성공</div>
                    <div style={{ fontSize: '20px', fontWeight: '600', color: '#16a34a' }}>
                      {indexingProgress.processed_files.length}
                    </div>
                  </div>
                  <div>
                    <div style={{ fontSize: '12px', color: '#6b7280' }}>실패</div>
                    <div style={{ fontSize: '20px', fontWeight: '600', color: '#dc2626' }}>
                      {indexingProgress.failed_files.length}
                    </div>
                  </div>
                  <div>
                    <div style={{ fontSize: '12px', color: '#6b7280' }}>청크 생성</div>
                    <div style={{ fontSize: '20px', fontWeight: '600', color: '#1e40af' }}>
                      {indexingProgress.chunks_created}
                    </div>
                  </div>
                  <div>
                    <div style={{ fontSize: '12px', color: '#6b7280' }}>상태</div>
                    <div style={{ fontSize: '14px', fontWeight: '600' }}>
                      {indexingProgress.status === 'indexing' ? '진행 중...' :
                       indexingProgress.status === 'completed' ? '완료' :
                       indexingProgress.status === 'error' ? '오류' : '대기'}
                    </div>
                  </div>
                </div>
                
                {/* Message Log */}
                <div style={{
                  maxHeight: '200px',
                  overflowY: 'auto',
                  backgroundColor: 'white',
                  borderRadius: '4px',
                  padding: '8px',
                  fontSize: '12px',
                  fontFamily: 'monospace',
                  border: '1px solid #e5e7eb'
                }}>
                  {indexingProgress.messages.map((msg, idx) => (
                    <div key={idx} style={{ marginBottom: '4px' }}>
                      <span style={{ color: '#6b7280' }}>[{new Date(msg.time).toLocaleTimeString()}]</span>{' '}
                      <span style={{ 
                        color: msg.text.includes('✓') ? '#16a34a' : 
                               msg.text.includes('✗') ? '#dc2626' : '#111827'
                      }}>
                        {msg.text}
                      </span>
                    </div>
                  ))}
                  <div ref={messagesEndRef} />
                </div>
              </div>
            )}
            
            {ragDocuments && ragDocuments.length > 0 ? (
              <div style={{ overflowX: 'auto' }}>
                <div style={{ marginBottom: '16px', fontSize: '14px', color: '#6b7280' }}>
                  현재 {ragDocuments.length}개의 문서가 인덱싱되어 있습니다.
                </div>
                <table style={{ width: '100%', borderCollapse: 'collapse' as const }}>
                  <thead>
                    <tr style={{ borderBottom: '2px solid #e5e7eb' }}>
                      <th style={{ padding: '8px', textAlign: 'left', fontSize: '14px' }}>파일명</th>
                      <th style={{ padding: '8px', textAlign: 'center', fontSize: '14px' }}>인덱싱 시간</th>
                      <th style={{ padding: '8px', textAlign: 'center', fontSize: '14px' }}>작업</th>
                    </tr>
                  </thead>
                  <tbody>
                    {ragDocuments.map((doc: RAGDocument, idx: number) => (
                      <tr key={idx} style={{ borderBottom: '1px solid #e5e7eb' }}>
                        <td style={{ padding: '8px', fontSize: '14px' }}>
                          {doc.file_name || doc.document_id}
                        </td>
                        <td style={{ padding: '8px', textAlign: 'center', fontSize: '14px' }}>
                          {doc.indexed_at ? new Date(doc.indexed_at).toLocaleString() : '-'}
                        </td>
                        <td style={{ padding: '8px', textAlign: 'center' }}>
                          <button
                            onClick={() => handleDeleteDocument(doc.document_id)}
                            style={{
                              padding: '4px 12px',
                              backgroundColor: '#ef4444',
                              color: 'white',
                              border: 'none',
                              borderRadius: '4px',
                              fontSize: '12px',
                              cursor: 'pointer'
                            }}
                            onMouseOver={(e) => e.currentTarget.style.backgroundColor = '#dc2626'}
                            onMouseOut={(e) => e.currentTarget.style.backgroundColor = '#ef4444'}
                          >
                            삭제
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : ragStats && ragStats.documents && ragStats.documents.length > 0 ? (
              <div style={{ overflowX: 'auto' }}>
                <div style={{ marginBottom: '16px', fontSize: '14px', color: '#6b7280' }}>
                  현재 {ragStats.total_documents}개의 문서가 인덱싱되어 있습니다.
                </div>
                <table style={{ width: '100%', borderCollapse: 'collapse' as const }}>
                  <thead>
                    <tr style={{ borderBottom: '2px solid #e5e7eb' }}>
                      <th style={{ padding: '8px', textAlign: 'left', fontSize: '14px' }}>파일명</th>
                      <th style={{ padding: '8px', textAlign: 'center', fontSize: '14px' }}>상태</th>
                      <th style={{ padding: '8px', textAlign: 'center', fontSize: '14px' }}>작업</th>
                    </tr>
                  </thead>
                  <tbody>
                    {ragStats.documents.map((docId: string, idx: number) => (
                      <tr key={idx} style={{ borderBottom: '1px solid #e5e7eb' }}>
                        <td style={{ padding: '8px', fontSize: '14px' }}>
                          {docId.split('/').pop() || docId}
                        </td>
                        <td style={{ padding: '8px', textAlign: 'center' }}>
                          <span style={{
                            padding: '2px 8px',
                            backgroundColor: '#dcfce7',
                            color: '#16a34a',
                            borderRadius: '4px',
                            fontSize: '12px'
                          }}>
                            인덱싱됨
                          </span>
                        </td>
                        <td style={{ padding: '8px', textAlign: 'center' }}>
                          <button
                            onClick={() => handleDeleteDocument(docId)}
                            style={{
                              padding: '4px 12px',
                              backgroundColor: '#ef4444',
                              color: 'white',
                              border: 'none',
                              borderRadius: '4px',
                              fontSize: '12px',
                              cursor: 'pointer'
                            }}
                            onMouseOver={(e) => e.currentTarget.style.backgroundColor = '#dc2626'}
                            onMouseOut={(e) => e.currentTarget.style.backgroundColor = '#ef4444'}
                          >
                            삭제
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <div style={{ textAlign: 'center', color: '#6b7280', padding: '32px' }}>
                인덱스된 문서가 없습니다
              </div>
            )}
          </div>
        </>
      )}
      </div>

      <style>{`
        @keyframes spin {
          to { transform: rotate(360deg); }
        }
      `}</style>
    </div>
  );
};

export default AdminPage;