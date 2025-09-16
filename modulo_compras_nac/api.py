# ==modulo_compras_nac/api.py #023
from fastapi import APIRouter, HTTPException, status, UploadFile, File, Form
import sqlite3
from datetime import date, datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
import os
import uuid

from config.settings import DB_NAME

router = APIRouter(prefix="/compras_nacionales", tags=["Compras Nacionales - Exportador"])

# --- Modelos Pydantic ---

class CompraBase(BaseModel):
    """Modelo base para una compra nacional."""
    fecha_compra: date
    id_intermediario: Optional[int] = None
    id_productor: Optional[int] = None
    tipo_cafe: str # Debe ser uno de los valores permitidos en la BD
    numero_sacos: int
    precio_por_saco: Optional[float] = None
    numero_comprobante: Optional[str] = None
    numero_constancia_venta: Optional[str] = None
    observaciones: Optional[str] = None

class CompraCreate(CompraBase):
    """Modelo para crear una nueva compra."""
    # Puede requerir que algunos campos sean obligatorios dependiendo de la lógica de negocio
    pass

class Compra(CompraBase):
    """Modelo para representar una compra existente."""
    id_compra: int
    id_exportador: int # Este se obtendrá del token/usuario autenticado
    fecha_registro: str # ISO string
    peso_kg: float # Campo calculado
    precio_total: float # Campo calculado
    retencion_lps: float # Campo calculado
    numero_constancia_compra: str # Campo generado por el sistema
    ruta_archivo_comprobante: Optional[str] = None
    ruta_archivo_constancia_venta: Optional[str] = None
    estado: str

    class Config:
        from_attributes = True

# --- Funciones Auxiliares ---

def generar_numero_constancia():
    """Genera un número único para la constancia de compra."""
    # Puedes usar un UUID acortado o un contador secuencial por exportador/año
    # Por simplicidad, usamos un UUID4 truncado
    return f"CC-{uuid.uuid4().hex[:8].upper()}"

# --- Endpoints ---

@router.post("/", response_model=Compra, status_code=status.HTTP_201_CREATED)
def registrar_compra(compra: CompraCreate): # , usuario_actual: Usuario = Depends(get_exportador_actual) # Para proteger
    """
    Registra una nueva compra nacional de café.
    (Por ahora, simulamos que cualquier usuario puede hacerlo, o lo protegemos más adelante).
    """
    try:
        conn = sqlite3.connect(DB_NAME)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # TODO: Obtener el id_exportador del usuario autenticado
        # id_exportador = usuario_actual.id_usuario # O id_entidad
        # Por ahora, lo simulamos como 1 (ajusta según tu prueba)
        id_exportador_simulado = 1 

        # Preparar datos para la inserción
        datos = compra.dict()
        datos['id_exportador'] = id_exportador_simulado
        datos['numero_constancia_compra'] = generar_numero_constancia()
        # peso_kg, precio_total, retencion_lps se calculan en la BD
        
        campos = list(datos.keys())
        valores = tuple(datos.values())
        placeholders = ', '.join(['?' for _ in campos])
        campos_str = ', '.join(campos)
        
        sql = f"""
            INSERT INTO compras_nacionales_exportador 
            ({campos_str})
            VALUES ({placeholders})
        """
        cursor.execute(sql, valores)
        conn.commit()
        
        # Obtener el registro recién creado
        id_nuevo = cursor.lastrowid
        cursor.execute("SELECT * FROM compras_nacionales_exportador WHERE id_compra = ?", (id_nuevo,))
        nuevo_registro = cursor.fetchone()
        
        conn.close()
        
        if nuevo_registro:
            return Compra(**dict(nuevo_registro))
        else:
            raise HTTPException(status_code=500, detail="Error al recuperar el registro creado.")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al registrar la compra: {str(e)}")


