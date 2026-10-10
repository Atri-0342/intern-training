
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.api.rate_limit import enforce_auth_rate_limit
from app.core.security import (
    create_access_token,
    hash_password,
    verify_password,
)
from app.db.dependencies import get_db
from app.models.models import User
from app.schemas.auth import RegisterRequest, TokenRequest, TokenResponse


router = APIRouter(
    prefix="/v1/auth",
    tags=["auth"],
)


@router.get("/me")
def get_me(
    current_user: dict = Depends(get_current_user),
) -> dict:
    return current_user


@router.post("/register", status_code=201)
def register_user(
    request: Request,
    user: RegisterRequest,
    db: Session = Depends(get_db),
) -> dict:
    enforce_auth_rate_limit(
        request=request,
        email=user.email,
    )

    existing_user = (
        db.query(User)
        .filter(User.email == user.email)
        .first()
    )

    if existing_user is not None:
        raise HTTPException(
            status_code=409,
            detail="User already exists",
        )

    db_user = User(
        id=str(uuid4()),
        email=user.email,
        hashed_password=hash_password(user.password),
        role=user.role,
    )

    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    return {
        "message": "User registered successfully",
        "user_id": db_user.id,
    }


@router.post("/token", response_model=TokenResponse)
def login_user(
    request: Request,
    user: TokenRequest,
    db: Session = Depends(get_db),
) -> TokenResponse:
    enforce_auth_rate_limit(
        request=request,
        email=user.email,
    )

    db_user = (
        db.query(User)
        .filter(User.email == user.email)
        .first()
    )

    if db_user is None:
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password",
        )

    if not verify_password(
        user.password,
        db_user.hashed_password,
    ):
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password",
        )

    access_token = create_access_token(
        user_id=db_user.id,
        role=db_user.role,
    )

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
    )
