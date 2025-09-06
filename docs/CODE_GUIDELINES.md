# Code Guidelines for Medical Gait RAG WebUI

## 📏 File Size Rules

### Maximum Lines Per File
- **Python files**: 200 lines (ideal: 100-150)
- **React components**: 150 lines (ideal: 80-120)
- **CSS/Styles**: 100 lines (use utility classes)
- **Test files**: 300 lines (can be longer for comprehensive tests)

### When to Split Files
```python
# BAD: Single large file (400+ lines)
# auth.py
class User:
    # 50 lines
class AuthService:
    # 200 lines
def login():
    # 50 lines
def register():
    # 50 lines
def validate():
    # 50 lines

# GOOD: Split into modules
# models.py (50 lines)
class User:
    pass

# service.py (100 lines)
class AuthService:
    pass

# router.py (100 lines)
def login():
    pass
def register():
    pass

# utils.py (50 lines)
def validate():
    pass
```

## 🏗️ Project Structure Rules

### 1. One Class/Component Per File
```tsx
// BAD: Multiple components in one file
// components.tsx
export const Header = () => {...}
export const Footer = () => {...}
export const Sidebar = () => {...}

// GOOD: Separate files
// Header.tsx
export const Header = () => {...}

// Footer.tsx
export const Footer = () => {...}

// Sidebar.tsx
export const Sidebar = () => {...}
```

### 2. Clear Module Boundaries
```
backend/
├── auth/          # Everything auth-related
├── chat/          # Everything chat-related
├── database/      # Database only
└── core/          # Shared utilities only
```

## 💻 Python Code Style

### 1. Function Length
```python
# Maximum 30 lines per function
# If longer, split into smaller functions

# BAD
def process_message(message: str, user_id: int):
    # 100 lines of code...
    
# GOOD
def process_message(message: str, user_id: int):
    validated = validate_message(message)
    sanitized = sanitize_content(validated)
    result = save_to_database(sanitized, user_id)
    send_notification(user_id, result)
    return result

def validate_message(message: str) -> str:
    # 10 lines
    
def sanitize_content(content: str) -> str:
    # 10 lines
    
def save_to_database(content: str, user_id: int):
    # 10 lines
```

### 2. Class Design
```python
# Keep classes focused and small
class UserService:
    """Handle user-related operations."""
    
    def __init__(self, db_session):
        self.db = db_session
    
    def create_user(self, user_data: dict) -> User:
        """Create new user."""
        # 10-15 lines
        
    def get_user(self, user_id: int) -> User:
        """Get user by ID."""
        # 5-10 lines
        
    def update_user(self, user_id: int, data: dict) -> User:
        """Update user."""
        # 10-15 lines
        
# Total: ~50-80 lines
```

### 3. Import Organization
```python
# Standard library
import os
from datetime import datetime

# Third-party
from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session

# Local application
from ..database import get_db
from ..models import User
from .schemas import UserCreate
```

## ⚛️ React/TypeScript Style

### 1. Component Structure
```tsx
// components/ChatMessage.tsx (max 100 lines)
import React from 'react';
import { Message } from '../types';

interface ChatMessageProps {
  message: Message;
  onEdit?: (id: string) => void;
  onDelete?: (id: string) => void;
}

export const ChatMessage: React.FC<ChatMessageProps> = ({
  message,
  onEdit,
  onDelete
}) => {
  // Keep logic minimal
  const handleEdit = () => {
    onEdit?.(message.id);
  };
  
  return (
    <div className="message">
      <div className="message-content">{message.content}</div>
      {/* Simple, readable JSX */}
    </div>
  );
};
```

### 2. Custom Hooks
```tsx
// hooks/useAuth.ts (max 50 lines)
export const useAuth = () => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  
  useEffect(() => {
    // Load user from token
  }, []);
  
  const login = async (credentials) => {
    // 10 lines
  };
  
  const logout = () => {
    // 5 lines
  };
  
  return { user, loading, login, logout };
};
```

