from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from ..database import get_db
from ..models.user import User
from ..schemas.user import (
    User as UserSchema,
    UserLogin,
    FirebaseLoginRequest,
)
from sqlalchemy.future import select

from app.services.firebase_auth import (
    FirebaseAuthError,
    get_verified_phone_from_claims,
    verify_firebase_id_token,
)

router = APIRouter(
    prefix="/users",
    tags=["users"]
)


def _get_or_create_user(*, db: Session, user_data: UserLogin) -> User:
    db_user = db.query(User).filter(User.phone == user_data.phone).first()
    if db_user:
        return db_user

    new_user = User(
        phone=user_data.phone,
        full_name=user_data.full_name or "New User",
        location_name=user_data.location_name,
        location_district=user_data.location_district,
        location_state=user_data.location_state,
        weather_alert=True,
        pest_alert=True,
        market_update=False,
        notification_alert=True,
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


def _extract_bearer_token(authorization: str | None) -> str:
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing Authorization header")
    parts = authorization.split(" ", 1)
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(status_code=401, detail="Authorization must be 'Bearer <token>'")
    return parts[1].strip()


@router.post("/firebase/login", response_model=UserSchema)
def firebase_login(
    payload: FirebaseLoginRequest,
    authorization: str | None = Header(default=None, alias="Authorization"),
    db: Session = Depends(get_db),
):
    """Login/signup using Firebase Phone Authentication.

    Client flow:
      1) Client performs Firebase Phone OTP verification.
      2) Client sends Firebase ID token in Authorization header.
      3) Backend verifies token and uses verified phone_number as user identity.
    """

    token = _extract_bearer_token(authorization)
    try:
        claims = verify_firebase_id_token(token)
        phone = get_verified_phone_from_claims(claims)
    except FirebaseAuthError as exc:
        raise HTTPException(status_code=401, detail=str(exc))

    user_data = UserLogin(
        phone=phone,
        full_name=payload.full_name or "New User",
        location_name=payload.location_name,
        location_district=payload.location_district,
        location_state=payload.location_state,
    )
    return _get_or_create_user(db=db, user_data=user_data)

@router.post("/login", response_model=UserSchema)
def login_or_register(user_data: UserLogin, db: Session = Depends(get_db)):
    return _get_or_create_user(db=db, user_data=user_data)

@router.get("/check/{phone}", response_model=UserSchema)
def check_user_exists(phone: str, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.phone == phone).first()
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user

@router.get("/{user_id}", response_model=UserSchema)
def get_user(user_id: int, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.id == user_id).first()
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user
