# ==admin/solicitudes.py #019 (Versión actualizada con autenticación real)
from fastapi import APIRouter, HTTPException, status, Depends
import sqlite3
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel

# Importaciones reales
from auth.seguridad import get_admin_ihcafe_actual # Importamos la nueva dependencia
from usuarios.modelos import Usuario # Asegúrate de que este modelo exista
from config.settings import DB_NAME

router = APIRouter(prefix="/admin/solicitudes", tags=["Administración - Solicitudes"])

# --- Modelos Pydantic para respuestas ---

class SolicitudResumen(BaseModel):
    id_solicitud: int
    nombre_completo: str
    email: str
    nombre_organizacion: str
    tipo_entidad_solicitada: str
    fecha_solicitud: str
    estado: str

class SolicitudDetalle(SolicitudResumen):
    clave_exportador: str
    mensaje_solicitud: str
    cargo_relacion: Optional[str] = None
    telefono_contacto: Optional[str] = None

# --- Endpoints ---

@router.get("/pendientes", response_model=List[SolicitudResumen])
def listar_solicitudes_pendientes(admin: Usuario = Depends(get_admin_ihcafe_actual)):
    """
    Endpoint para que un administrador de IHCAFE liste las solicitudes pendientes.
    """
    # ... (resto del código de la función, igual que antes) ...
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id_solicitud, nombre_completo, email, nombre_organizacion, 
                   tipo_entidad_solicitada, fecha_solicitud, estado
            FROM solicitudes_registro
            WHERE estado = 'PENDIENTE'
            ORDER BY fecha_solicitud DESC
        """)
        
        filas = cursor.fetchall()
        conn.close()
        
        solicitudes = [
            SolicitudResumen(
                id_solicitud=row[0],
                nombre_completo=row[1],
                email=row[2],
                nombre_organizacion=row[3],
                tipo_entidad_solicitada=row[4],
                fecha_solicitud=row[5] if isinstance(row[5], str) else datetime.strptime(row[5], '%Y-%m-%d %H:%M:%S').strftime('%Y-%m-%d %H:%M:%S') if row[5] else None,
                estado=row[6]
            )
            for row in filas
        ]
        
        return solicitudes
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error al obtener solicitudes pendientes: {str(e)}"
        )

@router.get("/{id_solicitud}", response_model=SolicitudDetalle)
def obtener_detalle_solicitud(id_solicitud: int, admin: Usuario = Depends(get_admin_ihcafe_actual)):
    """
    Endpoint para obtener los detalles de una solicitud específica.
    """
    # ... (resto del código de la función, igual que antes) ...
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id_solicitud, nombre_completo, email, nombre_organizacion, 
                   tipo_entidad_solicitada, fecha_solicitud, estado, mensaje_solicitud,
                   clave_exportador
            FROM solicitudes_registro
            WHERE id_solicitud = ?
        """, (id_solicitud,))
        
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            raise HTTPException(
                status_code=404,
                detail="Solicitud no encontrada"
            )
        
        return SolicitudDetalle(
            id_solicitud=row[0],
            nombre_completo=row[1],
            email=row[2],
            nombre_organizacion=row[3],
            tipo_entidad_solicitada=row[4],
            fecha_solicitud=row[5] if isinstance(row[5], str) else datetime.strptime(row[5], '%Y-%m-%d %H:%M:%S').strftime('%Y-%m-%d %H:%M:%S') if row[5] else None,
            estado=row[6],
            mensaje_solicitud=row[7],
            clave_exportador=row[8] if row[8] else "No especificada"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error al obtener detalle de la solicitud: {str(e)}"
        )

# Próximamente: @router.post("/{id_solicitud}/aprobar") y @router.post("/{id_solicitud}/rechazar")
# ==admin/solicitudes.py #019 (Versión actualizada con aprobación/rechazo)
# ... (todo el código existente) ...

# --- Nuevos modelos para las solicitudes ---
from pydantic import BaseModel

class RespuestaAprobar(BaseModel):
    mensaje: str
    id_usuario_creado: int

class RespuestaRechazar(BaseModel):
    mensaje: str

class MotivoRechazo(BaseModel):
    motivo: str = "Solicitud rechazada por el administrador de IHCAFE."
# ------------------------------------------

# ... (endpoints existentes: listar_solicitudes_pendientes, obtener_detalle_solicitud) ...

# --- Nuevos Endpoints ---

