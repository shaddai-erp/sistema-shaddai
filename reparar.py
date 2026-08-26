import sqlite3

print("🔄 Conectando a mi_negocio.db para una reparación completa...")
try:
    conn = sqlite3.connect("mi_negocio.db")
    cursor = conn.cursor()
    
    # 1. Crear la tabla con la estructura exacta que pide tu app.py
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS cuentas_por_pagar (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            id_compra INTEGER DEFAULT 0,
            proveedor TEXT DEFAULT '',
            num_factura TEXT DEFAULT '',
            monto_original REAL DEFAULT 0.0,
            saldo_pendiente REAL DEFAULT 0.0,
            fecha_vencimiento TEXT DEFAULT '',
            estado TEXT DEFAULT 'Pendiente'
        )''')
    conn.commit()
    
    # 2. Revisar qué columnas tiene actualmente en el disco
    cursor.execute("PRAGMA table_info(cuentas_por_pagar)")
    columnas = [col[1] for col in cursor.fetchall()]
    print(f"📋 Columnas actuales en el archivo: {columnas}")
    
    # 3. Agregar una por una las columnas si es que no existen
    columnas_a_verificar = {
        "id_compra": "INTEGER DEFAULT 0",
        "proveedor": "TEXT DEFAULT ''",
        "num_factura": "TEXT DEFAULT ''",
        "monto_original": "REAL DEFAULT 0.0",
        "saldo_pendiente": "REAL DEFAULT 0.0",
        "fecha_vencimiento": "TEXT DEFAULT ''",
        "estado": "TEXT DEFAULT 'Pendiente'"
    }
    
    for columna, tipo in columnas_a_verificar.items():
        if columna not in columnas:
            print(f"➕ Agregando columna faltante: '{columna}'...")
            cursor.execute(f"ALTER TABLE cuentas_por_pagar ADD COLUMN {columna} {tipo}")
            conn.commit()
        else:
            print(f"✅ La columna '{columna}' ya está integrada.")
            
    conn.close()
    print("🎉 ¡Estructura de base de datos reparada por completo!")

except sqlite3.OperationalError as e:
    print(f"❌ ERROR: El archivo de la base de datos está bloqueado.")
    print(f"Detalle: {e}")
    print("💡 Cierra el navegador y vuelve a intentar ejecutar este script.")
except Exception as e:
    print(f"❌ Ocurrió un error inesperado: {e}")