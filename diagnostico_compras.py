import sqlite3
import pandas as pd

# Conectamos a tu base de datos
conn = sqlite3.connect(r"C:\Users\fjose\OneDrive\Desktop\SISTEMA INVENTARIO\mi_negocio.db")

# 1. ¿Cuántas filas hay en la tabla compras?
total_filas = pd.read_sql_query("SELECT COUNT(*) FROM compras", conn).iloc[0, 0]
print(f"Total de registros en la tabla 'compras': {total_filas}")

# 2. ¿Qué hay en las primeras 3 filas?
if total_filas > 0:
    datos = pd.read_sql_query("SELECT * FROM compras LIMIT 3", conn)
    print("\n--- Primeros 3 registros encontrados ---")
    print(datos)
else:
    print("\n¡La tabla 'compras' está totalmente vacía!")

conn.close()