"""
Custom Exception Classes
"""

from typing import Optional, Dict, Any


class RAGException(Exception):
    """Base exception for RAG system"""
    
    def __init__(
        self, 
        message: str, 
        details: Optional[Dict[str, Any]] = None,
        cause: Optional[Exception] = None
    ):
        super().__init__(message)
        self.message = message
        self.details = details or {}
        self.cause = cause
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary"""
        result = {
            "error": self.__class__.__name__,
            "message": self.message
        }
        
        if self.details:
            result["details"] = self.details
            
        if self.cause:
            result["cause"] = str(self.cause)
            
        return result


class DocumentProcessingError(RAGException):
    """Error in document processing"""
    
    def __init__(
        self,
        message: str,
        file_path: Optional[str] = None,
        page_number: Optional[int] = None,
        cause: Optional[Exception] = None
    ):
        details = {}
        if file_path:
            details["file_path"] = file_path
        if page_number:
            details["page_number"] = page_number
            
        super().__init__(message, details, cause)


class EmbeddingError(RAGException):
    """Error in embedding generation"""
    
    def __init__(
        self,
        message: str,
        text_length: Optional[int] = None,
        model_name: Optional[str] = None,
        cause: Optional[Exception] = None
    ):
        details = {}
        if text_length:
            details["text_length"] = text_length
        if model_name:
            details["model_name"] = model_name
            
        super().__init__(message, details, cause)


class VectorStoreError(RAGException):
    """Error in vector store operations"""
    
    def __init__(
        self,
        message: str,
        operation: Optional[str] = None,
        collection_name: Optional[str] = None,
        cause: Optional[Exception] = None
    ):
        details = {}
        if operation:
            details["operation"] = operation
        if collection_name:
            details["collection_name"] = collection_name
            
        super().__init__(message, details, cause)


class ValidationError(RAGException):
    """Data validation error"""
    
    def __init__(
        self,
        message: str,
        field_name: Optional[str] = None,
        field_value: Optional[Any] = None,
        cause: Optional[Exception] = None
    ):
        details = {}
        if field_name:
            details["field_name"] = field_name
        if field_value is not None:
            details["field_value"] = str(field_value)
            
        super().__init__(message, details, cause)


class ConfigurationError(RAGException):
    """Configuration error"""
    
    def __init__(
        self,
        message: str,
        config_key: Optional[str] = None,
        cause: Optional[Exception] = None
    ):
        details = {}
        if config_key:
            details["config_key"] = config_key
            
        super().__init__(message, details, cause)