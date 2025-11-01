from fastapi import APIRouter, Depends, status
from ...services.document import DocumentService
from ...schemas.document import DocumentCreate, DocumentResponse
from ...database.session import get_db_session
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

router = APIRouter(prefix="/documents", tags=["documents"])


@router.post("", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def create_document(
    request: DocumentCreate,
    session: AsyncSession = Depends(get_db_session)
):
    service = DocumentService(session)
    return await service.create_document(request)


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: int,
    session: AsyncSession = Depends(get_db_session)
):
    service = DocumentService(session)
    return await service.get_by_id(document_id)


@router.get("/user/{user_id}", response_model=List[DocumentResponse])
async def get_user_documents(
    user_id: int,
    skip: int = 0,
    limit: int = 100,
    session: AsyncSession = Depends(get_db_session)
):
    service = DocumentService(session)
    return await service.get_by_user(user_id, skip, limit)


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    document_id: int,
    session: AsyncSession = Depends(get_db_session)
):
    service = DocumentService(session)
    await service.delete_document(document_id)
