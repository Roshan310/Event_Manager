from pydantic import BaseModel, Field
from typing import TypeVar, Generic, List

T = TypeVar('T')


class PaginationParams(BaseModel):
    """Query parameters for pagination"""
    limit: int = Field(default=10, ge=1, le=100, description="Number of items per page")
    offset: int = Field(default=0, ge=0, description="Number of items to skip")


class PaginatedResponse(BaseModel, Generic[T]):
    """Generic paginated response wrapper"""
    items: List[T]
    total: int = Field(description="Total number of items available")
    limit: int = Field(description="Items per page")
    offset: int = Field(description="Items skipped")
    has_more: bool = Field(description="Whether there are more items")

    class Config:
        json_schema_extra = {
            "example": {
                "items": [],
                "total": 100,
                "limit": 10,
                "offset": 0,
                "has_more": True
            }
        }

    @classmethod
    def create(cls, items: List[T], total: int, limit: int, offset: int):
        """Factory method to create paginated response"""
        return cls(
            items=items,
            total=total,
            limit=limit,
            offset=offset,
            has_more=(offset + limit) < total
        )