@router.get("/", response_model=List[Compra])
def listar_compras(skip: int = 0, limit: int = 100): # , usuario_actual: Usuario = Depends(get_exportador_actual)
    """
    Lista las compras nacionales registradas por el exportador.
    """
    try:
        conn = sqlite3.connect(DB_NAME)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # TODO: Filtrar por id_exportador del usuario autenticado
        # id_exportador = usuario_actual.id_usuario
        # Por ahora, simulamos
        id_exportador_simulado = 1
        
        cursor.execute("""
            SELECT * FROM compras_nacionales_exportador
            WHERE id_exportador = ?
            ORDER BY fecha_compra DESC
            LIMIT ? OFFSET ?
        """, (id_exportador_simulado, limit, skip))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [Compra(**dict(row)) for row in rows]
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al listar compras: {str(e)}")


@router.get("/por_fecha/{fecha}", response_model=List[Compra])
def listar_compras_por_fecha(fecha: date): # , usuario_actual: Usuario = Depends(get_exportador_actual)
    """
    Lista las compras nacionales registradas para una fecha específica.
    """
    try:
        conn = sqlite3.connect(DB_NAME)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # TODO: Filtrar por id_exportador del usuario autenticado
        id_exportador_simulado = 1
        
        cursor.execute("""
            SELECT * FROM compras_nacionales_exportador
            WHERE id_exportador = ? AND fecha_compra = ?
            ORDER BY fecha_registro DESC
        """, (id_exportador_simulado, fecha.isoformat()))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [Compra(**dict(row)) for row in rows]
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al listar compras por fecha: {str(e)}")


@router.get("/{id_compra}", response_model=Compra)
def obtener_detalle_compra(id_compra: int): # , usuario_actual: Usuario = Depends(get_exportador_actual)
    """
    Obtiene el detalle de una compra nacional específica.
    """
    try:
        conn = sqlite3.connect(DB_NAME)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # TODO: Verificar que la compra pertenece al exportador
        # id_exportador = usuario_actual.id_usuario
        
        cursor.execute("""
            SELECT * FROM compras_nacionales_exportador
            WHERE id_compra = ?
        """, (id_compra,))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return Compra(**dict(row))
        else:
            raise HTTPException(status_code=404, detail="Compra no encontrada.")
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener detalle de la compra: {str(e)}")


# (Opcional) Endpoint para subir archivos (comprobante, constancia)
UPLOAD_FOLDER = "uploads/comprobantes"
os.makedirs(UPLOAD_FOLDER, exist_ok=True) # Crear carpeta si no existe

@router.post("/subir_documento/{id_compra}")
def subir_documento_compra(
    id_compra: int,
    archivo: UploadFile = File(...),
    tipo_documento: str = Form(...) # 'comprobante' o 'constancia_venta'
): # , usuario_actual: Usuario = Depends(get_exportador_actual)
    """
    Sube un archivo (PDF/JPG) asociado a una compra.
    """
    try:
        # TODO: Verificar que la compra pertenece al exportador
        
        # Generar nombre único para el archivo
        extension = os.path.splitext(archivo.filename)[1]
        nombre_archivo = f"{tipo_documento}_{id_compra}_{uuid.uuid4().hex}{extension}"
        ruta_completa = os.path.join(UPLOAD_FOLDER, nombre_archivo)

        # Guardar el archivo
        with open(ruta_completa, "wb+") as file_object:
            file_object.write(archivo.file.read())

        # Actualizar la base de datos con la ruta del archivo
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        campo_actualizar = "ruta_archivo_comprobante" if tipo_documento == "comprobante" else "ruta_archivo_constancia_venta"
        cursor.execute(f"""
            UPDATE compras_nacionales_exportador
            SET {campo_actualizar} = ?
            WHERE id_compra = ?
        """, (ruta_completa, id_compra))
        conn.commit()
        conn.close()

        return {"mensaje": f"Documento '{tipo_documento}' subido exitosamente.", "ruta": ruta_completa}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al subir el documento: {str(e)}")

