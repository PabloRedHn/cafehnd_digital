# ==auth/seguridad.py #006
from passlib.context import CryptContext
import jwt
from datetime import datetime, timedelta
from config.settings import SECRET_KEY, ALGORITHM

# --- Importaciones para la nueva función de seguridad ---
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer # <-- Importar OAuth2PasswordBearer
from jose import JWTError, jwt
# Asumimos que tienes un CRUD para obtener usuarios
from usuarios.crud import obtener_usuario_por_id
from usuarios.modelos import Usuario
# ---

# Configuración para hash de contraseñas
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# --- Definición de oauth2_scheme (DEBE estar antes de usarla) ---
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")
# ---------------------------------------------------------------

def hash_password(password: str) -> str:
    """Genera un hash seguro de la contraseña."""
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifica si una contraseña coincide con su hash."""
    return pwd_context.verify(plain_password, hashed_password)

def crear_token_acceso(data: dict):
    """Genera un JWT para el usuario."""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=30)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


# --- Nueva función de dependencia para verificar rol admin_ihcafe ---

async def get_admin_ihcafe_actual(token: str = Depends(oauth2_scheme)):
    """
    Dependencia de FastAPI para verificar que el usuario actual:
    1. Tiene un token JWT válido.
    2. El token no ha expirado.
    3. El ID de usuario en el token corresponde a un usuario real.
    4. El usuario tiene el rol 'admin_ihcafe' (id_rol = 1).
    
    Si todo es correcto, devuelve el objeto Usuario.
    Si hay algún problema, lanza una excepción HTTP 401 o 403.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No se pudieron validar las credenciales",
        headers={"WWW-Authenticate": "Bearer"},
    )
    forbidden_exception = HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Se requiere rol de administrador de IHCAFE",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        # 1. Verificar y decodificar el token
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
        # Puedes verificar otros claims aquí si es necesario, como expiración
        
    except JWTError:
        raise credentials_exception

    # 2. Obtener el usuario de la base de datos
    usuario = obtener_usuario_por_id(int(user_id)) # Asumimos que obtener_usuario_por_id existe y devuelve un objeto Usuario o None
    if usuario is None:
        raise credentials_exception
        
    # 3. Verificar que el usuario esté activo
    if not usuario.activo:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Usuario inactivo"
        )
        
    # 4. Verificar el rol
    # Asumimos que el rol 'admin_ihcafe' tiene id_rol = 1
    # O podríamos verificar por nombre_rol directamente si es más seguro
    if usuario.id_rol != 1: # id_rol para 'admin_ihcafe'
        raise forbidden_exception
        
    # Si todo pasó, devolvemos el usuario
    return usuario

