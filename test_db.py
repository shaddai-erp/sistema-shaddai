import sqlite3
import pandas as pd

# Conecta al mismo archivo que usa tu app
conn = sqlite3.connect("mi_negocio.db")

# Verifica qué tablas existen
tablas = conn.execute("SELECT name FROM sqlite_master WHERE type='table';").fetchall()
print("Tablas encontradas:", tablas)

# Intenta contar cuántos proveedores hay
cantidad = conn.execute("SELECT COUNT(*) FROM proveedores").fetchone()[0]
print("Cantidad de proveedores en la tabla:", cantidad)

# Muestra los primeros datos
if cantidad > 0:
    df = pd.read_sql_query("SELECT * FROM proveedores", conn)
    print(df)
else:
    print("La tabla 'proveedores' está vacía.")

conn.close()