# ==usuarios/crud.py #010
import sqlite3
from typing import Optional
from usuarios.modelos import Usuario

DB_NAME = "cafehnd.db"

def crear_usuario(nombre: str, email: str, contraseña_hash: str, id_rol: int, id_entidad: int = None) -> bool:
    """Crea un nuevo usuario en la base de datos."""
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO usuarios (nombre_completo, email, contraseña_hash, id_rol, id_entidad)
            VALUES (?, ?, ?, ?, ?)
        """, (nombre, email, contraseña_hash, id_rol, id_entidad))
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        # El email ya existe
        return False
    except Exception as e:
        print(f"Error al crear usuario: {e}")
        return False

def obtener_usuario_por_email(email: str) -> Optional[Usuario]:
    """Busca un usuario por su email."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM usuarios WHERE email = ?", (email,))
    fila = cursor.fetchone()
    conn.close()
    return Usuario.desde_fila_db(fila)

def obtener_usuario_por_id(id_usuario: int) -> Optional[Usuario]:
    """Busca un usuario por su ID."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM usuarios WHERE id_usuario = ?", (id_usuario,))
    fila = cursor.fetchone()
    conn.close()
    return Usuario.desde_fila_db(fila)
