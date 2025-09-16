# ==usuarios/rutas.py #011
from fastapi import APIRouter

router = APIRouter(prefix="/usuarios", tags=["Usuarios"])

@router.get("/prueba")
def prueba_usuarios():
    return {"mensaje": "✅ Módulo de Usuarios cargado correctamente"}
