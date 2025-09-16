# ==usuarios/modelos.py #009
from typing import Optional

class Usuario:
    def __init__(
        self,
        id_usuario: int,
        nombre_completo: str,
        email: str,
        contraseña_hash: str,
        id_rol: int,
        id_entidad: Optional[int] = None,
        activo: bool = True,
    ):
        self.id_usuario = id_usuario
        self.nombre_completo = nombre_completo
        self.email = email
        self.contraseña_hash = contraseña_hash
        self.id_rol = id_rol
        self.id_entidad = id_entidad
        self.activo = activo

    @classmethod
    def desde_fila_db(cls, fila):
        """Crea una instancia de Usuario desde una fila de la base de datos."""
        if fila is None:
            return None
        return cls(
            id_usuario=fila[0],
            nombre_completo=fila[1],
            email=fila[2],
            contraseña_hash=fila[3],
            id_rol=fila[4],
            id_entidad=fila[5],
            activo=bool(fila[6]),
        )
