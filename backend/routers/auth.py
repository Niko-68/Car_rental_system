from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database import get_db
from models import Address, Customer, User
from schemas import LoginIn, RegisterIn, TokenOut, UserOut, UserUpdate
from security import create_token, get_current_user, hash_password, verify_password

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/register", response_model=TokenOut, status_code=201)
def register(data: RegisterIn, db: Session = Depends(get_db)):
    """Public sign-up: always creates a customer (users + customers rows)."""
    if db.query(User).filter(User.email == data.email).first():
        raise HTTPException(status.HTTP_409_CONFLICT, "Email already registered")
    user = User(name=data.name, last_name=data.last_name, email=data.email,
                password=hash_password(data.password))
    user.customer = Customer(birthdate=data.birthdate)
    if data.address:
        user.address = Address(**data.address.model_dump())
    db.add(user)
    db.commit()
    db.refresh(user)
    return TokenOut(access_token=create_token(user), user=user)


@router.post("/login", response_model=TokenOut)
def login(data: LoginIn, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == data.email).first()
    if not user or not verify_password(data.password, user.password):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid email or password")
    return TokenOut(access_token=create_token(user), user=user)


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)):
    return user


@router.put("/me", response_model=UserOut)
def update_me(data: UserUpdate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    payload = data.model_dump(exclude_unset=True)
    addr = payload.pop("address", None)
    for k, v in payload.items():
        setattr(user, k, v)
    if addr:
        if user.address:
            for k, v in addr.items():
                setattr(user.address, k, v)
        else:
            user.address = Address(**addr)
    db.commit()
    db.refresh(user)
    return user
