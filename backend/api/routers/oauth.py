from fastapi import APIRouter, Depends, Body

from ..validator import (
    user_login,
    refresh_user,
    Token
)

router = APIRouter(
    prefix="/oauth",
    tags=["OAuth"]
)

@router.post("/login")
async def login(code: str = Body(embed=True)) -> Token:
    return await user_login(code=code)

@router.post("/refresh")
async def refresh(new_token: str = Depends(refresh_user)) -> Token:
    return new_token
