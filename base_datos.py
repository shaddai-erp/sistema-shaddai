import sqlite3

def conectar_db():
    conexion = sqlite3.connect("mi_negocio.db")
    return conexion

def crear_tablas():
    conexion = conectar_db()
    cursor = conexion.cursor()
    
    # 2. Creamos la tabla de PRODUCTOS (Inventario)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS productos (
            codigo TEXT PRIMARY KEY,
            descripcion TEXT NOT NULL,
            existencia REAL DEFAULT 0,
            costo_dolares REAL DEFAULT 0,
            precio_dolares REAL DEFAULT 0
        )
    ''')
    
    conexion.commit()
    conexion.close()

# Opcional: Llama a crear_tablas() al final o cuando se importe
crear_tablas()