@router.post("/{id_solicitud}/aprobar", response_model=RespuestaAprobar, status_code=status.HTTP_201_CREATED)
def aprobar_solicitud(id_solicitud: int, admin: Usuario = Depends(get_admin_ihcafe_actual)):
    """
    Endpoint para que un administrador de IHCAFE apruebe una solicitud de acceso.
    Esto crea un usuario en la tabla 'usuarios' y actualiza el estado de la solicitud.
    """
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        
        # 1. Verificar que la solicitud exista y esté pendiente
        cursor.execute("""
            SELECT id_solicitud, nombre_completo, email, nombre_organizacion, clave_exportador
            FROM solicitudes_registro
            WHERE id_solicitud = ? AND estado = 'PENDIENTE'
        """, (id_solicitud,))
        
        solicitud = cursor.fetchone()
        if not solicitud:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Solicitud no encontrada o ya procesada."
            )
        
        # Extraer datos de la solicitud
        _, nombre_completo, email, nombre_organizacion, clave_exportador = solicitud
        
        # 2. Crear una contraseña temporal/hash (en una implementación real, se enviaría un correo para que la establezca)
        # Por ahora, creamos un hash de una contraseña temporal.
        from auth.seguridad import hash_password
        contraseña_temporal = "Temporal123!" # En el futuro, esto debería manejarse mejor
        hash_contraseña_temp = hash_password(contraseña_temporal)
        
        # 3. Crear el usuario en la tabla 'usuarios'
        # Asumimos rol 'editor_exportador' (id_rol=2) por defecto. 
        # En el futuro, se podría parametrizar.
        # Para id_entidad, necesitamos encontrar o crear la entidad exportadora.
        # Por simplicidad, asumimos que existe o creamos una básica.
        
        # Verificar si la entidad (exportadora) ya existe
        cursor.execute("SELECT id_entidad FROM entidades WHERE nombre = ?", (nombre_organizacion,))
        entidad = cursor.fetchone()
        
        id_entidad = None
        if entidad:
            id_entidad = entidad[0]
        else:
            # Crear la entidad si no existe
            cursor.execute("""
                INSERT INTO entidades (tipo, nombre)
                VALUES (?, ?)
            """, ("EXPORTADOR", nombre_organizacion))
            id_entidad = cursor.lastrowid
            
        # Crear el usuario
        cursor.execute("""
            INSERT INTO usuarios (nombre_completo, email, contraseña_hash, id_rol, id_entidad)
            VALUES (?, ?, ?, ?, ?)
        """, (nombre_completo, email, hash_contraseña_temp, 2, id_entidad)) # id_rol=2 -> editor_exportador
        
        id_usuario_creado = cursor.lastrowid
        
        # 4. Actualizar el estado de la solicitud
        cursor.execute("""
            UPDATE solicitudes_registro
            SET estado = 'APROBADA', id_usuario_aprobador = ?, fecha_respuesta = ?
            WHERE id_solicitud = ?
        """, (admin.id_usuario, datetime.now().strftime('%Y-%m-%d %H:%M:%S'), id_solicitud))
        
        conn.commit()
        conn.close()
        
        return RespuestaAprobar(
            mensaje=f"✅ Solicitud aprobada. Usuario '{nombre_completo}' creado con ID {id_usuario_creado}.",
            id_usuario_creado=id_usuario_creado
        )
        
    except HTTPException:
        # Re-lanzar excepciones HTTP ya definidas
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error al aprobar la solicitud: {str(e)}"
        )


@router.post("/{id_solicitud}/rechazar", response_model=RespuestaRechazar)
def rechazar_solicitud(id_solicitud: int, motivo: MotivoRechazo = None, admin: Usuario = Depends(get_admin_ihcafe_actual)):
    """
    Endpoint para que un administrador de IHCAFE rechace una solicitud de acceso.
    """
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        
        # 1. Verificar que la solicitud exista y esté pendiente
        cursor.execute("""
            SELECT id_solicitud FROM solicitudes_registro
            WHERE id_solicitud = ? AND estado = 'PENDIENTE'
        """, (id_solicitud,))
        
        solicitud = cursor.fetchone()
        if not solicitud:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Solicitud no encontrada o ya procesada."
            )
        
        # 2. Actualizar el estado de la solicitud
        motivo_texto = motivo.motivo if motivo else "Solicitud rechazada por el administrador de IHCAFE."
        cursor.execute("""
            UPDATE solicitudes_registro
            SET estado = 'RECHAZADA', id_usuario_aprobador = ?, fecha_respuesta = ?, mensaje_solicitud = ?
            WHERE id_solicitud = ?
        """, (admin.id_usuario, datetime.now().strftime('%Y-%m-%d %H:%M:%S'), motivo_texto, id_solicitud))
        
        conn.commit()
        conn.close()
        
        return RespuestaRechazar(mensaje=f"✅ Solicitud {id_solicitud} rechazada.")
        
    except HTTPException:
        # Re-lanzar excepciones HTTP ya definidas
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error al rechazar la solicitud: {str(e)}"
        )

