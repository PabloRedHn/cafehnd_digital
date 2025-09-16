# ==main.py #001 (Versión actualizada)
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
# Importar los routers
from usuarios.rutas import router as usuarios_router
from auth.login import router as login_router
from auth.registro import router as registro_router
from admin.solicitudes import router as admin_solicitudes_router
# --- Nuevo import ---
from modulo_cierre.api import router as cierre_router # Importamos el nuevo router
from modulo_compras_nac.api import router as compras_nac_router # Importar el nuevo router
from modulo_registro_compras.api import router as registro_compras_router # Importar el nuevo router

app = FastAPI(title="CaféHND Digital - Sistema de Usuarios, Solicitudes y Cierres")

# Incluir los routers de la API
app.include_router(usuarios_router)
app.include_router(login_router)
app.include_router(registro_router)
app.include_router(admin_solicitudes_router)
app.include_router(registro_compras_router)
# --- Nuevo router ---
app.include_router(cierre_router)

# Servir archivos estáticos desde la carpeta 'static'
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
def inicio():
    return {"mensaje": "🌱 Bienvenido a CaféHND Digital. Visita /static/index.html para la interfaz o /docs para ver la API."}

