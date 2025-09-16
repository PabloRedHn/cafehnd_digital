# ==base_datos/conexion.py #013
import sqlite3
import os

# Nombre de la base de datos
DB_NAME = "cafehnd.db"

def crear_base_datos():
    """Crea la base de datos y las tablas si no existen."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # Tabla: ROLES
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS roles (
            id_rol INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre_rol TEXT UNIQUE NOT NULL,
            nivel INTEGER NOT NULL,
            permisos TEXT
        )
    ''')

    # Tabla: ENTIDADES
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS entidades (
            id_entidad INTEGER PRIMARY KEY AUTOINCREMENT,
            tipo TEXT CHECK(tipo IN ('IHCAFE', 'EXPORTADOR', 'GESTOR')) NOT NULL,
            nombre TEXT NOT NULL,
            direccion TEXT,
            telefono TEXT,
            contacto_principal TEXT
        )
    ''')

    # Tabla: USUARIOS
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS usuarios (
            id_usuario INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre_completo TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            contraseña_hash TEXT NOT NULL,
            id_rol INTEGER NOT NULL,
            id_entidad INTEGER,
            activo BOOLEAN DEFAULT 1,
            fecha_creacion DATETIME DEFAULT CURRENT_TIMESTAMP,
            ultimo_login DATETIME,
            FOREIGN KEY (id_rol) REFERENCES roles(id_rol),
            FOREIGN KEY (id_entidad) REFERENCES entidades(id_entidad)
        )
    ''')

    # Tabla: SOLICITUDES_REGISTRO
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS solicitudes_registro (
            id_solicitud INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre_completo TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            nombre_organizacion TEXT,
            tipo_entidad_solicitada TEXT CHECK(tipo_entidad_solicitada IN ('EXPORTADOR', 'GESTOR')) NOT NULL,
            clave_exportador TEXT, -- Columna añadida
            mensaje_solicitud TEXT,
            fecha_solicitud DATETIME DEFAULT CURRENT_TIMESTAMP,
            estado TEXT DEFAULT 'PENDIENTE' CHECK(estado IN ('PENDIENTE', 'APROBADA', 'RECHAZADA')),
            id_usuario_aprobador INTEGER,
            fecha_respuesta DATETIME,
            FOREIGN KEY (id_usuario_aprobador) REFERENCES usuarios(id_usuario)
        )
    ''')

    # --- Nueva Tabla: CIERRE_NY_ICE_BCH ---
# ==base_datos/conexion.py #013 (Fragmento actualizado)
# ... (resto del código existente: importaciones, DB_NAME, otras tablas) ...

    # --- Nueva Tabla: CIERRE_NY_ICE_BCH (Actualizada con columnas de posiciones) ---
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS cierre_ny_ice_bch (
            id_registro INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha DATE NOT NULL UNIQUE, -- Fecha del cierre/reportado
            
            -- Campos principales
            precio_usd_saco REAL, -- Precio principal por saco en USD (NY ICE)
            tasa_cambio_bch REAL, -- Tasa de cambio Lempiras por Dólar (BCH)
            
            -- Posiciones ICE - Precios de Cierre (Close#)
            precio_posicion_dic24 REAL, -- Diciembre 2024
            precio_posicion_mar25 REAL, -- Marzo 2025
            precio_posicion_may25 REAL, -- Mayo 2025
            precio_posicion_jul25 REAL, -- Julio 2025
            precio_posicion_sep25 REAL, -- Septiembre 2025
            precio_posicion_dic25 REAL, -- Diciembre 2025
            precio_posicion_mar26 REAL, -- Marzo 2026
            precio_posicion_may26 REAL, -- Mayo 2026
            precio_posicion_jul26 REAL, -- Julio 2026
            precio_posicion_sep26 REAL, -- Septiembre 2026
            
            -- Metadatos
            fuente_precio TEXT DEFAULT "ICE Futures", -- Fuente del precio
            fuente_tasa TEXT DEFAULT "Banco Central de Honduras", -- Fuente de la tasa
            fecha_registro DATETIME DEFAULT CURRENT_TIMESTAMP -- Fecha de registro/actualización en el sistema
        )
    ''')

# ==base_datos/conexion.py # Fragmento actualizado ==
# ... (resto del código existente) ...

# ==base_datos/conexion.py # Fragmento actualizado ==
# ... (resto del código existente) ...

    # --- Tabla Reemplazada: REGISTRO_COMPRAS_NACIONALES (Formato de la imagen) ---
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS registro_compras_nacionales (
            id_registro INTEGER PRIMARY KEY AUTOINCREMENT,
            reg_compa TEXT,          -- Número de serie del reporte (ej: '020/048')
            registro TEXT,          -- Número de registro dentro del reporte (ej: '020')
            exp_qic TEXT,            -- Número de Licencia/Registro del Exportador ante OIC
            cosecha TEXT,            -- Año de cosecha (ej: '2024-2025')
            fecha DATE,              -- Fecha del reporte/registro
            sacos46l REAL,           -- Total acumulado anterior de sacos de café lavado
            valorlemp REAL,          -- Valor Lempiras asociado al acumulado anterior (lavado)
            sacos46c REAL,           -- Total acumulado anterior de sacos de café corriente
            valorelemp REAL,         -- Valor Lempiras asociado al acumulado anterior (corriente)
            clase TEXT,              -- Tipo de café (ej: 'LAVADO', 'CORRIENTE')
            sede TEXT,               -- Sede o región de origen
            -- Campos calculados para ESTE REGISTRO (la compra actual que se está registrando)
            este_registro_sacos REAL GENERATED ALWAYS AS (sacos46l + sacos46c) STORED, -- Total sacos en este registro
            -- Campo para el nuevo acumulado total (se calcularía en la aplicación)
            nuevo_acumulado_sacos REAL,
            -- Metadatos
            fecha_registro DATETIME DEFAULT CURRENT_TIMESTAMP,
            observaciones TEXT
        )
    ''')
    # ------------------------------------

# ... (resto del código existente: inserts de roles, entidades, etc.) ...



    # ------------------------------------

# ... (resto del código existente: inserts de roles, entidades, etc.) ...
    # ------------------------------------

    # Insertar roles base (ejemplo)
    roles_base = [
        ('admin_ihcafe', 1, '{"permisos": ["total"]}'),
        ('editor_exportador', 2, '{"permisos": ["editar", "ver"]}'),
        ('basico_gestor', 3, '{"permisos": ["ver"]}')
    ]
    cursor.executemany('''
        INSERT OR IGNORE INTO roles (nombre_rol, nivel, permisos)
        VALUES (?, ?, ?)
    ''', roles_base)

    # Insertar entidad base (IHCAFE como ejemplo)
    cursor.execute('''
        INSERT OR IGNORE INTO entidades (id_entidad, tipo, nombre)
        VALUES (1, 'IHCAFE', 'Instituto Hondureño del Café')
    ''')

    conn.commit()
    conn.close()
    print(f"✅ Base de datos '{DB_NAME}' lista.")

if __name__ == "__main__":
    crear_base_datos()