### 3. API Calls
```tsx
// api/chat.ts (max 80 lines)
import { axios } from './client';

export const chatApi = {
  // Each method 5-10 lines
  getConversations: async () => {
    return axios.get('/conversations');
  },
  
  createConversation: async (title: string) => {
    return axios.post('/conversations', { title });
  },
  
  sendMessage: async (conversationId: string, content: string) => {
    return axios.post(`/conversations/${conversationId}/messages`, {
      content
    });
  }
};
```

## 📦 Module Dependencies

### Dependency Direction
```
presentation → application → domain → infrastructure
     ↓             ↓            ↓            ↓
   (API)       (Use Cases)   (Entities)  (Database)
```

### Import Rules
1. **No circular imports**
2. **Domain layer imports nothing**
3. **Infrastructure imports only domain**
4. **Application imports domain and infrastructure**
5. **Presentation imports all layers**

## 🧪 Testing Guidelines

### Test File Organization
```python
# tests/test_auth.py (max 150 lines)
import pytest
from app.auth import AuthService

class TestAuthService:
    """Test authentication service."""
    
    def test_login_success(self):
        """Test successful login."""
        # 10 lines
        
    def test_login_invalid_password(self):
        """Test login with wrong password."""
        # 10 lines
        
    # Maximum 10 test methods per class
```

## 📝 Documentation Standards

### 1. Docstrings (Python)
```python
def process_document(
    file_path: str,
    chunk_size: int = 500
) -> List[str]:
    """Process document and return chunks.
    
    Args:
        file_path: Path to document file
        chunk_size: Size of each chunk
        
    Returns:
        List of document chunks
        
    Raises:
        FileNotFoundError: If file doesn't exist
    """
    # Implementation
```

### 2. Comments (When Necessary)
```python
# Use comments only for complex logic
def calculate_similarity(vec1, vec2):
    # Cosine similarity: dot(a,b) / (norm(a) * norm(b))
    dot_product = np.dot(vec1, vec2)
    norm_product = np.linalg.norm(vec1) * np.linalg.norm(vec2)
    return dot_product / norm_product
```

### 3. TypeScript Interfaces
```tsx
// types/index.ts
export interface User {
  id: string;
  username: string;
  fullName: string;
  department?: string;
}

export interface Message {
  id: string;
  conversationId: string;
  role: 'user' | 'assistant';
  content: string;
  sources?: Source[];
  createdAt: Date;
}
```

## 🔄 Refactoring Checklist

When a file exceeds size limits:

1. **Identify cohesive groups** of functions/methods
2. **Extract to new modules** with clear names
3. **Create interfaces** for module communication
4. **Update imports** in dependent files
5. **Run tests** to ensure nothing broke
6. **Update documentation**

## 🚀 Performance Guidelines

### 1. Database Queries
```python
# BAD: N+1 queries
users = db.query(User).all()
for user in users:
    messages = db.query(Message).filter_by(user_id=user.id).all()
    
# GOOD: Single query with join
users = db.query(User).options(
    joinedload(User.messages)
).all()
```

### 2. React Re-renders
```tsx
// BAD: Creating new objects in render
<Component onClick={() => handleClick(item.id)} />

// GOOD: Use useCallback
const handleItemClick = useCallback((id) => {
  // handle click
}, []);

<Component onClick={handleItemClick} />
```

## 📋 File Naming Conventions

### Python
```
user_service.py       # Snake case for modules
UserService           # Pascal case for classes
create_user()         # Snake case for functions
MAX_RETRIES          # Upper case for constants
```

### TypeScript/React
```
UserProfile.tsx       # Pascal case for components
useAuth.ts           # Camel case for hooks
chatApi.ts           # Camel case for utilities
types.ts             # Lower case for type files
```

## ✅ Code Review Checklist

Before committing:
- [ ] File is under 200 lines
- [ ] Functions are under 30 lines
- [ ] No circular imports
- [ ] Has necessary docstrings
- [ ] Follows naming conventions
- [ ] Tests pass
- [ ] No commented-out code
- [ ] No console.log/print statements
- [ ] Error handling in place
- [ ] Type hints (Python) / TypeScript types added