from fastapi import APIRouter, Depends, HTTPException, status
from datetime import timedelta

from .. import schemas
from ..services.usuario_service import UsuarioService
from ..core.dependencies import get_usuario_service
from ..auth import crear_token_de_acceso
from ..core.config import get_settings, Settings

router = APIRouter(
    tags=["Autenticación"]
)

@router.post("/login", response_model=schemas.Token)
def login(
    request: schemas.LoginRequest,
    service: UsuarioService = Depends(get_usuario_service),
    settings: Settings = Depends(get_settings)
):
    """
    Inicia sesión para obtener un token de acceso.
    """
    user = service.autenticar_usuario(correo=request.correo, contraseña=request.contraseña)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Correo o contraseña incorrectos",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = crear_token_de_acceso(
        data={"sub": user.correo, "id_usuario": user.id_usuario, "rol": user.rol},
        expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}
