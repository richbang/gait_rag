"""Chat service."""

from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from datetime import datetime
import json
from loguru import logger

from database.models import Conversation, Message, User
from .schemas import ConversationCreate, MessageCreate
from .rag_proxy import RAGProxyService


class ChatService:
    """Chat service for conversation management."""
    
    def __init__(self, db: Session):
        """Initialize chat service."""
        self.db = db
        self.rag_proxy = RAGProxyService()
    
    def create_conversation(
        self,
        user_id: int,
        conversation_data: ConversationCreate
    ) -> Conversation:
        """
        Create new conversation.
        
        Args:
            user_id: User ID
            conversation_data: Conversation creation data
            
        Returns:
            Created conversation
        """
        conversation = Conversation(
            user_id=user_id,
            title=conversation_data.title or "New Conversation"
        )
        
        self.db.add(conversation)
        self.db.commit()
        self.db.refresh(conversation)
        
        logger.info(f"Created conversation {conversation.id} for user {user_id}")
        return conversation
    
    def get_user_conversations(
        self,
        user_id: int,
        limit: int = 20,
        offset: int = 0
    ) -> List[Conversation]:
        """
        Get user's conversations.
        
        Args:
            user_id: User ID
            limit: Maximum number of conversations
            offset: Offset for pagination
            
        Returns:
            List of conversations
        """
        return self.db.query(Conversation).filter(
            Conversation.user_id == user_id
        ).order_by(
            Conversation.updated_at.desc()
        ).limit(limit).offset(offset).all()
    
    def get_conversation(
        self,
        conversation_id: int,
        user_id: int
    ) -> Optional[Conversation]:
        """
        Get conversation by ID.
        
        Args:
            conversation_id: Conversation ID
            user_id: User ID (for authorization)
            
        Returns:
            Conversation or None
        """
        return self.db.query(Conversation).filter(
            Conversation.id == conversation_id,
            Conversation.user_id == user_id
        ).first()
    
    def delete_conversation(
        self,
        conversation_id: int,
        user_id: int
    ) -> bool:
        """
        Delete conversation.
        
        Args:
            conversation_id: Conversation ID
            user_id: User ID (for authorization)
            
        Returns:
            True if deleted, False otherwise
        """
        conversation = self.get_conversation(conversation_id, user_id)
        if conversation:
            self.db.delete(conversation)
            self.db.commit()
            logger.info(f"Deleted conversation {conversation_id}")
            return True
        return False
    
    async def send_message(
        self,
        conversation_id: int,
        user_id: int,
        message_data: MessageCreate
    ) -> tuple[Message, Message]:
        """
        Send message and get response.
        
        Args:
            conversation_id: Conversation ID
            user_id: User ID
            message_data: Message data
            
        Returns:
            Tuple of (user_message, assistant_message)
        """
        # Verify conversation ownership
        conversation = self.get_conversation(conversation_id, user_id)
        if not conversation:
            raise ValueError(f"Conversation {conversation_id} not found")
        
        # Save user message
        user_message = Message(
            conversation_id=conversation_id,
            role="user",
            content=message_data.content
        )
        self.db.add(user_message)
        
        # Get RAG response
        try:
            if message_data.use_vllm:
                # Use QA endpoint with vLLM
                response = await self.rag_proxy.question_answer(
                    query=message_data.content,
                    limit=message_data.search_limit,
                    use_vllm=True,
                    document_types=message_data.document_types,
                    disease_categories=message_data.disease_categories,
                    min_score=message_data.min_score
                )
                
                assistant_content = response.get("answer", "No answer generated")
                sources = response.get("sources", [])
            else:
                # Use search only
                response = await self.rag_proxy.search_documents(
                    query=message_data.content,
                    limit=message_data.search_limit,
                    document_types=message_data.document_types,
                    disease_categories=message_data.disease_categories,
                    min_score=message_data.min_score
                )
                
                # Format search results as answer
                results = response.get("results", [])
                if results:
                    assistant_content = "Found the following relevant information:\n\n"
                    for i, result in enumerate(results[:3], 1):
                        assistant_content += f"{i}. {result['content'][:200]}...\n\n"
                else:
                    assistant_content = "No relevant documents found."
                
                sources = results
            
            # Save assistant message
            assistant_message = Message(
                conversation_id=conversation_id,
                role="assistant",
                content=assistant_content,
                sources=json.dumps(sources) if sources else None
            )
            self.db.add(assistant_message)
            
            # Update conversation timestamp
            conversation.updated_at = datetime.utcnow()
            
            # Update title if first message
            if not conversation.title or conversation.title == "New Conversation":
                # Use first 50 chars of user message as title
                conversation.title = message_data.content[:50] + ("..." if len(message_data.content) > 50 else "")
            
            self.db.commit()
            self.db.refresh(user_message)
            self.db.refresh(assistant_message)
            
            logger.info(f"Messages added to conversation {conversation_id}")
            return user_message, assistant_message
            
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            self.db.rollback()
            raise
    
    def get_conversation_messages(
        self,
        conversation_id: int,
        user_id: int,
        limit: int = 50,
        offset: int = 0
    ) -> List[Message]:
        """
        Get conversation messages.
        
        Args:
            conversation_id: Conversation ID
            user_id: User ID (for authorization)
            limit: Maximum number of messages
            offset: Offset for pagination
            
        Returns:
            List of messages
        """
        conversation = self.get_conversation(conversation_id, user_id)
        if not conversation:
            return []
        
        return self.db.query(Message).filter(
            Message.conversation_id == conversation_id
        ).order_by(
            Message.created_at.asc()
        ).limit(limit).offset(offset).all()