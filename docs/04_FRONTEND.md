# Frontend System (frontend/) - 상세 문서

## 기술 스택

- **React** 18.3.1
- **TypeScript** 5.6.2  
- **Tailwind CSS** 3.4.17
- **Axios** 1.7.9
- **Vite** 6.0.5 (빌드 도구)

## 디렉토리 구조

```
frontend/
├── src/
│   ├── App.tsx           # 메인 채팅 인터페이스 (1145 lines)
│   ├── AdminPage.tsx     # 관리자 패널 (1424 lines)
│   ├── styles.ts         # 스타일 상수
│   └── main.tsx         # 앱 진입점
├── public/              # 정적 파일
└── package.json         # 의존성
```

## 1. App.tsx - 메인 채팅 인터페이스 (1145 lines)

### 상태 관리:
```typescript
interface AppState {
  // 인증
  isLoggedIn: boolean
  token: string | null
  user: User | null
  
  // 채팅
  conversations: Conversation[]
  currentConversation: Conversation | null
  messages: Message[]
  
  // UI
  input: string
  isLoading: boolean
  showAdminPanel: boolean
  sidebarOpen: boolean
}
```

### 주요 컴포넌트 구조:

#### 1. 로그인 화면
```typescript
const handleLogin = async (e: FormEvent) => {
  // POST /api/auth/login
  // JWT 토큰을 localStorage에 저장
  // axios 기본 헤더 설정
  axios.defaults.headers.common['Authorization'] = `Bearer ${token}`
}
```

#### 2. 사이드바 (대화 목록)
```typescript
// 대화 목록 표시
conversations.map(conv => (
  <div onClick={() => loadConversation(conv.id)}>
    {conv.title}
    {conv.updated_at}
  </div>
))

// 새 대화 생성
const createNewConversation = async () => {
  // POST /api/chat/conversations
  // title: "New Chat {timestamp}"
}
```

#### 3. 메인 채팅 영역
```typescript
const handleSendMessage = async () => {
  // @ 감지로 모드 결정
  const isRagMode = input.trim().startsWith('@')
  
  // POST /api/chat/messages
  const response = await axios.post('/api/chat/messages', {
    conversation_id,
    content: input,
    use_rag: isRagMode
  })
  
  // 메시지 목록 업데이트
  setMessages([...messages, userMsg, assistantMsg])
}
```

#### 4. 메시지 렌더링
```typescript
interface Message {
  role: 'user' | 'assistant'
  content: string
  sources?: Array<{
    chunk_id: string
    content: string
    score: number
    metadata: {
      document_id: string
      page_number: number
    }
  }>
}

// 소스 문서 표시 (RAG 모드)
{message.sources && (
  <div className="sources">
    참고 문서:
    {message.sources.map(src => (
      <div>
        {src.metadata.document_id} (p.{src.metadata.page_number})
        신뢰도: {(src.score * 100).toFixed(1)}%
      </div>
    ))}
  </div>
)}
```

### API 통신:
```typescript
// axios 인터셉터 설정
axios.interceptors.request.use(config => {
  const token = localStorage.getItem('token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// 에러 처리
axios.interceptors.response.use(
  response => response,
  error => {
    if (error.response?.status === 401) {
      // 토큰 만료 - 로그아웃
      handleLogout()
    }
    return Promise.reject(error)
  }
)
```

## 2. AdminPage.tsx - 관리자 패널 (1424 lines)

### 인터페이스 정의:
```typescript
interface RAGStats {
  total_chunks: number
  total_documents: number
  text_chunks: number
  table_chunks: number
  chunks_with_gait_params: number  // 보행 파라미터 포함
  documents: string[]
}

interface RAGDocument {
  document_id: string
  file_name: string
  chunks: number
  indexed_at: string
}

interface IndexingProgress {
  status: 'idle' | 'indexing' | 'completed' | 'error'
  current_file: string | null
  processed_files: string[]
  total_files: number
  completed_files: number
}
```

### 주요 기능:

#### 1. 사용자 관리 탭
```typescript
const UserManagement = () => {
  // GET /api/v1/admin/users
  const fetchUsers = async () => {
    const users = await axios.get('/api/v1/admin/users')
  }
  
  // 사용자 생성
  const createUser = async (userData) => {
    await axios.post('/api/v1/admin/users', userData)
  }
  
  // 관리자 권한 토글
  const toggleAdmin = async (userId) => {
    await axios.put(`/api/v1/admin/users/${userId}/toggle-admin`)
  }
}
```

#### 2. RAG 관리 탭
```typescript
const RAGManagement = () => {
  // 통계 조회
  const fetchStats = async () => {
    const stats = await axios.get('/api/v1/rag/stats')
    // chunks_with_gait_params 표시
  }
  
  // 문서 업로드
  const handleFileUpload = async (file: File) => {
    const formData = new FormData()
    formData.append('file', file)
    
    await axios.post('/api/v1/rag/documents/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
  }
  
  // 문서 삭제
  const deleteDocument = async (documentId: string) => {
    // URL 인코딩 필요
    const encoded = encodeURIComponent(documentId)
    await axios.delete(`/api/v1/rag/documents/${encoded}`)
  }
}
```

#### 3. WebSocket 진행상황 모니터링
```typescript
const useWebSocketProgress = () => {
  useEffect(() => {
    const ws = new WebSocket('ws://localhost:8003/api/v1/rag/ws/progress')
    
    ws.onmessage = (event) => {
      const progress = JSON.parse(event.data)
      setIndexingProgress(progress)
      
      // 파일별 진행상황 표시
      if (progress.current_file) {
        console.log(`Processing: ${progress.current_file}`)
      }
    }
    
    return () => ws.close()
  }, [])
}
```

#### 4. 통계 카드 표시
```typescript
// 보행 파라미터 통계 카드
<div className="stat-card">
  <div className="stat-label">보행 파라미터 포함</div>
  <div className="stat-value">
    {ragStats?.chunks_with_gait_params || 0}
  </div>
  <div className="stat-desc">
    키워드가 감지된 청크
  </div>
</div>
```

### 스타일링 (Tailwind + Inline):
```typescript
const styles = {
  container: {
    minHeight: '100vh',
    background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)'
  },
  card: {
    backgroundColor: 'white',
    borderRadius: '12px',
    boxShadow: '0 4px 6px rgba(0, 0, 0, 0.1)',
    padding: '24px'
  },
  statCard: {
    background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
    color: 'white',
    padding: '20px',
    borderRadius: '8px'
  }
}
```

## 3. 라우팅 시스템

### 조건부 렌더링:
```typescript
function App() {
  const [showAdminPanel, setShowAdminPanel] = useState(false)
  
  // 관리자 패널 토글
  if (showAdminPanel && user?.is_admin) {
    return <AdminPage token={token} onLogout={handleLogout} />
  }
  
  // 메인 채팅 인터페이스
  return <ChatInterface />
}
```

## 4. 상태 관리 패턴

### Local State (useState):
- UI 상태 (모달, 탭, 로딩)
- 폼 입력값
- 임시 데이터

### Persistent State (localStorage):
- JWT 토큰
- 사용자 정보
- 테마 설정

### Server State (axios):
- 대화 목록
- 메시지 내역
- RAG 통계

## 5. 보행 파라미터 표시 플로우

```
1. AdminPage 마운트
    ↓
2. fetchRAGStats() 호출
    ↓
3. GET /api/v1/rag/stats
    ↓
4. Backend에서 ChromaDB 조회
    ↓
5. has_gait_params=true 카운트
    ↓
6. ragStats.chunks_with_gait_params 받음
    ↓
7. UI에 "보행 파라미터 포함: N개" 표시
```

## 6. 성능 최적화

### 디바운싱:
```typescript
// 검색 입력 디바운싱
const [searchTerm, setSearchTerm] = useState('')
const [debouncedSearch, setDebouncedSearch] = useState('')

useEffect(() => {
  const timer = setTimeout(() => {
    setDebouncedSearch(searchTerm)
  }, 300)
  
  return () => clearTimeout(timer)
}, [searchTerm])
```

### 메모이제이션:
```typescript
// 필터링된 사용자 목록
const filteredUsers = useMemo(() => {
  return users.filter(user => 
    user.username.includes(searchTerm) ||
    user.full_name?.includes(searchTerm)
  )
}, [users, searchTerm])
```

### 레이지 로딩:
```typescript
// 대화 목록 페이지네이션
const loadMoreConversations = async () => {
  const response = await axios.get('/api/chat/conversations', {
    params: { offset, limit: 20 }
  })
}
```

## 7. 에러 처리

### 전역 에러 바운더리:
```typescript
class ErrorBoundary extends Component {
  componentDidCatch(error, errorInfo) {
    console.error('React Error:', error, errorInfo)
  }
  
  render() {
    if (this.state.hasError) {
      return <div>오류가 발생했습니다. 새로고침해주세요.</div>
    }
    return this.props.children
  }
}
```

### API 에러 처리:
```typescript
try {
  const response = await axios.post('/api/chat/messages', data)
} catch (error) {
  if (error.response?.status === 429) {
    alert('요청이 너무 많습니다. 잠시 후 다시 시도하세요.')
  } else if (error.response?.status === 500) {
    alert('서버 오류가 발생했습니다.')
  }
}
```

## 8. 빌드 및 배포

### 개발 서버:
```bash
npm run dev  # Vite 개발 서버 (포트 3000)
```

### 프로덕션 빌드:
```bash
npm run build  # dist/ 폴더에 빌드
npm run preview  # 빌드 결과 미리보기
```

### 환경 변수:
```typescript
// .env
VITE_API_URL=http://localhost:8003
VITE_WS_URL=ws://localhost:8003
```