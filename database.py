# database.py
import sqlite3
import pandas as pd
from datetime import datetime

DB_NAME = "kamadata.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS trabajadores (
            id INTEGER PRIMARY KEY,
            nombre TEXT NOT NULL
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS produccion (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha TEXT NOT NULL,
            area TEXT NOT NULL,
            empresa TEXT NOT NULL,
            tipo TEXT,
            cantidad INTEGER NOT NULL,
            trabajador_id INTEGER,
            responsable_id INTEGER,
            FOREIGN KEY(trabajador_id) REFERENCES trabajadores(id)
        )
    """)
    conn.commit()
    conn.close()

# trabajadores
def upsert_trabajador(trabajador_id: int, nombre: str):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO trabajadores (id, nombre) VALUES (?, ?)
        ON CONFLICT(id) DO UPDATE SET nombre=excluded.nombre
    """, (trabajador_id, nombre))
    conn.commit()
    conn.close()

def listar_trabajadores():
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("SELECT id, nombre FROM trabajadores ORDER BY nombre")
    rows = cur.fetchall()
    conn.close()
    return rows

# produccion
def agregar_registro(trabajador_id: int, area: str, empresa: str, cantidad: float, 
                     responsable_id: int, cantidad_auxiliar: int = None,
                     tipo: str = None, fecha: str = None):
    if fecha is None:
        fecha = datetime.now().strftime("%Y-%m-%d")
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    
    # Importante: Si la tabla 'produccion' no tiene la columna 'cantidad_auxiliar', esta función fallará
    # a menos que la retire de la lista de columnas y valores.
    # Asumiré la estructura definida anteriormente:
    cur.execute("""
        INSERT INTO produccion (fecha, area, empresa, tipo, cantidad, trabajador_id, responsable_id)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (fecha, area, empresa, tipo, cantidad, trabajador_id, responsable_id))
    
    conn.commit()
    conn.close()

# Reporte 1: Registros por fecha (CORREGIDO)
def obtener_registros_por_fecha(fecha: str):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("""
        SELECT p.fecha, p.area, p.empresa, p.tipo, p.cantidad,
               p.trabajador_id, t.nombre
        FROM produccion p
        LEFT JOIN trabajadores t ON p.trabajador_id = t.id
        WHERE p.fecha = ?
        ORDER BY p.area, p.empresa
    """, (fecha,))
    rows = cur.fetchall()
    conn.close()
    return rows

# Reporte 2: Registros por periodo (CORREGIDO)
def obtener_registros_periodo(fecha_inicio: str, fecha_fin: str):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("""
        SELECT p.fecha, p.area, p.empresa, p.tipo, p.cantidad,
               p.trabajador_id, t.nombre
        FROM produccion p
        LEFT JOIN trabajadores t ON p.trabajador_id = t.id
        WHERE p.fecha BETWEEN ? AND ?
        ORDER BY p.fecha, p.area, p.empresa
    """, (fecha_inicio, fecha_fin))
    rows = cur.fetchall()
    conn.close()
    return rows