from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.db.dependencies import get_db
from app.models.models import User
from app.core.security import create_access_token, hash_password, verify_password
from app.schemas.auth import RegisterRequest, TokenRequest, TokenResponse
from app.api.dependencies import get_current_user, require_role

router = APIRouter(
    prefix="/v1/auth",
    tags=["auth"],
)

# test purpose
@router.get("/me")
def get_me(
    current_user: dict = Depends(get_current_user),
) -> dict:
    return current_user

@router.post("/register", status_code=201)
def register_user(
    user: RegisterRequest,
    db: Session = Depends(get_db),
) -> dict:
    existing_user = db.query(User).filter(User.email == user.email).first()

    if existing_user is not None:
        return {"error": "User already exists"}

    db_user = User(
        id=str(uuid4()),
        email=user.email,
        hashed_password=hash_password(user.password),
        role=user.role,
    )

    db.add(db_user)
    db.commit()

    return {
        "message": "User registered successfully",
        "user_id": db_user.id,
    }

@router.post("/token", response_model=TokenResponse)
def login_user(
    user: TokenRequest,
    db: Session = Depends(get_db),
) -> TokenResponse:
    db_user = db.query(User).filter(User.email == user.email).first()

    if db_user is None:
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password",
        )

    if not verify_password(user.password, db_user.hashed_password):
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