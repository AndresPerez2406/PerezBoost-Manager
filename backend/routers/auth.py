from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from backend.core.database import get_db
from backend.core.security import create_access_token, verify_password, get_current_user
from backend.core.config import settings
from backend.models.booster import Booster
from backend.schemas.auth import LoginRequest, TokenResponse, UserProfile

router = APIRouter(prefix="/auth", tags=["Autenticación"])

@router.post("/login", response_model=TokenResponse)
def login(request: LoginRequest, db: Session = Depends(get_db)):
    username = request.username.strip()
    password = request.password.strip()

    # 1. Verificar si es Administrador maestro
    if username.lower() == "admin":
        # Contraseña maestra de admin
        if password in ["perez2026", "admin", "1234"]:
            token = create_access_token(data={"sub": "admin", "role": "admin", "name": "Administrador"})
            return TokenResponse(access_token=token, role="admin", name="Administrador")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales de administrador incorrectas."
        )

    # 2. Verificar si es Booster
    booster = db.query(Booster).filter(Booster.nombre == username).first()
    if not booster:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario o booster no encontrado."
        )

    if not verify_password(password, booster.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Contraseña incorrecta."
        )

    token = create_access_token(data={"sub": str(booster.id), "role": "booster", "name": booster.nombre})
    return TokenResponse(access_token=token, role="booster", name=booster.nombre)

@router.get("/me", response_model=UserProfile)
def get_me(current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    role = current_user.get("role")
    name = current_user.get("name")
    
    if role == "admin":
        return UserProfile(name=name, role=role)
    
    booster = db.query(Booster).filter(Booster.nombre == name).first()
    if booster:
        return UserProfile(
            name=booster.nombre,
            role="booster",
            discord_id=booster.discord_id,
            binance=booster.binance
        )
    return UserProfile(name=name, role=role)
