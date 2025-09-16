# ==auth/login.py #004 (Versión actualizada)
from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel
from usuarios.crud import obtener_usuario_por_email
from auth.seguridad import verify_password, crear_token_acceso

router = APIRouter(prefix="/login", tags=["Autenticación"])

class CredencialesLogin(BaseModel):
    email: str
    contraseña: str

@router.post("/", status_code=status.HTTP_200_OK)
def login_usuario(credenciales: CredencialesLogin):
    usuario = obtener_usuario_por_email(credenciales.email)
    if not usuario or not verify_password(credenciales.contraseña, usuario.contraseña_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales incorrectas",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Crear token de acceso
    token_data = {"sub": str(usuario.id_usuario), "email": usuario.email, "rol_id": str(usuario.id_rol)}
    token = crear_token_acceso(token_data)
    
    return {"mensaje": "✅ Login exitoso", "token": token, "token_type": "bearer"}
