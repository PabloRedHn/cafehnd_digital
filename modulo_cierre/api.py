# ==modulo_cierre/api.py #021
from fastapi import APIRouter, HTTPException, status, Depends
import sqlite3
from datetime import date, datetime # Para manejar fechas
from typing import List, Optional, Dict, Any
from pydantic import BaseModel

from config.settings import DB_NAME
# from usuarios.modelos import Usuario  # Descomentar si se protege el endpoint
# from auth.seguridad import get_admin_ihcafe_actual # Descomentar si se protege el endpoint

# --- Creación del Router ---
router = APIRouter(prefix="/cierre_ny_bch", tags=["Cierre NY ICE y Tasa BCH"])
# -------------------------

# --- Modelos Pydantic ---

class CierreBase(BaseModel):
    """Modelo base para datos de cierre."""
    fecha: date
    precio_usd_saco: Optional[float] = None
    tasa_cambio_bch: Optional[float] = None
    
    # Posiciones ICE - Precios de Cierre (Close#)
    precio_posicion_dic24: Optional[float] = None
    precio_posicion_mar25: Optional[float] = None
    precio_posicion_may25: Optional[float] = None
    precio_posicion_jul25: Optional[float] = None
    precio_posicion_sep25: Optional[float] = None
    precio_posicion_dic25: Optional[float] = None
    precio_posicion_mar26: Optional[float] = None
    precio_posicion_may26: Optional[float] = None
    precio_posicion_jul26: Optional[float] = None
    precio_posicion_sep26: Optional[float] = None
    
    fuente_precio: Optional[str] = "ICE Futures"
    fuente_tasa: Optional[str] = "Banco Central de Honduras"

class CierreCreate(CierreBase):
    """Modelo para crear un nuevo registro de cierre."""
    pass

class Cierre(CierreBase):
    """Modelo para representar un registro de cierre existente."""
    id_registro: int
    fecha_registro: str # ISO string

    class Config:
        from_attributes = True # Para compatibilidad con datos de la BD

# --- Endpoints ---

@router.get("/ultimo", response_model=Optional[Cierre])
def obtener_ultimo_cierre():
    """
    Obtiene el último registro de cierre ingresado.
    Útil para que los exportadores vean la información más reciente.
    """
    try:
        conn = sqlite3.connect(DB_NAME)
        conn.row_factory = sqlite3.Row # Permite acceder a columnas por nombre
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM cierre_ny_ice_bch
            ORDER BY fecha DESC
            LIMIT 1
        """)
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return Cierre(**dict(row))
        else:
            return None # O podrías devolver un 404 si prefieres
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener el último cierre: {str(e)}")


@router.get("/por_fecha/{fecha}", response_model=Optional[Cierre])
def obtener_cierre_por_fecha(fecha: date):
    """
    Obtiene el registro de cierre para una fecha específica.
    Formato de fecha: YYYY-MM-DD
    """
    try:
        conn = sqlite3.connect(DB_NAME)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Asegurarse de que la fecha esté en formato string 'YYYY-MM-DD'
        fecha_str = fecha.isoformat() 
        
        cursor.execute("""
            SELECT * FROM cierre_ny_ice_bch
            WHERE fecha = ?
        """, (fecha_str,))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return Cierre(**dict(row))
        else:
            return None # O 404
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener cierre para {fecha}: {str(e)}")


@router.post("/", response_model=Cierre, status_code=status.HTTP_201_CREATED)
# def crear_o_actualizar_cierre(cierre: CierreCreate, admin: Usuario = Depends(get_admin_ihcafe_actual)): # <- Para proteger
def crear_o_actualizar_cierre(cierre: CierreCreate): # <- Para pruebas sin autenticación
    """
    Crea un nuevo registro de cierre o lo actualiza si la fecha ya existe.
    """
    try:
        conn = sqlite3.connect(DB_NAME)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Preparar los campos y valores para la consulta SQL
        campos = [
            "fecha", "precio_usd_saco", "tasa_cambio_bch",
            "precio_posicion_dic24", "precio_posicion_mar25", "precio_posicion_may25",
            "precio_posicion_jul25", "precio_posicion_sep25", "precio_posicion_dic25",
            "precio_posicion_mar26", "precio_posicion_may26", "precio_posicion_jul26",
            "precio_posicion_sep26", "fuente_precio", "fuente_tasa"
        ]
        
        valores = (
            cierre.fecha.isoformat(),
            cierre.precio_usd_saco,
            cierre.tasa_cambio_bch,
            cierre.precio_posicion_dic24,
            cierre.precio_posicion_mar25,
            cierre.precio_posicion_may25,
            cierre.precio_posicion_jul25,
            cierre.precio_posicion_sep25,
            cierre.precio_posicion_dic25,
            cierre.precio_posicion_mar26,
            cierre.precio_posicion_may26,
            cierre.precio_posicion_jul26,
            cierre.precio_posicion_sep26,
            cierre.fuente_precio,
            cierre.fuente_tasa
        )
        
        placeholders = ", ".join(["?" for _ in campos])
        campos_str = ", ".join(campos)
        
        # Usar INSERT ... ON CONFLICT para crear o actualizar
        # NOTA: Esto requiere que 'fecha' tenga una restricción UNIQUE o sea PRIMARY KEY
        sql = f"""
            INSERT INTO cierre_ny_ice_bch 
            ({campos_str})
            VALUES ({placeholders})
            ON CONFLICT(fecha) DO UPDATE SET
        """
        # Construir la parte SET del UPDATE, excluyendo 'fecha'
        set_parts = [f"{campo} = excluded.{campo}" for campo in campos if campo != "fecha"]
        sql += ", ".join(set_parts)
        # Actualizar siempre la fecha de registro
        sql += ", fecha_registro = CURRENT_TIMESTAMP" 
        
        cursor.execute(sql, valores)
        conn.commit()
        
        # Recuperar el registro creado o actualizado
        cursor.execute("SELECT * FROM cierre_ny_ice_bch WHERE fecha = ?", (cierre.fecha.isoformat(),))
        nuevo_registro = cursor.fetchone()
        
        conn.close()
        
        if nuevo_registro:
            return Cierre(**dict(nuevo_registro))
        else:
            raise HTTPException(status_code=500, detail="Error al recuperar el registro creado/actualizado.")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al crear/actualizar cierre: {str(e)}")


# (Opcional) Endpoint para listar un rango de cierres, útil para reportes
@router.get("/", response_model=List[Cierre])
def listar_cierres(skip: int = 0, limit: int = 100):
    """
    Lista los registros de cierre, con paginación básica.
    """
    try:
        conn = sqlite3.connect(DB_NAME)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM cierre_ny_ice_bch
            ORDER BY fecha DESC
            LIMIT ? OFFSET ?
        """, (limit, skip))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [Cierre(**dict(row)) for row in rows]
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al listar cierres: {str(e)}")

