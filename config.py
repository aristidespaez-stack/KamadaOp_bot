# config.py

# Usaremos un set vacío inicialmente. Se recomienda que el ADMIN se incluya al inicio.
# IMPORTANTE: Reemplace 12345 con su ID de Telegram para que funcione la administración.
ADMINISTRADORES = {146814016} 

USUARIOS_AUTORIZADOS = set()

CLAVES_ACCESO = {
    "sardina": "123",
    "mesa": "123",
    "linea": "123",
    "empaque": "123",
    "trabajadores": "123",
    "reportes": "123"
}

EMPRESA_PERMISOS = {
    "pariamar": ["Pariamar"],
    "kamada": ["Kamada", "Pariamar"]
}

def autorizado(user_id: int) -> bool:
    """Verifica si el usuario está en la lista de autorizados o es administrador."""
    return user_id in USUARIOS_AUTORIZADOS or user_id in ADMINISTRADORES

def es_admin(user_id: int) -> bool:
    """Verifica si el usuario es administrador."""
    return user_id in ADMINISTRADORES

def validar_clave(area: str, clave: str) -> bool:
    """Valida la clave de acceso por área."""
    return CLAVES_ACCESO.get(area) == clave

# NUEVAS FUNCIONES para manejar la autorización dinámica:

def agregar_usuario_autorizado(user_id: int):
    """Añade un usuario al conjunto de autorizados."""
    if user_id not in ADMINISTRADORES:
        USUARIOS_AUTORIZADOS.add(user_id)
        # Nota: En un sistema de producción, estos cambios deberían guardarse
        # en un archivo JSON o en la base de datos para persistencia.
        print(f"DEBUG: Usuario {user_id} autorizado. Autorizados actuales: {USUARIOS_AUTORIZADOS}")
        
def remover_usuario_autorizado(user_id: int):
    """Remueve un usuario del conjunto de autorizados."""
    if user_id in USUARIOS_AUTORIZADOS:
        USUARIOS_AUTORIZADOS.remove(user_id)
        print(f"DEBUG: Usuario {user_id} removido. Autorizados actuales: {USUARIOS_AUTORIZADOS}")