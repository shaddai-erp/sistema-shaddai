import sqlite3

ruta_db = r"C:\Users\fjose\OneDrive\Desktop\SISTEMA INVENTARIO\mi_negocio.db"

try:
    conn = sqlite3.connect(ruta_db)
    cursor = conn.cursor()
    
    # Eliminamos las dos deudas duplicadas usando el número de factura y sus montos exactos
    # Esto dejará la de 269.04 intacta (si es la que deseas conservar) o limpiará el lote de forma segura.
    cursor.execute("""
        DELETE FROM cuentas_por_pagar 
        WHERE num_factura = 'N# 80013848' AND monto_original IN (195.36, 60.84)
    """)
    
    conn.commit()
    print("🗑️ ¡Líneas duplicadas de Q20 eliminadas con éxito por monto!")
    conn.close()

except Exception as e:
    print(f"❌ Ocurrió un error: {e}")