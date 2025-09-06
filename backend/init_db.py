#!/usr/bin/env python3
"""
Database initialization script for Medical Gait RAG
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database.models import Base, User, Conversation, Message
from auth.service import AuthService
from auth.schemas import UserCreate
from datetime import datetime
import argparse

def init_database(reset=False):
    """Initialize database with clean structure"""
    
    # Database URL
    DATABASE_URL = "sqlite:///./gait_rag.db"
    
    # Create engine
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
    
    if reset:
        print("Resetting database...")
        Base.metadata.drop_all(bind=engine)
    
    # Create tables
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    
    # Create session
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = SessionLocal()
    
    try:
        # Check if admin user exists
        admin_user = session.query(User).filter_by(username="admin").first()
        
        if not admin_user:
            print("Creating admin user...")
            auth_service = AuthService(session)
            admin_data = UserCreate(
                username="admin",
                password="admin12345",
                full_name="System Administrator",
                department="IT",
                is_admin=True
            )
            admin_user = auth_service.create_user(admin_data)
            admin_user.is_admin = True
            session.commit()
            print(f"   Created admin: {admin_user.username}")
        else:
            print("   Admin user already exists")
        
        # Check if demo user exists
        demo_user = session.query(User).filter_by(username="demouser").first()
        
        if not demo_user:
            print("Creating demo user...")
            auth_service = AuthService(session)
            demo_data = UserCreate(
                username="demouser",
                password="demo12345",
                full_name="Demo User",
                department="Demo",
                is_admin=False
            )
            demo_user = auth_service.create_user(demo_data)
            print(f"   Created: {demo_user.username}")
        else:
            print("   Demo user already exists")
        
        # Create sample conversation
        sample_conv = session.query(Conversation).filter_by(
            user_id=demo_user.id,
            title="Welcome to Medical Gait RAG"
        ).first()
        
        if not sample_conv:
            print("Creating welcome conversation...")
            sample_conv = Conversation(
                user_id=demo_user.id,
                title="Welcome to Medical Gait RAG",
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            session.add(sample_conv)
            session.flush()
            
            # Add welcome message
            welcome_msg = Message(
                conversation_id=sample_conv.id,
                role="assistant",
                content="""안녕하세요! Medical Gait RAG 시스템입니다.

저는 의료 보행 분석에 특화된 AI 어시스턴트입니다. 다음과 같은 도움을 드릴 수 있습니다:

**RAG 모드** (@ 사용)
- @파킨슨병 환자의 보행 특징은?
- @보행 분석의 주요 파라미터는?
- @정상 보행 주기의 단계는?

**일반 대화 모드**
- 보행 분석에 대한 일반적인 질문
- 의료 용어 설명
- 연구 관련 조언

시작하려면 질문을 입력해주세요!""",
                sources=None,
                created_at=datetime.utcnow()
            )
            session.add(welcome_msg)
            print("   Created welcome conversation")
        
        session.commit()
        print("\nDatabase initialization complete!")
        
        # Show summary
        user_count = session.query(User).count()
        conv_count = session.query(Conversation).count()
        msg_count = session.query(Message).count()
        
        print(f"\nDatabase Summary:")
        print(f"   - Users: {user_count}")
        print(f"   - Conversations: {conv_count}")
        print(f"   - Messages: {msg_count}")
        
    except Exception as e:
        print(f"Error: {e}")
        session.rollback()
        raise
    finally:
        session.close()

def clean_test_data():
    """Remove test data while preserving demo user"""
    
    DATABASE_URL = "sqlite:///./gait_rag.db"
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = SessionLocal()
    
    try:
        # Remove test users (keep demouser)
        test_users = session.query(User).filter(
            User.username.in_(['testuser', 'testuser1', 'test_1756708135'])
        ).all()
        
        for user in test_users:
            print(f"Removing user: {user.username}")
            session.delete(user)
        
        # Clean up untitled conversations
        untitled = session.query(Conversation).filter(
            Conversation.title.like('New Chat%')
        ).all()
        
        for conv in untitled:
            # Update title based on first message
            first_msg = session.query(Message).filter(
                Message.conversation_id == conv.id,
                Message.role == 'user'
            ).order_by(Message.created_at).first()
            
            if first_msg:
                # Generate better title
                content = first_msg.content.replace('@', '').strip()
                new_title = content[:50] + ('...' if len(content) > 50 else '')
                conv.title = new_title
                print(f"Updated conversation title: {new_title}")
        
        session.commit()
        print("\nTest data cleaned!")
        
    except Exception as e:
        print(f"Error: {e}")
        session.rollback()
    finally:
        session.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Medical Gait RAG Database Management")
    parser.add_argument('--reset', action='store_true', help='Reset database (delete all data)')
    parser.add_argument('--clean', action='store_true', help='Clean test data only')
    
    args = parser.parse_args()
    
    if args.clean:
        clean_test_data()
    else:
        init_database(reset=args.reset)