"""Document service for managing user documents."""

from ..repositories.document import DocumentRepository
from ..schemas.document import DocumentCreate, DocumentResponse
from ..models.document import Document
from ..exceptions.base import NotFoundException
from ..constants.messages import Messages
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
import logging

logger = logging.getLogger(__name__)


class DocumentService:
    """Service for document-related operations."""
    
    def __init__(self, session: AsyncSession):
        self.repository = DocumentRepository(session)
    
    async def create_document(self, document_data: DocumentCreate) -> DocumentResponse:
        """Create a new document."""
        document = Document(
            title=document_data.title,
            content=document_data.content,
            file_path=document_data.file_path,
            file_type=document_data.file_type,
            extra_data=document_data.extra_data,
            user_id=document_data.user_id
        )
        
        created = await self.repository.create(document)
        return DocumentResponse.model_validate(created)
    
    async def get_by_id(self, document_id: int) -> DocumentResponse:
        """Get a document by ID."""
        document = await self.repository.get_by_id(document_id)
        if not document:
            raise NotFoundException(Messages.DOCUMENT_NOT_FOUND, "Document")
        return DocumentResponse.model_validate(document)
    
    async def get_by_user(self, user_id: int, skip: int = 0, limit: int = 100) -> List[DocumentResponse]:
        """Get all documents for a user."""
        documents = await self.repository.get_by_user_id(user_id, skip, limit)
        return [DocumentResponse.model_validate(d) for d in documents]
    
    async def delete_document(self, document_id: int) -> bool:
        """Delete a document."""
        return await self.repository.delete(document_id)

