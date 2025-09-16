# ==auth/registro.py #005 (Versión actualizada)
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, EmailStr
from typing import Optional
import sqlite3
from datetime import datetime

# Asumimos que DB_NAME está definido en un lugar común o lo definimos aquí
# En una implementación más avanzada, esto debería venir de config/settings.py
DB_NAME = "cafehnd.db"

router = APIRouter(prefix="/registro", tags=["Registro"])

# Modelo para la solicitud de acceso de exportador
class SolicitudAccesoExportador(BaseModel):
    nombre_completo: str
    email_corporativo: str # EmailStr para validación más estricta
    nombre_exportadora: str
    clave_exportador: str # Clave/Licencia otorgada por IHCAFE
    cargo_relacion: Optional[str] = None # Ej: "Gerente", "Contador", "Operaciones"
    telefono_contacto: Optional[str] = None

# Endpoint para solicitar acceso
@router.post("/solicitar_acceso", status_code=status.HTTP_201_CREATED)
def solicitar_acceso_exportador(solicitud: SolicitudAccesoExportador):
    """
    Endpoint para que un representante autorizado de una exportadora
    registrada en IHCAFE solicite acceso al sistema CaféHND Digital.
    La solicitud se guarda en la tabla 'solicitudes_registro' para ser
    verificada y aprobada por el equipo de CaféHND.
    """
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        
        # Verificar si ya existe una solicitud con ese email
        cursor.execute(
            "SELECT id_solicitud FROM solicitudes_registro WHERE email = ?",
            (solicitud.email_corporativo,)
        )
        if cursor.fetchone():
            raise HTTPException(
                status_code=400,
                detail="Ya existe una solicitud de acceso con ese email corporativo."
            )
        
        # Verificar si ya existe un usuario con ese email (seguridad adicional)
        cursor.execute(
            "SELECT id_usuario FROM usuarios WHERE email = ?",
            (solicitud.email_corporativo,)
        )
        if cursor.fetchone():
            raise HTTPException(
                status_code=400,
                detail="Ya existe un usuario registrado con ese email corporativo."
            )

        # Insertar la nueva solicitud
        # Ahora incluimos clave_exportador en su columna específica
        cursor.execute('''
            INSERT INTO solicitudes_registro 
            (nombre_completo, email, nombre_organizacion, tipo_entidad_solicitada, 
             clave_exportador, mensaje_solicitud, fecha_solicitud, estado)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            solicitud.nombre_completo,
            solicitud.email_corporativo,
            solicitud.nombre_exportadora,
            'EXPORTADOR', # Fijamos este valor según nuestro flujo
            solicitud.clave_exportador, # Valor específico
            f"Solicitud de acceso para {solicitud.nombre_exportadora} (Clave: {solicitud.clave_exportador}). "
            f"Cargo/Relación: {solicitud.cargo_relacion or 'No especificado'}. "
            f"Teléfono: {solicitud.telefono_contacto or 'No proporcionado'}.",
            datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'PENDIENTE' # Estado inicial
        ))
        
        conn.commit()
        conn.close()
        
        return {
            "mensaje": "✅ Solicitud de acceso enviada exitosamente. "
                       "Nuestro equipo la revisará y se comunicará con usted al correo proporcionado."
        }
        
    except sqlite3.IntegrityError as e:
        raise HTTPException(
            status_code=400,
            detail="Error de integridad en la base de datos: " + str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail="Error interno del servidor al procesar la solicitud: " + str(e)
       )

