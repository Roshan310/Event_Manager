import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.dependencies import admin_user
from app.db.database import get_db
from app.models.user import User, UserRole
from app.schemas.pagination import PaginatedResponse
from app.schemas.user import RoleUpdate, UserOut
from app.services import user_service

router = APIRouter(prefix="/admin", tags=["Administration"])


@router.get("/users", response_model=PaginatedResponse[UserOut])
def users(
    q: str | None = Query(None, min_length=1, max_length=200),
    role: UserRole | None = None,
    is_active: bool | None = None,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    _: User = Depends(admin_user),
) -> PaginatedResponse[UserOut]:
    rows, total = user_service.list_users(db, limit, offset, q=q, role=role, is_active=is_active)
    users = [UserOut.model_validate(row) for row in rows]
    return PaginatedResponse.create(users, total, limit, offset)


@router.patch("/users/{user_id}/role", response_model=UserOut)
def change_role(
    user_id: uuid.UUID,
    request: RoleUpdate,
    db: Session = Depends(get_db),
    actor: User = Depends(admin_user),
) -> User:
    return user_service.change_role(db, user_id, request.role, actor)
