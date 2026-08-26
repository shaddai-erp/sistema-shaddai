import sqlite3
conn = sqlite3.connect("mi_negocio.db")
cursor = conn.cursor()
# Esto crea la tabla si no existe, sin borrar lo que ya tienes
cursor.execute('''CREATE TABLE IF NOT EXISTS proveedores 
                (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                 nombre TEXT, contacto TEXT, telefono TEXT)''')
conn.commit()
conn.close()
print("¡Tabla creada con éxito!")