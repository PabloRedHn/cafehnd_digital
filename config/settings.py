# ==config/settings.py #018
import os

# En producción, esto debería venir de una variable de entorno
SECRET_KEY = os.environ.get("SECRET_KEY") or "tu_clave_secreta_super_segura_para_jwt"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# --- Nueva línea añadida ---
DB_NAME = "cafehnd.db"
# --------------------------
