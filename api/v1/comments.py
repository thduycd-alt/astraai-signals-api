from fastapi import APIRouter
from pydantic import BaseModel
from services.comment_service import comment_service

router = APIRouter()

class CommentModel(BaseModel):
    user_name: str
    content: str

@router.get("/{symbol}")
async def get_comments(symbol: str):
    return comment_service.get_comments(symbol)

@router.post("/{symbol}")
async def add_comment(symbol: str, comment: CommentModel):
    return comment_service.add_comment(symbol, comment.user_name, comment.content)
