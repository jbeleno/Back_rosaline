
from fastapi import APIRouter, Depends, HTTPException, status, Body, Query, Path
from typing import List, Optional
from .. import schemas
from ..services.usuario_service import UsuarioService
from ..core.dependencies import get_usuario_service, get_usuario_repository
from ..auth import get_current_user, require_admin

router = APIRouter(
    prefix="/usuarios",
    tags=["Usuarios"]
)

@router.post("/", summary="Registrar nuevo usuario", status_code=status.HTTP_201_CREATED, response_model=schemas.Usuario)
def crear_usuario(
    usuario: schemas.UsuarioCreate,
    service: UsuarioService = Depends(get_usuario_service)
):
    return service.crear_usuario(usuario)

@router.get("/", summary="Listar usuarios", response_model=List[schemas.Usuario])
def listar_usuarios(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    rol: Optional[str] = Query(None),
    correo: Optional[str] = Query(None),
    email_verificado: Optional[str] = Query(None),
    current_user: dict = Depends(require_admin()),
    service: UsuarioService = Depends(get_usuario_service)
):
    return service.listar_usuarios(skip, limit, rol, correo, email_verificado)

@router.get("/me", summary="Obtener usuario actual")
def leer_usuarios_me(current_user: dict = Depends(get_current_user)):
    return current_user

@router.get("/{usuario_id}", summary="Obtener usuario por ID", response_model=schemas.Usuario)
def obtener_usuario(
    usuario_id: int = Path(..., ge=1),
    current_user: dict = Depends(require_admin()),
    service: UsuarioService = Depends(get_usuario_service)
):
    return service.obtener_usuario(usuario_id)

@router.put("/{usuario_id}", summary="Actualizar usuario", response_model=schemas.Usuario)
def actualizar_usuario(
    usuario_id: int,
    usuario: schemas.UsuarioUpdate,
    current_user: dict = Depends(require_admin()),
    service: UsuarioService = Depends(get_usuario_service)
):
    return service.actualizar_usuario(usuario_id, usuario, current_user)

@router.delete("/{usuario_id}", summary="Eliminar usuario", response_model=schemas.Usuario)
def eliminar_usuario(
    usuario_id: int,
    current_user: dict = Depends(require_admin()),
    service: UsuarioService = Depends(get_usuario_service)
):
    return service.eliminar_usuario(usuario_id, current_user)

# Endpoints de autenticación y recuperación
auth_router = APIRouter(
    prefix="/usuarios",
    tags=["Autenticación"]
)

@auth_router.post("/confirmar-cuenta", summary="Confirmar cuenta con PIN", response_model=schemas.ConfirmarCuentaResponse)
def confirmar_cuenta(
    request: schemas.ConfirmarCuentaRequest,
    service: UsuarioService = Depends(get_usuario_service)
):
    return service.confirmar_cuenta(request.correo, request.pin)

@auth_router.post("/reenviar-confirmacion", summary="Reenviar PIN de confirmación")
def reenviar_confirmacion(
    request: schemas.ReenviarConfirmacionRequest,
    service: UsuarioService = Depends(get_usuario_service)
):
    return service.reenviar_confirmacion(request.correo)

@auth_router.post("/solicitar-recuperacion", summary="Solicitar recuperación de contraseña")
def solicitar_recuperacion(
    request: schemas.SolicitarRecuperacionRequest,
    service: UsuarioService = Depends(get_usuario_service)
):
    return service.solicitar_recuperacion(request.correo)

@auth_router.post("/validar-pin", summary="Validar PIN de recuperación")
def validar_pin(
    request: schemas.ValidarPinRequest,
    service: UsuarioService = Depends(get_usuario_service)
):
    return service.validar_pin_recuperacion(request.correo, request.pin)

@auth_router.post("/cambiar-contraseña", summary="Cambiar contraseña con PIN")
def cambiar_contraseña(
    request: schemas.CambiarContraseñaRequest,
    service: UsuarioService = Depends(get_usuario_service)
):
    return service.cambiar_contraseña_con_pin(request)

@auth_router.post("/cambiar-contraseña-autenticado", summary="Cambiar contraseña (autenticado)")
def cambiar_contraseña_autenticado(
    request: schemas.CambiarContraseñaAutenticadoRequest,
    current_user: dict = Depends(get_current_user),
    service: UsuarioService = Depends(get_usuario_service)
):
    usuario_id = current_user.get("id_usuario")
    return service.cambiar_contraseña_autenticado(usuario_id, request)
