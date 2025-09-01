"""Chat API routes."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
import json
from loguru import logger

from database.session import get_db
from database.models import User
from auth.dependencies import get_current_user
from core.middleware import APIResponse
from .schemas import (
    ConversationCreate, ConversationResponse, ConversationWithMessages,
    MessageCreate, MessageResponse, SearchRequest, QARequest
)
from .service import ChatService
from .rag_proxy import RAGProxyService

router = APIRouter(prefix="/api/v1", tags=["Chat"])


@router.post("/conversations", response_model=ConversationResponse)
async def create_conversation(
    conversation_data: ConversationCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create new conversation."""
    try:
        chat_service = ChatService(db)
        conversation = chat_service.create_conversation(
            current_user.id,
            conversation_data
        )
        
        return ConversationResponse(
            id=conversation.id,
            user_id=conversation.user_id,
            title=conversation.title,
            created_at=conversation.created_at,
            updated_at=conversation.updated_at,
            message_count=0
        )
    except Exception as e:
        logger.error(f"Create conversation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/conversations", response_model=List[ConversationResponse])
async def get_conversations(
    limit: int = 20,
    offset: int = 0,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user's conversations."""
    try:
        chat_service = ChatService(db)
        conversations = chat_service.get_user_conversations(
            current_user.id,
            limit,
            offset
        )
        
        results = []
        for conv in conversations:
            results.append(ConversationResponse(
                id=conv.id,
                user_id=conv.user_id,
                title=conv.title,
                created_at=conv.created_at,
                updated_at=conv.updated_at,
                message_count=len(conv.messages)
            ))
        
        return results
    except Exception as e:
        logger.error(f"Get conversations error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/conversations/{conversation_id}", response_model=ConversationWithMessages)
async def get_conversation(
    conversation_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get conversation with messages."""
    try:
        chat_service = ChatService(db)
        conversation = chat_service.get_conversation(
            conversation_id,
            current_user.id
        )
        
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found"
            )
        
        # Parse sources from JSON string
        messages = []
        for msg in conversation.messages:
            sources = None
            if msg.sources:
                try:
                    sources = json.loads(msg.sources)
                except:
                    sources = None
            
            messages.append(MessageResponse(
                id=msg.id,
                conversation_id=msg.conversation_id,
                role=msg.role,
                content=msg.content,
                sources=sources,
                created_at=msg.created_at
            ))
        
        return ConversationWithMessages(
            id=conversation.id,
            user_id=conversation.user_id,
            title=conversation.title,
            created_at=conversation.created_at,
            updated_at=conversation.updated_at,
            messages=messages
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get conversation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.delete("/conversations/{conversation_id}")
async def delete_conversation(
    conversation_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete conversation."""
    try:
        chat_service = ChatService(db)
        deleted = chat_service.delete_conversation(
            conversation_id,
            current_user.id
        )
        
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found"
            )
        
        return APIResponse.success(message="Conversation deleted")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Delete conversation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/conversations/{conversation_id}/messages")
async def send_message(
    conversation_id: int,
    message_data: MessageCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Send message to conversation."""
    try:
        chat_service = ChatService(db)
        user_msg, assistant_msg = await chat_service.send_message(
            conversation_id,
            current_user.id,
            message_data
        )
        
        # Parse sources
        sources = None
        if assistant_msg.sources:
            try:
                sources = json.loads(assistant_msg.sources)
            except:
                sources = None
        
        return {
            "user_message": MessageResponse(
                id=user_msg.id,
                conversation_id=user_msg.conversation_id,
                role=user_msg.role,
                content=user_msg.content,
                sources=None,
                created_at=user_msg.created_at
            ),
            "assistant_message": MessageResponse(
                id=assistant_msg.id,
                conversation_id=assistant_msg.conversation_id,
                role=assistant_msg.role,
                content=assistant_msg.content,
                sources=sources,
                created_at=assistant_msg.created_at
            )
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Send message error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/rag/search")
async def search_documents(
    request: SearchRequest,
    current_user: User = Depends(get_current_user)
):
    """Search documents directly via RAG API."""
    try:
        rag_proxy = RAGProxyService()
        result = await rag_proxy.search_documents(
            query=request.query,
            limit=request.limit,
            document_types=request.document_types,
            disease_categories=request.disease_categories,
            min_score=request.min_score
        )
        await rag_proxy.close()
        return result
    except Exception as e:
        logger.error(f"RAG search error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/rag/qa")
async def question_answer(
    request: QARequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Question answering via RAG API."""
    try:
        rag_proxy = RAGProxyService()
        result = await rag_proxy.question_answer(
            query=request.query,
            limit=request.limit,
            use_vllm=request.use_vllm,
            document_types=request.document_types,
            disease_categories=request.disease_categories,
            min_score=request.min_score
        )
        
        # Save to conversation if requested
        if request.conversation_id:
            chat_service = ChatService(db)
            conversation = chat_service.get_conversation(
                request.conversation_id,
                current_user.id
            )
            
            if conversation:
                # Save messages
                from database.models import Message
                
                user_msg = Message(
                    conversation_id=request.conversation_id,
                    role="user",
                    content=request.query
                )
                db.add(user_msg)
                
                assistant_msg = Message(
                    conversation_id=request.conversation_id,
                    role="assistant",
                    content=result.get("answer", ""),
                    sources=json.dumps(result.get("sources", []))
                )
                db.add(assistant_msg)
                
                from datetime import datetime
                conversation.updated_at = datetime.utcnow()
                db.commit()
        
        await rag_proxy.close()
        return result
    except Exception as e:
        logger.error(f"RAG QA error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )