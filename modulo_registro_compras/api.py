# === modulo_registro_compras/api.py (Versión Corregida, Completa y con Tasa de Cambio) ===
from fastapi import APIRouter, HTTPException, status, Query
import sqlite3
from datetime import date
from typing import List, Optional
from pydantic import BaseModel
from config.settings import DB_NAME

router = APIRouter(prefix="/registro_compras_nac", tags=["Registro Compras Nacionales (Resumen)"])

# --- Modelos Pydantic ---

class RegistroCompraBase(BaseModel):
    """Modelo base para un registro resumido de compra nacional."""
    reg_compa: Optional[str] = None
    registro: Optional[str] = None
    exp_qic: Optional[str] = None
    cosecha: Optional[str] = None
    fecha: date
    sacos46l: float
    valorlemp: float
    sacos46c: float
    valorelemp: float
    clase: str
    sede: Optional[str] = None
    nuevo_acumulado_sacos: Optional[float] = None
    observaciones: Optional[str] = None

class RegistroCompraCreate(RegistroCompraBase):
    """Modelo para crear un nuevo registro resumido de compra."""
    pass

class RegistroCompra(RegistroCompraBase):
    """Modelo para representar un registro resumido de compra existente."""
    id_registro: int
    este_registro_sacos: float
    fecha_registro: str

    class Config:
        from_attributes = True

# === 02 - Modelo para la Respuesta del Próximo Número de Reporte ===
class ProximoRegCompaResponse(BaseModel):
    proximo_reg_compa: str

# === 04 - Modelo para Datos de Registro desde el Frontend (Agrupado) ===
class RegistroCompraFrontendCreate(BaseModel):
    """Modelo para recibir datos de registro desde el frontend, que incluye ambos tipos de café."""
    fecha: date
    exp_qic: str
    cosecha: str
    sacos46l: float
    valorlemp: float
    sacos46c: float
    valorelemp: float
    sede: Optional[str] = None
    nuevo_acumulado_sacos: Optional[float] = None
    observaciones: Optional[str] = None

# === 07 - Modelo para la Respuesta del Detalle de Pago ===
class DetallePagoResponse(BaseModel):
    total_sacos: float
    tasa_cambio_usd_hnl: float
    detalle_pago_calculado: float

# --- Funciones de Utilidad ---

def obtener_tasa_cambio(fecha: date, conn: sqlite3.Connection) -> float:
    """
    Obtiene la tasa de cambio USD a HNL para una fecha específica desde la tabla cierre_ny_ice_bch.
    """
    cursor = conn.cursor()
    cursor.execute("SELECT tasa_cambio_bch FROM cierre_ny_ice_bch WHERE strftime('%Y-%m-%d', fecha_cierre) = ?", (fecha.isoformat(),))
    row = cursor.fetchone()
    if row and row[0] is not None:
        return float(row[0])
    else:
        raise HTTPException(status_code=400, detail=f"No se encontró una tasa de cambio para la fecha {fecha} en la tabla cierre_ny_ice_bch.")

# --- Endpoints ---

# === 03 - Endpoint para Obtener el Próximo Número de Reporte ===
@router.get("/proximo_reg_compa", response_model=ProximoRegCompaResponse)
def obtener_proximo_reg_compa(exp_qic: str = Query(..., description="Código del exportador (exp_qic)")):
    """
    Obtiene el próximo número de reporte (reg_compa) con formato 'NNNN/EXP_QIC'.
    El número secuencial (NNNN) se incrementa basado en el último registro existente.
    """
    try:
        conn = sqlite3.connect(DB_NAME)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("SELECT MAX(CAST(registro AS INTEGER)) as max_registro FROM registro_compras_nacionales")
        row = cursor.fetchone()
        ultimo_numero_global = row['max_registro'] if row['max_registro'] is not None else 0
        proximo_numero_global = ultimo_numero_global + 1
        
        proximo_reg_compa_formateado = f"{proximo_numero_global:04d}/{exp_qic}"
        
        conn.close()
        return ProximoRegCompaResponse(proximo_reg_compa=proximo_reg_compa_formateado)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener el próximo número de reporte: {str(e)}")

# === 06 - Endpoint para Cargar Datos por Fecha y Exportador ===
@router.get("/por_fecha", response_model=List[RegistroCompra])
def obtener_registros_por_fecha(
    fecha: date = Query(..., description="Fecha del reporte"),
    exp_qic: str = Query(..., description="Código del exportador (exp_qic)")
):
    """
    Obtiene los registros (Lavado y Corriente) para una fecha y exportador específicos.
    """
    try:
        conn = sqlite3.connect(DB_NAME)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM registro_compras_nacionales
            WHERE fecha = ? AND exp_qic = ?
            ORDER BY clase
        """, (fecha.isoformat(), exp_qic))
        
        rows = cursor.fetchall()
        conn.close()
        
        if not rows:
            raise HTTPException(status_code=404, detail="No se encontraron registros para la fecha y exportador proporcionados.")
            
        return [RegistroCompra(**dict(row)) for row in rows]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener registros por fecha: {str(e)}")

# === 08 - Endpoint para Calcular Detalle de Pago ===
@router.post("/calcular_detalle_pago", response_model=DetallePagoResponse)
def calcular_detalle_pago(registro_frontend: RegistroCompraFrontendCreate):
    """
    Calcula el detalle de pago basado en el total de sacos y la tasa de cambio para la fecha.
    Formula: (sacos46l + sacos46c) * 10.50 * tasa_cambio_usd_hnl
    """
    try:
        conn = sqlite3.connect(DB_NAME)
        conn.row_factory = sqlite3.Row
        
        total_sacos = registro_frontend.sacos46l + registro_frontend.sacos46c
        tasa_cambio = obtener_tasa_cambio(registro_frontend.fecha, conn)
        detalle_pago = total_sacos * 10.50 * tasa_cambio
        
        conn.close()
        return DetallePagoResponse(
            total_sacos=total_sacos,
            tasa_cambio_usd_hnl=tasa_cambio,
            detalle_pago_calculado=detalle_pago
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al calcular el detalle de pago: {str(e)}")

# === 05 - Endpoint POST Modificado para Manejar Datos del Frontend y Tasa de Cambio ===
@router.post("/", response_model=dict, status_code=status.HTTP_201_CREATED)
def crear_registro_compra_agrupado(registro_frontend: RegistroCompraFrontendCreate):
    """
    Crea registros resumidos de compra nacional para Lavado y/o Corriente desde datos agrupados del frontend.
    Calcula 'este_registro_sacos' y genera 'reg_compa' y 'registro' automáticamente.
    Valida la existencia de la tasa de cambio antes de guardar.
    """
    try:
        conn = sqlite3.connect(DB_NAME)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # --- Validación de Tasa de Cambio (antes de insertar) ---
        try:
            tasa_cambio = obtener_tasa_cambio(registro_frontend.fecha, conn)
        except HTTPException:
            raise # Relanzar el error de tasa de cambio

        # --- 1. Generar reg_compa ---
        cursor.execute("SELECT MAX(CAST(registro AS INTEGER)) as max_registro FROM registro_compras_nacionales")
        row = cursor.fetchone()
        ultimo_numero_global = row['max_registro'] if row['max_registro'] is not None else 0
        proximo_numero_global = ultimo_numero_global + 1
        reg_compa = f"{proximo_numero_global:04d}/{registro_frontend.exp_qic}"
        registro_numero = str(proximo_numero_global)

        # --- 2. Preparar datos comunes ---
        datos_comunes = {
            "reg_compa": reg_compa,
            "registro": registro_numero,
            "exp_qic": registro_frontend.exp_qic,
            "cosecha": registro_frontend.cosecha,
            "fecha": registro_frontend.fecha,
            "sede": registro_frontend.sede,
            "nuevo_acumulado_sacos": registro_frontend.nuevo_acumulado_sacos,
            "observaciones": registro_frontend.observaciones,
        }

        # --- 3. Insertar registros individuales ---
        registros_creados = []
        if registro_frontend.sacos46l > 0 or registro_frontend.valorlemp > 0:
            datos_lavado = {
                **datos_comunes,
                "sacos46l": registro_frontend.sacos46l,
                "valorlemp": registro_frontend.valorlemp,
                "sacos46c": 0.0,
                "valorelemp": 0.0,
                "clase": "Lavado",
                "este_registro_sacos": registro_frontend.sacos46l
            }
            campos = list(datos_lavado.keys())
            valores = tuple(datos_lavado.values())
            placeholders = ', '.join(['?' for _ in campos])
            campos_str = ', '.join(campos)
            sql = f"INSERT INTO registro_compras_nacionales ({campos_str}) VALUES ({placeholders})"
            cursor.execute(sql, valores)
            id_nuevo_lavado = cursor.lastrowid
            cursor.execute("SELECT * FROM registro_compras_nacionales WHERE id_registro = ?", (id_nuevo_lavado,))
            nuevo_registro_lavado_row = cursor.fetchone()
            if nuevo_registro_lavado_row:
                registros_creados.append(dict(nuevo_registro_lavado_row))

        if registro_frontend.sacos46c > 0 or registro_frontend.valorelemp > 0:
            datos_corriente = {
                **datos_comunes,
                "sacos46l": 0.0,
                "valorlemp": 0.0,
                "sacos46c": registro_frontend.sacos46c,
                "valorelemp": registro_frontend.valorelemp,
                "clase": "Corriente",
                "este_registro_sacos": registro_frontend.sacos46c
            }
            campos = list(datos_corriente.keys())
            valores = tuple(datos_corriente.values())
            placeholders = ', '.join(['?' for _ in campos])
            campos_str = ', '.join(campos)
            sql = f"INSERT INTO registro_compras_nacionales ({campos_str}) VALUES ({placeholders})"
            cursor.execute(sql, valores)
            id_nuevo_corriente = cursor.lastrowid
            cursor.execute("SELECT * FROM registro_compras_nacionales WHERE id_registro = ?", (id_nuevo_corriente,))
            nuevo_registro_corriente_row = cursor.fetchone()
            if nuevo_registro_corriente_row:
                 registros_creados.append(dict(nuevo_registro_corriente_row))

        conn.commit()
        conn.close()

        if not registros_creados:
             raise HTTPException(status_code=400, detail="No se proporcionaron datos válidos para Lavado o Corriente.")

        # Calcular el detalle de pago para la respuesta
        total_sacos = registro_frontend.sacos46l + registro_frontend.sacos46c
        detalle_pago = total_sacos * 10.50 * tasa_cambio

        return {
            "mensaje": "Registros creados exitosamente",
            "registros": registros_creados,
            "reg_compa": reg_compa,
            "detalle_pago": {
                "total_sacos": total_sacos,
                "tasa_cambio_usd_hnl": tasa_cambio,
                "detalle_pago_calculado": detalle_pago
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        conn.rollback()
        conn.close()
        raise HTTPException(status_code=500, detail=f"Error al crear los registros de compra: {str(e)}")

# --- Endpoint GET (Listar) existente ---
@router.get("/", response_model=List[RegistroCompra])
def listar_registros_compras(skip: int = 0, limit: int = 100):
    """
    Lista los registros resumidos de compras nacionales.
    """
    try:
        conn = sqlite3.connect(DB_NAME)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM registro_compras_nacionales
            ORDER BY fecha DESC
            LIMIT ? OFFSET ?
        """, (limit, skip))
        rows = cursor.fetchall()
        conn.close()
        return [RegistroCompra(**dict(row)) for row in rows]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al listar registros de compras: {str(e)}")

# --- Endpoint GET (Detalle) existente ---
@router.get("/{id_registro}", response_model=RegistroCompra)
def obtener_detalle_registro_compra(id_registro: int):
    """
    Obtiene el detalle de un registro resumido de compra nacional específico.
    """
    try:
        conn = sqlite3.connect(DB_NAME)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM registro_compras_nacionales
            WHERE id_registro = ?
        """, (id_registro,))
        row = cursor.fetchone()
        conn.close()
        if row:
            return RegistroCompra(**dict(row))
        else:
            raise HTTPException(status_code=404, detail="Registro de compra no encontrado.")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener detalle del registro: {str(e)}")

