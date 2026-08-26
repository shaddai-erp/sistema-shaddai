import streamlit as st
import sqlite3
import pandas as pd
from io import BytesIO
from datetime import datetime
import tempfile
import pyBCV
import requests
from bs4 import BeautifulSoup
import urllib3

import streamlit as st

# --- CONFIGURACIÓN DEL LOGIN ---
# Inicializamos la variable de estado para saber si ya inició sesión
if "autenticado" not in st.session_state:
    st.session_state.autenticado = False
if "empresa_actual" not in st.session_state:
    st.session_state.empresa_actual = "shaddai"

# Función simple de validación (aquí defines tus usuarios y empresas)
def verificar_credenciales(usuario, password):
    # Base de datos simulada de usuarios (más adelante la pasamos a SQLite)
    usuarios_permitidos = {
        "shaddai": {"pass": "1234", "empresa": "Acrílicos Shaddai", "rol": "Admin"},
        # Aquí podrás agregar a otros clientes en el futuro, ej:
        # "ferreteriasol": {"pass": "abcd", "empresa": "Ferretería El Sol", "rol": "Admin"}
    }
    
    if usuario in usuarios_permitidos and usuarios_permitidos[usuario]["pass"] == password:
        return usuarios_permitidos[usuario]
    return None

# --- PANTALLA DE ACCESO SI NO ESTÁ LOGUEADO ---
if not st.session_state.autenticado:
    st.title("🔐 Acceso al Sistema SHADDAI")
    st.markdown("Por favor, ingrese sus credenciales para continuar.")
    
    with st.form("form_login"):
        usuario_input = st.text_input("Usuario").strip().lower()
        password_input = st.text_input("Contraseña", type="password")
        btn_login = st.form_submit_button("🔑 Entrar al Sistema")
        
        if btn_login:
            datos_usuario = verificar_credenciales(usuario_input, password_input)
            if datos_usuario:
                st.session_state.autenticado = True
                st.session_state.usuario = usuario_input
                st.session_state.empresa_actual = datos_usuario["empresa"]
                st.success(f"¡Bienvenido, {datos_usuario['empresa']}!")
                st.rerun() # Recarga la página para mostrar el sistema principal
            else:
                st.error("❌ Usuario o contraseña incorrectos.")
    
    # Detenemos la ejecución aquí para que no muestre el resto de la app si no se ha logueado
    st.stop()

# --- SI YA ESTÁ LOGUEADO, MUESTRA LA BARRA LATERAL CON SU INFORMACIÓN ---
st.sidebar.success(f"Empresa: *{st.session_state.empresa_actual}*")
if st.sidebar.button("🚪 Cerrar Sesión"):
    st.session_state.autenticado = False
    st.session_state.empresa_actual = ""
    st.rerun()

st.sidebar.markdown("---")

# Desactivamos advertencias de certificados SSL para el BCV
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# --- FUNCIONES GENERALES MULTI-EMPRESA ---

def ejecutar_sql(query, parametros=()):
    """Ejecuta cualquier INSERT, UPDATE o DELETE de forma segura."""
    conn = sqlite3.connect("mi_negocio.db")
    cursor = conn.cursor()
    try:
        cursor.execute(query, parametros)
        conn.commit()
    except Exception as e:
        st.error(f"Error en la base de datos: {e}")
    finally:
        conn.close()

def crear_tablas_si_no_existen():
    conn = sqlite3.connect("mi_negocio.db")
    cursor = conn.cursor()
    
    # Creamos la tabla inventario por si no existe
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS inventario (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            empresa_id TEXT NOT NULL,
            sku TEXT,
            descripcion TEXT,
            precio REAL
        )
    ''')
    
    # 🌟 TRUCO NUEVO: Si la tabla ya existía pero no tenía la columna empresa_id, se la agregamos aquí:
    try:
        cursor.execute("ALTER TABLE inventario ADD COLUMN empresa_id TEXT DEFAULT 'shaddai'")
    except Exception as e:
        pass # Si la columna ya existe, ignora el error y sigue adelante
        
    conn.commit()
    conn.close()

# Ejecutamos la función
crear_tablas_si_no_existen()

def crear_tablas_si_no_existen():
    conn = sqlite3.connect("mi_negocio.db")
    cursor = conn.cursor()
    
    # 1. Crear tablas base por si no existen
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS inventario (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            empresa_id TEXT NOT NULL,
            sku TEXT,
            descripcion TEXT,
            precio REAL
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS ventas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            empresa_id TEXT NOT NULL,
            fecha TEXT,
            total REAL
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS clientes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            empresa_id TEXT NOT NULL,
            codigo TEXT,
            tipo TEXT,
            nombre_razon TEXT,
            direccion TEXT,
            telefono TEXT,
            email TEXT
        )
    ''')
    
    # 🌟 2. ASEGURAR COLUMNAS SI LAS TABLAS YA EXISTÍAN DE ANTES
    try:
        cursor.execute("ALTER TABLE inventario ADD COLUMN empresa_id TEXT DEFAULT 'shaddai'")
    except Exception:
        pass

    try:
        cursor.execute("ALTER TABLE ventas ADD COLUMN empresa_id TEXT DEFAULT 'shaddai'")
    except Exception:
        pass

    try:
        cursor.execute("ALTER TABLE clientes ADD COLUMN empresa_id TEXT DEFAULT 'shaddai'")
    except Exception:
        pass

    conn.commit()
    conn.close()

# Ejecutamos la función al arrancar
crear_tablas_si_no_existen()

def obtener_todas_las_tasas():
    tasas = {"USD": 36.50, "EUR": 40.00, "USDT": 37.00} 
    try:
        url = "https://www.bcv.org.ve/"
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=5, verify=False)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            
            dolar_div = soup.find('div', id='dolar')
            if dolar_div:
                dolar_val = dolar_div.find('strong').text.strip().replace(',', '.')
                tasas["USD"] = float(dolar_val)
                
            euro_div = soup.find('div', id='euro')
            if euro_div:
                euro_val = euro_div.find('strong').text.strip().replace(',', '.')
                tasas["EUR"] = float(euro_val)
                
    except Exception as e:
        print(f"No se pudo conectar al BCV: {e}")
        
    return tasas

    st.sidebar.markdown("---")
st.sidebar.subheader("💱 Consulta de Tasas")

if st.sidebar.button("🔄 Ver Tasas del Día"):
    tasas_actuales = obtener_todas_las_tasas()
    st.sidebar.success("¡Tasas listas!")
    st.sidebar.write(f"🇺🇸 *Dólar BCV:* {tasas_actuales['USD']:,.2f} Bs")
    st.sidebar.write(f"🇪🇺 *Euro BCV:* {tasas_actuales['EUR']:,.2f} Bs")
    st.sidebar.info("💡 Nota: Ingrese la tasa de USDT de Binance manualmente abajo según el mercado.")

def generar_factura_pdf(cliente_data, carrito_items, totales_data, tasa_cambio, moneda_texto):
    tasa = float(tasa_cambio) if tasa_cambio and tasa_cambio > 0 else 36.50
    
    html_content = f"""
    <!DOCTYPE html>
    <html lang="es">
    <head>
    <meta charset="UTF-8">
    <style>
        @page {{ size: letter; margin: 10mm 15mm; background-color: transparent; }}
        *, *::before, *::after {{ box-sizing: border-box; }}
        body {{ font-family: 'Courier New', Courier, monospace; font-size: 9.5pt; color: #000; margin: 0; padding: 0; line-height: 1.15; }}
        .container {{ width: 100%; padding: 0px; }}
        .spacer-header {{ height: 110px; }} 
        .date-table {{ width: 100%; border-collapse: collapse; margin-bottom: 15px; }}
        .client-table {{ width: 100%; border-collapse: collapse; font-size: 9pt; margin-bottom: 20px; }}
        .client-table td {{ padding: 2px 4px; vertical-align: middle; }}
        .items-table {{ width: 100%; border-collapse: collapse; min-height: 100px; }}
        .items-table td {{ padding: 3px 4px; font-size: 9pt; vertical-align: top; }}
        .col-sku {{ width: 15%; }}
        .col-desc {{ width: 45%; }}
        .col-cant {{ width: 10%; text-align: center; }}
        .col-precio {{ width: 15%; text-align: right; }}
        .col-total {{ width: 15%; text-align: right; }}
        .footer-section {{ width: 100%; border-collapse: collapse; margin-top: 10px; }}
        .totals-table {{ width: 100%; border-collapse: collapse; }}
        .totals-table td {{ padding: 2px 6px; border: none; text-align: right; font-size: 9.5pt; }}
    </style>
    </head>
    <body>
    <div class="container">
        <div class="spacer-header"></div>

        <!-- Fecha arriba a la derecha -->
        <table class="date-table">
            <tr>
                <td style="width: 70%;"></td>
                <td style="width: 30%; text-align: right; font-size: 8.5pt;">
                    <strong>{totales_data['dia']}</strong> / <strong>{totales_data['mes']}</strong> / <strong>{totales_data['anio']}</strong>
                </td>
            </tr>
        </table>

        <table class="client-table">
            <tr>
                <td style="width: 65%;"><strong>{cliente_data['nombre']}</strong></td>
                <td style="width: 35%;">{totales_data['condicion']}</td>
            </tr>
            <tr>
                <td>{cliente_data['direccion']}</td>
                <td>{cliente_data['telefono']}</td>
            </tr>
            <tr>
                <td colspan="2">{cliente_data['rif']}</td>
            </tr>
        </table>

        <table class="items-table">
            <tbody>
    """
    
    for item in carrito_items:
        precio_bs = item['precio'] * tasa
        total_bs = item['total'] * tasa
        html_content += f"""
                <tr>
                    <td class="col-sku">{item['SKU']}</td>
                    <td class="col-desc">{item['descripcion']}</td>
                    <td class="col-cant">{item['cantidad']}</td>
                    <td class="col-precio">{precio_bs:,.2f}</td>
                    <td class="col-total">{total_bs:,.2f}</td>
                </tr>
        """
        
    subtotal_bs = totales_data['subtotal'] * tasa
    iva_bs = totales_data['iva'] * tasa
    # Forzamos la sumatoria correcta (Base Imponible + IVA)
    total_bs_final = subtotal_bs + iva_bs

    html_content += f"""
            </tbody>
        </table>

        <table class="footer-section">
            <tr>
                <td style="width: 50%;">
                    <div style="font-size: 7.5pt;">Tasa {moneda_texto} Aplicada: {tasa:,.2f} Bs</div>
                </td>
                <td style="width: 50%; vertical-align: top; padding: 0;">
                    <table class="totals-table">
                        <tr>
                            <td>{subtotal_bs:,.2f}</td>
                        </tr>
                        <tr>
                            <td>{iva_bs:,.2f}</td>
                        </tr>
                        <tr>
                            <td style="font-size: 10.5pt; font-weight: bold;">{total_bs_final:,.2f}</td>
                        </tr>
                    </table>
                </td>
            </tr>
        </table>
    </div>
    </body>
    </html>
    """
    html_content += """
    <script> window.onload = function() { window.print(); } </script>
    """
    
    with tempfile.NamedTemporaryFile(delete=False, suffix=".html", mode="w", encoding="utf-8") as tmp:
        tmp.write(html_content)
        return tmp.name

def inicializar_bd_ventas():
    conn = sqlite3.connect("mi_negocio.db")
    cursor = conn.cursor()
    # Tabla de clientes
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS clientes (
            codigo TEXT PRIMARY KEY,
            tipo TEXT,
            nombre_razon TEXT,
            direccion TEXT,
            telefono TEXT,
            email TEXT
        )
    ''')
    # Tabla de facturas / ventas registradas
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS ventas (
            id_factura INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha TEXT,
            cliente TEXT,
            tipo_pago TEXT,
            banco_metodo TEXT,
            subtotal REAL,
            descuento REAL,
            iva REAL,
            total REAL,
            estado TEXT
        )
    ''')
    conn.commit()
    conn.close()

inicializar_bd_ventas()

st.set_page_config(page_title="Acrílicos Shaddai - Sistema Administrativo", layout="wide")

# Título principal del sistema
st.title("🎨 Acrílicos Shaddai 2021, C.A. - Sistema Administrativo")

# Menú lateral en forma de mosaico / pestañas principales
menu = st.sidebar.selectbox(
    "Navegación Principal",
    ["Inventario", "Ventas y Facturación", "Compras", "Cuentas por Pagar", "Cuentas por Cobrar", "Bancos", "Gastos", "Reportes"]
)

# Simulación de Base de Datos en Memoria para el Inventario
if 'inventario' not in st.session_state:
    st.session_state.inventario = pd.DataFrame(columns=[
        "SKU", "Descripción", "Instancia", "Cantidad", "Stock Mínimo", "Costo ($)", "IVA (%)", "Precio Venta ($)"
    ])

elif menu == "Inventario":
    st.header("📦 Módulo de Inventario")
    
    # Creamos las pestañas incluyendo la nueva de carga masiva
    tab1, tab2, tab3, tab4 = st.tabs(["Consultar / Alertas", "Registrar Producto", "Ajuste Físico (Autorizado)", "Carga Masiva Excel"])
    
    with tab1:
        st.subheader("Existencia Actual y Alertas de Stock")
           # 🔍 PEGA LA BARRITA DE BÚSQUEDA AQUÍ:
    busq_inv = st.text_input("🔍 Buscar por SKU o Descripción:")

    try:
        # Obtenemos la empresa actual de la sesión
        empresa_actual = st.session_state.get("usuario", "general")
        
        # Conectamos a la base de datos y filtramos por la empresa logueada
        conn = sqlite3.connect("mi_negocio.db")
        df_inventario = pd.read_sql_query(
            "SELECT * FROM inventario WHERE empresa_id = ?", 
            conn, 
            params=(empresa_actual,)
        )
        conn.close()

        if not df_inventario.empty:
            # Si escribes algo en la barra, filtramos la tabla
            if busq_inv:
                df_filtrado = df_inventario[
                    df_inventario['SKU'].astype(str).str.contains(busq_inv, case=False, na=False) | 
                    df_inventario['DESCRIPCION'].astype(str).str.contains(busq_inv, case=False, na=False)
                ]
                st.dataframe(df_filtrado, use_container_width=True)
            else:
                # Mostramos la tabla completa si no hay nada escrito
                st.dataframe(df_inventario, use_container_width=True)
                
            # Opcional: Un indicador rápido de productos totales cargados
            st.info(f"Total de registros en inventario: {len(df_inventario)}")
        else:
            st.warning("La base de datos está vacía. Sube un archivo en la pestaña...")
            
    except Exception as e:
        st.error(f"Error al cargar el inventario: {e}")
        
        try:
            # Conectamos a la base de datos y leemos la tabla inventario
            conn = sqlite3.connect("mi_negocio.db")
            df_inventario = pd.read_sql_query("SELECT * FROM inventario", conn)
            conn.close()
            
            if not df_inventario.empty:
                # Mostramos la tabla completa de forma interactiva
                st.dataframe(df_inventario, use_container_width=True)
                
                # Opcional: Un indicador rápido de productos totales cargados
                st.info(f"Total de registros en inventario: {len(df_inventario)}")
            else:
                st.warning("La base de datos está vacía. Sube un archivo en la pestaña 'Carga Masiva Excel'.")
                
        except Exception as e:
            st.info("Aún no hay una base de datos creada. Sube tu archivo Excel en la pestaña 'Carga Masiva Excel' para comenzar.")
        
    with tab2:
        st.subheader("Registrar Producto Individual")
        
        with st.form("form_nuevo_producto"):
            col1, col2 = st.columns(2)
            with col1:
                sku_nuevo = st.text_input("SKU / Código del Producto")
                desc_nueva = st.text_input("Descripción del Producto")
                ubicacion_nueva = st.text_input("Ubicación en Tienda / Almacén", value="CUA")
            with col2:
                costo_nuevo = st.number_input("Costo Unitario", min_value=0.0, format="%.4f")
                precio_nuevo = st.number_input("Precio de Venta", min_value=0.0, format="%.4f")
                cantidad_nueva = st.number_input("Cantidad Inicial (Stock)", min_value=0.0, format="%.2f")
            
            # Datos adicionales opcionales según tu estructura de Excel
            unid_medida = st.selectbox("Unidad de Medida", ["UNIDAD", "GALON", "LITRO", "ML", "METRO", "KG"])
            
            btn_guardar_prod = st.form_submit_button("💾 Guardar Producto en Inventario")
            
            if btn_guardar_prod:
                if sku_nuevo and desc_nueva:
                    try:
                        conn = sqlite3.connect("mi_negocio.db")
                        cursor = conn.cursor()
                        
                        # Insertar el nuevo producto respetando las columnas de tu tabla
                        cursor.execute('''
                            INSERT INTO inventario (SKU, DESCRIPCION, UBICACION, COSTO, PRECIO, "INV INICIAL", "UNID MEDIDA")
                            VALUES (?, ?, ?, ?, ?, ?, ?)
                        ''', (sku_nuevo, desc_nueva.upper(), ubicacion_nueva.upper(), costo_nuevo, precio_nuevo, cantidad_nueva, unid_medida))
                        
                        conn.commit()
                        conn.close()
                        st.success(f"¡El producto '{desc_nueva}' ha sido registrado exitosamente!")
                    except Exception as e:
                        st.error(f"Error al registrar el producto: {e}")
                else:
                    st.warning("Por lo menos debes rellenar el SKU y la Descripción del producto.")
        
    with tab3:
        st.subheader("Ajuste Físico de Inventario")
        st.markdown("Esta sección está restringida. Permite cargar o descargar inventario físico por diferencias de conteo, dejando un concepto y un responsable.")
        
        with st.form("form_ajuste_fisico"):
            # 1. SEGURIDAD: Clave de acceso
            clave_ingresada = st.text_input("Clave de Autorización", type="password")
            
            st.markdown("---")
            
            # 2. DATOS DEL AJUSTE
            col1, col2 = st.columns(2)
            with col1:
                sku_ajuste = st.text_input("SKU del Producto a Ajustar")
                tipo_movimiento = st.selectbox("Tipo de Ajuste", ["Carga (Sumar al inventario)", "Descarga (Restar del inventario)"])
                cantidad_ajuste = st.number_input("Cantidad a Ajustar", min_value=0.01, format="%.2f")
            with col2:
                concepto_ajuste = st.selectbox("Concepto", ["Diferencia en conteo físico", "Merma / Daño", "Robo / Extravío", "Error de carga anterior", "Devolución sin factura"])
                responsable = st.text_input("Responsable / Firma (Nombre y Apellido)")
                observacion_extra = st.text_input("Observación adicional (Opcional)")
            
            btn_ejecutar_ajuste = st.form_submit_button("⚖️ Aplicar Ajuste Físico")
            
            if btn_ejecutar_ajuste:
                # Clave temporal de administrador (puedes cambiarla por la que prefieras)
                CLAVE_AUTORIZADA = "Shaddai2021*" 
                
                if clave_ingresada == CLAVE_AUTORIZADA:
                    if sku_ajuste and responsable:
                        try:
                            conn = sqlite3.connect("mi_negocio.db")
                            cursor = conn.cursor()
                            
                            # Verificamos si el producto existe en la base de datos
                            cursor.execute('SELECT "INV INICIAL", DESCRIPCION FROM inventario WHERE SKU = ?', (sku_ajuste,))
                            resultado = cursor.fetchone()
                            
                            if resultado:
                                stock_actual = resultado[0]
                                desc_producto = resultado[1]
                                
                                # Calculamos el nuevo stock según sea carga o descarga
                                if "Carga" in tipo_movimiento:
                                    nuevo_stock = stock_actual + cantidad_ajuste
                                else:
                                    nuevo_stock = stock_actual - cantidad_ajuste
                                    if nuevo_stock < 0:
                                        nuevo_stock = 0 # Evitar stock negativo por seguridad
                                        
                                # Actualizamos el inventario en la tabla
                                cursor.execute('UPDATE inventario SET "INV INICIAL" = ? WHERE SKU = ?', (nuevo_stock, sku_ajuste))
                                
                                # Opcional: Podrías guardar un historial de auditoría si lo deseas luego
                                
                                conn.commit()
                                conn.close()
                                
                                st.success(f"✅ Ajuste realizado con éxito en '{desc_producto}'. Stock anterior: {stock_actual} | Nuevo Stock: {nuevo_stock}")
                                st.info(f"Registrado bajo el concepto de *{concepto_ajuste}* por el responsable: *{responsable}*.")
                            else:
                                conn.close()
                                st.error("❌ El SKU ingresado no se encuentra registrado en el inventario.")
                        except Exception as e:
                            st.error(f"Error al procesar el ajuste en la base de datos: {e}")
                    else:
                        st.warning("⚠️ Debes rellenar obligatoriamente el SKU y el nombre del Responsable/Firma.")
                else:
                    st.error("🔒 Clave de autorización incorrecta. No se puede realizar el ajuste.")
        
    with tab4:
        st.subheader("Carga Masiva de Inventario mediante Excel")
        st.markdown("Sube tu archivo de Excel para actualizar todo el inventario de una sola vez.")
        
        # 1. DESCARGA DE PLANTILLA
        df_plantilla = pd.DataFrame(columns=["SKU", "Nombre", "Cantidad", "Precio", "Costo"])
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df_plantilla.to_excel(writer, index=False, sheet_name='Inventario')
        processed_data = output.getvalue()
        
        st.download_button(
            label="📥 Descargar Plantilla de Excel",
            data=processed_data,
            file_name="plantilla_inventario_shaddai.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        
        st.markdown("---")
        
        
archivo_subido = st.file_uploader("Sube tu plantilla de Excel completada", type=["xlsx", "xls"])
        
if archivo_subido is not None:
            try:
                df_carga = pd.read_excel(archivo_subido)
                st.write("Vista previa de los datos cargados:")
                st.dataframe(df_carga.head())
                
                if st.button("💾 Procesar e Insertar en Base de Datos"):
                    # Limpiamos los nombres de las columnas para evitar espacios o errores
                    df_carga.columns = [str(c).strip().upper() for c in df_carga.columns]
                    
                    conn = sqlite3.connect("mi_negocio.db")
                    df_carga.to_sql("inventario", conn, if_exists="replace", index=False)
                    conn.close()
                    
                    st.success("¡Inventario cargado y guardado en la base de datos con éxito!")
                    st.rerun() # Esto recarga automáticamente la pantalla para que aparezca la tabla de una vez
                    
            except Exception as e:
                st.error(f"Error al procesar el archivo: {e}")

elif menu == "Ventas y Facturación":
    st.header("🛒 Módulo de Ventas y Facturación")
    
    # 🌟 Obtenemos la empresa actual de la sesión
    empresa_actual = st.session_state.get("usuario", "general")
    
    # 🌟 Asegurarnos de que las tablas de clientes y ventas existan con todas sus columnas
    conn_init = sqlite3.connect("mi_negocio.db")
    cursor_init = conn_init.cursor()
    cursor_init.execute('''
        CREATE TABLE IF NOT EXISTS ventas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            empresa_id TEXT,
            fecha TEXT,
            cliente TEXT,
            tipo_pago TEXT,
            banco_metodo TEXT,
            subtotal REAL,
            descuento REAL,
            iva REAL,
            total REAL,
            estado TEXT
        )
    ''')
    cursor_init.execute('''
        CREATE TABLE IF NOT EXISTS clientes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            empresa_id TEXT,
            codigo TEXT,
            tipo TEXT,
            nombre_razon TEXT,
            direccion TEXT,
            telefono TEXT,
            email TEXT
        )
    ''')
    conn_init.commit()
    conn_init.close()
    
    # 1. DATOS DEL CLIENTE
    st.subheader("1. Datos del Cliente")
    tipo_persona = st.radio("Tipo de Cliente", ["Persona Natural", "Persona Jurídica"], horizontal=True)
    
    col_c1, col_c2 = st.columns(2)
    with col_c1:
        codigo_cliente = ""
        nombre = ""
        
        if tipo_persona == "Persona Natural":
            codigo_cliente = st.text_input("Cédula (Será su código de registro)", key="input_cedula")
            nombre = st.text_input("Nombre y Apellido", key="input_nombre_nat")
        else:
            codigo_cliente = st.text_input("RIF / Código de Registro (Persona Jurídica)", key="input_rif")
            nombre = st.text_input("Razón Social", key="input_nombre_jur")
    with col_c2:
        direccion_cli = st.text_input("Dirección")
        telefono_cli = st.text_input("Teléfono")
        email_cli = st.text_input("Email")

    st.markdown("---")

    try:
        conn = sqlite3.connect("mi_negocio.db")
        # 🔥 FILTRAMOS EL INVENTARIO POR LA EMPRESA ACTUAL
        df_inv = pd.read_sql_query("SELECT * FROM inventario WHERE empresa_id = ?", conn, params=(empresa_actual,))
        conn.close()
        
        columnas_necesarias = ['SKU', 'DESCRIPCION', 'PRECIO', 'INV INICIAL']
        
        if len(df_inv.columns) >= 4:
            df_inv = df_inv.rename(columns={
                df_inv.columns[0]: 'SKU',
                df_inv.columns[1]: 'DESCRIPCION',
                df_inv.columns[8]: 'PRECIO',
                df_inv.columns[4] if len(df_inv.columns) > 4 else df_inv.columns[3]: 'INV INICIAL'
            })
            
        df_inv.columns = [str(col).strip().upper() for col in df_inv.columns]
            
    except Exception as e:
        df_inv = pd.DataFrame()
        st.error(f"Error cargando inventario: {e}")

    if not df_inv.empty:
        if "carrito" not in st.session_state:
            st.session_state.carrito = []

        sku_seleccionado = st.selectbox("Seleccione el Producto", df_inv['SKU'] + " - " + df_inv['DESCRIPCION'])
        cantidad_solicitada = st.number_input("Cantidad solicitada", min_value=0.01, value=1.0, format="%.2f")
        
        if st.button("➕ Agregar al Carrito"):
            sku_puro = sku_seleccionado.split(" - ")[0]
            producto_row = df_inv[df_inv['SKU'] == sku_puro].iloc[0]

            precio_unitario = float(producto_row['PRECIO'].values[0]) if hasattr(producto_row['PRECIO'], 'values') else float(producto_row['PRECIO'])
            descripcion_prod = producto_row['DESCRIPCION'] if 'DESCRIPCION' in producto_row else producto_row.get('descripcion', '')
            
            st.session_state.carrito.append({
                "SKU": sku_puro,
                "Descripcion": descripcion_prod,
                "descripcion": descripcion_prod,
                "Cantidad": cantidad_solicitada,
                "cantidad": cantidad_solicitada,
                "Precio": precio_unitario,
                "precio": precio_unitario,
                "Total": cantidad_solicitada * precio_unitario,
                "total": cantidad_solicitada * precio_unitario,
            })
            st.success(f"Agregado: {descripcion_prod}")

        if st.session_state.carrito:
            st.markdown("#### Productos en la Venta:")
            df_carrito = pd.DataFrame(st.session_state.carrito)
            st.dataframe(df_carrito, use_container_width=True)
            
            if st.button("🗑️ Vaciar Carrito"):
                st.session_state.carrito = []
                st.rerun()
                
            subtotal = df_carrito['Total'].sum()
            
            st.markdown("---")
            st.subheader("3. Totales y Forma de Pago")
            
            col_p1, col_p2 = st.columns(2)
            with col_p1:
                tipo_pago = st.selectbox("Tipo de Pago", ["Contado", "Crédito"])
                
                if tipo_pago == "Contado":
                    metodo_pago = st.selectbox("Método / Banco", [
                        "Punto de Venta - Banesco", "Punto de Venta - BNC", "Punto de Venta - Venezuela",
                        "Efectivo ($)", "Efectivo (Bs)", 
                        "Pago Móvil - Banesco", "Pago Móvil - BNC", "Pago Móvil - Venezuela",
                        "Cashea", "Zelle", "Binance"
                    ])
                else:
                    metodo_pago = "Crédito por Cobrar"

            with col_p2:
                porcentaje_desct = st.number_input("Descuento (%)", min_value=0.0, max_value=100.0, value=0.0)
                aplica_iva = st.checkbox("Aplicar IVA (16%)", value=True)

            monto_descuento = subtotal * (porcentaje_desct / 100.0)
            subtotal_con_descuento = subtotal - monto_descuento
            monto_iva = subtotal_con_descuento * 0.16 if aplica_iva else 0.0
            total_general = subtotal_con_descuento + monto_iva

            st.markdown(f"""
            * Subtotal: {subtotal:.2f}$
            * Descuento ({porcentaje_desct}%): -{monto_descuento:.2f}$
            * IVA (16%): {monto_iva:.2f}$
            * ### Total a Pagar: {total_general:.2f}$
            """)

        tasas_disponibles = obtener_todas_las_tasas()

        st.markdown("### 💳 Moneda de Cobro y Tasa")
        tipo_moneda = st.selectbox(
            "Seleccione el método/moneda para calcular la factura:", 
            ["Dólar BCV (USD)", "Euro BCV (EUR)", "USDT (Binance)"]
        )

        if tipo_moneda == "Dólar BCV (USD)":
            tasa_seleccionada = st.number_input("Tasa Dólar BCV", value=float(tasas_disponibles["USD"]), format="%.2f")
            texto_moneda = "USD (BCV)"
        elif tipo_moneda == "Euro BCV (EUR)":
            tasa_seleccionada = st.number_input("Tasa Euro BCV", value=float(tasas_disponibles["EUR"]), format="%.2f")
            texto_moneda = "EUR (BCV)"
        else:
            tasa_seleccionada = st.number_input("Tasa USDT (Binance)", value=float(tasas_disponibles["USDT"]), format="%.2f")
            texto_moneda = "USDT (Binance)"

        st.markdown("---")

      # 4. BOTÓN DE PROCESAR VENTA
        if st.button("💾 Procesar y Facturar Venta"):
            if tipo_persona == "Persona Natural":
                codigo_cliente = st.session_state.get("input_cedula", "").strip()
                nombre = st.session_state.get("input_nombre_nat", "").strip()
            else:
                codigo_cliente = st.session_state.get("input_rif", "").strip()
                nombre = st.session_state.get("input_nombre_jur", "").strip()

            if not codigo_cliente:
                codigo_cliente = "J-30925148-1"
            if not nombre:
                nombre = "CLIENTE GENERAL"

            if codigo_cliente and nombre:
                try:
                    conn = sqlite3.connect("mi_negocio.db")
                    cursor = conn.cursor()
                    
                    # 🌟 Aseguramos la tabla ventas limpia
                    cursor.execute("DROP TABLE IF EXISTS ventas")
                    cursor.execute('''
                        CREATE TABLE ventas (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            empresa_id TEXT,
                            fecha TEXT,
                            cliente TEXT,
                            tipo_pago TEXT,
                            banco_metodo TEXT,
                            subtotal REAL,
                            descuento REAL,
                            iva REAL,
                            total REAL,
                            estado TEXT
                        )
                    ''')

                    cliente_info = {
                        "nombre": nombre,
                        "rif": codigo_cliente,
                        "direccion": direccion_cli if 'direccion_cli' in locals() and direccion_cli else "Cúa, Edo. Miranda",
                        "telefono": telefono_cli if 'telefono_cli' in locals() and telefono_cli else "0412-0000000"
                    }
                    
                    from datetime import datetime
                    fecha_actual = datetime.now()
                    
                    totales_info = {
                        "dia": fecha_actual.strftime("%d"), 
                        "mes": fecha_actual.strftime("%m"), 
                        "anio": fecha_actual.strftime("%Y"),
                        "condicion": tipo_pago,
                        "forma": metodo_pago,
                        "banco": metodo_pago,
                        "subtotal": subtotal,
                        "iva": monto_iva,
                        "total": total_general
                    }
                    
                    carrito_guardado_temporal = st.session_state.carrito.copy()

                    html_path = generar_factura_pdf(
                        cliente_info, 
                        carrito_guardado_temporal, 
                        totales_info, 
                        tasa_seleccionada, 
                        texto_moneda
                    )

                    st.session_state.factura_lista = html_path
                    
                    # 🌟 Guardar o actualizar cliente con empresa_id
                    cursor.execute('''
                        INSERT OR REPLACE INTO clientes (empresa_id, codigo, tipo, nombre_razon, direccion, telefono, email)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', (empresa_actual, codigo_cliente, tipo_persona, nombre.upper(), direccion_cli if 'direccion_cli' in locals() else "", telefono_cli if 'telefono_cli' in locals() else "", email_cli if 'email_cli' in locals() else ""))
                    
                    # 🌟 Registrar la venta
                    fecha_str = fecha_actual.strftime("%Y-%m-%d %H:%M:%S")
                    cursor.execute('''
                        INSERT INTO ventas (empresa_id, fecha, cliente, tipo_pago, banco_metodo, subtotal, descuento, iva, total, estado)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (empresa_actual, fecha_str, nombre.upper(), tipo_pago, metodo_pago, subtotal, monto_descuento, monto_iva, total_general, "Pendiente" if tipo_pago == "Crédito" else "Pagado"))
                    
                    # 🌟 SI ES DE CONTADO, IMPACTAR AUTOMÁTICAMENTE EL MÓDULO DE BANCOS / TESORERÍA
                    if tipo_pago == "Contado":
                        # Mapeo exacto con los nombres que reconoce el módulo de Bancos: Banesco, Venezuela, BNC, Cashea
                        metodo_str = str(metodo_pago).lower()
                        if "banesco" in metodo_str:
                            cuenta_destino = "Banesco"
                        elif "venezuela" in metodo_str or "bdv" in metodo_str:
                            cuenta_destino = "Venezuela"
                        elif "bnc" in metodo_str:
                            cuenta_destino = "BNC"
                        elif "cashea" in metodo_str:
                            cuenta_destino = "Cashea"
                        else:
                            # Si es efectivo, zelle o binance, por defecto lo mandamos a Banesco o la cuenta principal operativa
                            cuenta_destino = "Banesco"

                        concepto_mov = f"Venta Factura - Cliente: {nombre.upper()} ({metodo_pago})"
                        ref_mov = f"FACT-{int(datetime.now().timestamp())}"
                        
                        # Redondeamos a 2 decimales exactos para evitar decimales largos innecesarios
                        monto_en_bolivares = round(totales_info["total"] * tasa_seleccionada, 2)

                        cursor.execute('''
                            INSERT INTO movimientos_bancarios (empresa_id, fecha, cuenta_destino, tipo_movimiento, concepto, referencia, monto)
                            VALUES (?, ?, ?, 'Ingreso', ?, ?, ?)
                        ''', (empresa_actual, fecha_str, cuenta_destino, concepto_mov, ref_mov, monto_en_bolivares))

                    # 🌟 Descontar del inventario físico respetando la empresa
                    for item in st.session_state.carrito:
                        cursor.execute('UPDATE inventario SET "INV INICIAL" = "INV INICIAL" - ? WHERE SKU = ? AND empresa_id = ?', 
                                       (item['Cantidad'], item['SKU'], empresa_actual))
                                
                    conn.commit()
                    conn.close()
                    
                    st.session_state.carrito = []
                    st.success(f"✅ ¡Venta procesada con éxito! Total registrado: {total_general:.2f}$")

                    if tipo_pago == "Crédito":
                        st.warning("⚠️ La venta se ha enviado automáticamente a Cuentas por Cobrar.")
                    else:
                        st.info(f"✅ Ingreso registrado y sumado en tesorería para: {metodo_pago}")

                except Exception as e:
                    st.error(f"Error al procesar la venta en la base de datos: {e}")
            else:
                st.warning("⚠️ Por favor, completa la cédula/RIF y el nombre del cliente antes de procesar la venta.")

        if "factura_lista" in st.session_state and st.session_state.factura_lista:
            import os
            if os.path.exists(st.session_state.factura_lista):
                with open(st.session_state.factura_lista, "rb") as f:
                    st.download_button(
                        label="📥 Descargar Factura para Imprimir",
                        data=f,
                        file_name="factura_shaddai.html",
                        mime="text/html"
                    )              

elif menu == "Compras":
    st.header("📦 Módulo Avanzado de Registro de Compras")
    
    # Asegurar que la variable de empresa exista
    empresa_actual = st.session_state.get("empresa_actual", st.session_state.get("empresa", "shaddai"))
    
    conn = sqlite3.connect("mi_negocio.db")
    cursor = conn.cursor()
    
    # 1. Crear tablas con empresa_id
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS proveedores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            empresa_id TEXT NOT NULL,
            nombre_razon TEXT,
            rif TEXT,
            direccion TEXT,
            telefono TEXT,
            email TEXT,
            porcentaje_retencion_iva INTEGER DEFAULT 75
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS compras (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            empresa_id TEXT NOT NULL,
            fecha TEXT,
            proveedor TEXT,
            rif_proveedor TEXT,
            num_documento TEXT,
            tipo_documento TEXT,
            condicion_pago TEXT,
            dias_credito INTEGER,
            fecha_vencimiento TEXT,
            sku TEXT,
            cantidad REAL,
            costo REAL,
            subtotal REAL,
            iva REAL,
            retencion_iva REAL,
            total_pagar REAL
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS cuentas_por_pagar (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            empresa_id TEXT NOT NULL,
            proveedor TEXT,
            rif_proveedor TEXT,
            num_documento TEXT,
            fecha_emision TEXT,
            fecha_vencimiento TEXT,
            monto_total REAL,
            moneda_texto TEXT,
            tasa_aplicada REAL,
            estado TEXT DEFAULT 'Pendiente'
        )
    ''')

    # Seguridad por si las tablas ya existían sin empresa_id
    for tabla in ["proveedores", "compras", "cuentas_por_pagar"]:
        try:
            cursor.execute(f"ALTER TABLE {tabla} ADD COLUMN empresa_id TEXT DEFAULT 'shaddai'")
        except Exception:
            pass

    conn.commit()

    tab_reg, tab_prov = st.tabs(["📝 Registrar Nueva Compra", "🏢 Directorio de Proveedores"])

    with tab_prov:
        st.subheader("Registro y Actualización de Proveedores")
        with st.form("form_proveedor"):
            p_nombre = st.text_input("Nombre / Razón Social de la Compañía")
            p_rif = st.text_input("RIF (Ej: J-12345678-9)")
            p_dir = st.text_input("Dirección Fiscal")
            p_tel = st.text_input("Teléfono")
            p_email = st.text_input("Correo Electrónico (Email)")
            p_ret = st.selectbox("Porcentaje de Retención de IVA por Defecto", [75, 100], format_func=lambda x: f"{x}% de Retención")
            
            if st.form_submit_button("💾 Guardar Proveedor"):
                if p_nombre and p_rif:
                    cursor.execute('''
                        INSERT INTO proveedores (empresa_id, nombre_razon, rif, direccion, telefono, email, porcentaje_retencion_iva)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', (empresa_actual, p_nombre, p_rif, p_dir, p_tel, p_email, p_ret))
                    conn.commit()
                    st.success(f"✅ Proveedor {p_nombre} registrado exitosamente.")
                    st.rerun()
                else:
                    st.warning("⚠️ El Nombre y el RIF son obligatorios.")

    with tab_reg:
        # Filtrar proveedores por empresa actual
        cursor.execute("SELECT nombre_razon, rif, porcentaje_retencion_iva FROM proveedores WHERE empresa_id = ?", (empresa_actual,))
        lista_prov = cursor.fetchall()
        
        if not lista_prov:
            st.warning("⚠️ Debe registrar al menos un proveedor en la pestaña 'Directorio de Proveedores' antes de procesar compras.")
        else:
            dic_prov = {p[0]: {"rif": p[1], "ret": p[2]} for p in lista_prov}
            nombres_proveedores = list(dic_prov.keys())

            with st.form("form_registro_compra_avanzado"):
                st.subheader("Datos del Documento y Proveedor")
                st.info("💡 Nota: Si la compra es de Contado, el número de factura o recibo es obligatorio. Si es a Crédito, se registrará la deuda automáticamente en Cuentas por Pagar.")
                
                col_p1, col_p2 = st.columns(2)
                with col_p1:
                    prov_seleccionado = st.selectbox("Seleccionar Proveedor", nombres_proveedores)
                    tipo_doc = st.selectbox("Tipo de Documento", ["Factura Fiscal", "Nota de Entrega"])
                with col_p2:
                    num_doc = st.text_input("Número de Factura o Nota de Entrega")
                    fecha_compra = st.date_input("Fecha de Emisión / Compra")

                st.markdown("---")
                st.subheader("Condición de Pago y Crédito")
                col_c1, col_c2 = st.columns(2)
                with col_c1:
                    condicion = st.selectbox("Modalidad de Pago", ["Contado", "Crédito"])
                with col_c2:
                    dias_cred = st.number_input("Días de Crédito (si aplica)", min_value=0, value=0, step=1)

                st.markdown("---")
                st.subheader("Detalle del Producto y Costos")
                
                try:
                      cursor.execute('SELECT SKU, DESCRIPCION FROM inventario')
                      productos_inv = cursor.fetchall()
                except:
                    productos_inv = []
                   
elif menu == "Inventario":
    st.header("📦 Módulo de Inventario")
    
    # Creamos las pestañas incluyendo la nueva de carga masiva
    tab1, tab2, tab3, tab4 = st.tabs(["Consultar / Alertas", "Registrar Producto", "Ajuste Físico (Autorizado)", "Carga Masiva Excel"])
    
    with tab1:
        st.subheader("Existencia Actual y Alertas de Stock")
           # 🔍 PEGA LA BARRITA DE BÚSQUEDA AQUÍ:
    busq_inv = st.text_input("🔍 Buscar por SKU o Descripción:")

    try:
        # Obtenemos la empresa actual de la sesión
        empresa_actual = st.session_state.get("usuario", "general")
        
        # Conectamos a la base de datos y filtramos por la empresa logueada
        conn = sqlite3.connect("mi_negocio.db")
        df_inventario = pd.read_sql_query(
            "SELECT * FROM inventario WHERE empresa_id = ?", 
            conn, 
            params=(empresa_actual,)
        )
        conn.close()

        if not df_inventario.empty:
            # Si escribes algo en la barra, filtramos la tabla
            if busq_inv:
                df_filtrado = df_inventario[
                    df_inventario['SKU'].astype(str).str.contains(busq_inv, case=False, na=False) | 
                    df_inventario['DESCRIPCION'].astype(str).str.contains(busq_inv, case=False, na=False)
                ]
                st.dataframe(df_filtrado, use_container_width=True)
            else:
                # Mostramos la tabla completa si no hay nada escrito
                st.dataframe(df_inventario, use_container_width=True)
                
            # Opcional: Un indicador rápido de productos totales cargados
            st.info(f"Total de registros en inventario: {len(df_inventario)}")
        else:
            st.warning("La base de datos está vacía. Sube un archivo en la pestaña...")
            
    except Exception as e:
        st.error(f"Error al cargar el inventario: {e}")
        
        try:
            # Conectamos a la base de datos y leemos la tabla inventario
            conn = sqlite3.connect("mi_negocio.db")
            df_inventario = pd.read_sql_query("SELECT * FROM inventario", conn)
            conn.close()
            
            if not df_inventario.empty:
                # Mostramos la tabla completa de forma interactiva
                st.dataframe(df_inventario, use_container_width=True)
                
                # Opcional: Un indicador rápido de productos totales cargados
                st.info(f"Total de registros en inventario: {len(df_inventario)}")
            else:
                st.warning("La base de datos está vacía. Sube un archivo en la pestaña 'Carga Masiva Excel'.")
                
        except Exception as e:
            st.info("Aún no hay una base de datos creada. Sube tu archivo Excel en la pestaña 'Carga Masiva Excel' para comenzar.")
        
    with tab2:
        st.subheader("Registrar Producto Individual")
        
        with st.form("form_nuevo_producto"):
            col1, col2 = st.columns(2)
            with col1:
                sku_nuevo = st.text_input("SKU / Código del Producto")
                desc_nueva = st.text_input("Descripción del Producto")
                ubicacion_nueva = st.text_input("Ubicación en Tienda / Almacén", value="CUA")
            with col2:
                costo_nuevo = st.number_input("Costo Unitario", min_value=0.0, format="%.4f")
                precio_nuevo = st.number_input("Precio de Venta", min_value=0.0, format="%.4f")
                cantidad_nueva = st.number_input("Cantidad Inicial (Stock)", min_value=0.0, format="%.2f")
            
            # Datos adicionales opcionales según tu estructura de Excel
            unid_medida = st.selectbox("Unidad de Medida", ["UNIDAD", "GALON", "LITRO", "ML", "METRO", "KG"])
            
            btn_guardar_prod = st.form_submit_button("💾 Guardar Producto en Inventario")
            
            if btn_guardar_prod:
                if sku_nuevo and desc_nueva:
                    try:
                        conn = sqlite3.connect("mi_negocio.db")
                        cursor = conn.cursor()
                        
                        # Insertar el nuevo producto respetando las columnas de tu tabla
                        cursor.execute('''
                            INSERT INTO inventario (SKU, DESCRIPCION, UBICACION, COSTO, PRECIO, "INV INICIAL", "UNID MEDIDA")
                            VALUES (?, ?, ?, ?, ?, ?, ?)
                        ''', (sku_nuevo, desc_nueva.upper(), ubicacion_nueva.upper(), costo_nuevo, precio_nuevo, cantidad_nueva, unid_medida))
                        
                        conn.commit()
                        conn.close()
                        st.success(f"¡El producto '{desc_nueva}' ha sido registrado exitosamente!")
                    except Exception as e:
                        st.error(f"Error al registrar el producto: {e}")
                else:
                    st.warning("Por lo menos debes rellenar el SKU y la Descripción del producto.")
        
    with tab3:
        st.subheader("Ajuste Físico de Inventario")
        st.markdown("Esta sección está restringida. Permite cargar o descargar inventario físico por diferencias de conteo, dejando un concepto y un responsable.")
        
        with st.form("form_ajuste_fisico"):
            # 1. SEGURIDAD: Clave de acceso
            clave_ingresada = st.text_input("Clave de Autorización", type="password")
            
            st.markdown("---")
            
            # 2. DATOS DEL AJUSTE
            col1, col2 = st.columns(2)
            with col1:
                sku_ajuste = st.text_input("SKU del Producto a Ajustar")
                tipo_movimiento = st.selectbox("Tipo de Ajuste", ["Carga (Sumar al inventario)", "Descarga (Restar del inventario)"])
                cantidad_ajuste = st.number_input("Cantidad a Ajustar", min_value=0.01, format="%.2f")
            with col2:
                concepto_ajuste = st.selectbox("Concepto", ["Diferencia en conteo físico", "Merma / Daño", "Robo / Extravío", "Error de carga anterior", "Devolución sin factura"])
                responsable = st.text_input("Responsable / Firma (Nombre y Apellido)")
                observacion_extra = st.text_input("Observación adicional (Opcional)")
            
            btn_ejecutar_ajuste = st.form_submit_button("⚖️ Aplicar Ajuste Físico")
            
            if btn_ejecutar_ajuste:
                # Clave temporal de administrador (puedes cambiarla por la que prefieras)
                CLAVE_AUTORIZADA = "Shaddai2021*" 
                
                if clave_ingresada == CLAVE_AUTORIZADA:
                    if sku_ajuste and responsable:
                        try:
                            conn = sqlite3.connect("mi_negocio.db")
                            cursor = conn.cursor()
                            
                            # Verificamos si el producto existe en la base de datos
                            cursor.execute('SELECT "INV INICIAL", DESCRIPCION FROM inventario WHERE SKU = ?', (sku_ajuste,))
                            resultado = cursor.fetchone()
                            
                            if resultado:
                                stock_actual = resultado[0]
                                desc_producto = resultado[1]
                                
                                # Calculamos el nuevo stock según sea carga o descarga
                                if "Carga" in tipo_movimiento:
                                    nuevo_stock = stock_actual + cantidad_ajuste
                                else:
                                    nuevo_stock = stock_actual - cantidad_ajuste
                                    if nuevo_stock < 0:
                                        nuevo_stock = 0 # Evitar stock negativo por seguridad
                                        
                                # Actualizamos el inventario en la tabla
                                cursor.execute('UPDATE inventario SET "INV INICIAL" = ? WHERE SKU = ?', (nuevo_stock, sku_ajuste))
                                
                                # Opcional: Podrías guardar un historial de auditoría si lo deseas luego
                                
                                conn.commit()
                                conn.close()
                                
                                st.success(f"✅ Ajuste realizado con éxito en '{desc_producto}'. Stock anterior: {stock_actual} | Nuevo Stock: {nuevo_stock}")
                                st.info(f"Registrado bajo el concepto de *{concepto_ajuste}* por el responsable: *{responsable}*.")
                            else:
                                conn.close()
                                st.error("❌ El SKU ingresado no se encuentra registrado en el inventario.")
                        except Exception as e:
                            st.error(f"Error al procesar el ajuste en la base de datos: {e}")
                    else:
                        st.warning("⚠️ Debes rellenar obligatoriamente el SKU y el nombre del Responsable/Firma.")
                else:
                    st.error("🔒 Clave de autorización incorrecta. No se puede realizar el ajuste.")
        
    with tab4:
        st.subheader("Carga Masiva de Inventario mediante Excel")
        st.markdown("Sube tu archivo de Excel para actualizar todo el inventario de una sola vez.")
        
        # 1. DESCARGA DE PLANTILLA
        df_plantilla = pd.DataFrame(columns=["SKU", "Nombre", "Cantidad", "Precio", "Costo"])
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df_plantilla.to_excel(writer, index=False, sheet_name='Inventario')
        processed_data = output.getvalue()
        
        st.download_button(
            label="📥 Descargar Plantilla de Excel",
            data=processed_data,
            file_name="plantilla_inventario_shaddai.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        
        st.markdown("---")
        
        
archivo_subido = st.file_uploader("Sube tu plantilla de Excel completada", type=["xlsx", "xls"])
        
if archivo_subido is not None:
            try:
                df_carga = pd.read_excel(archivo_subido)
                st.write("Vista previa de los datos cargados:")
                st.dataframe(df_carga.head())
                
                if st.button("💾 Procesar e Insertar en Base de Datos"):
                    # Limpiamos los nombres de las columnas para evitar espacios o errores
                    df_carga.columns = [str(c).strip().upper() for c in df_carga.columns]
                    
                    conn = sqlite3.connect("mi_negocio.db")
                    df_carga.to_sql("inventario", conn, if_exists="replace", index=False)
                    conn.close()
                    
                    st.success("¡Inventario cargado y guardado en la base de datos con éxito!")
                    st.rerun() # Esto recarga automáticamente la pantalla para que aparezca la tabla de una vez
                    
            except Exception as e:
                st.error(f"Error al procesar el archivo: {e}")
 

                sku_opciones = [f"{p[0]} - {p[1]}" for p in productos_inv] if productos_inv else ["SIN-SKU - PRODUCTO GENERAL"]
                prod_sel = st.selectbox("Seleccionar Producto (SKU - Descripción)", sku_opciones)

                col_i1, col_i2 = st.columns(2)
                with col_i1:
                    cantidad = st.number_input("Cantidad Comprada", min_value=0.01, value=1.00, step=1.00)
                with col_i2:
                    costo_unitario = st.number_input("Costo Unitario ($ sin IVA)", min_value=0.0, value=0.0, format="%.2f")

                submitted_compra = st.form_submit_button("🚀 Procesar y Registrar Compra en el Sistema")

                if submitted_compra:
                    if condicion == "Contado" and (not num_doc or not num_doc.strip()):
                        st.error("❌ ¡Atención! Al ser una compra de Contado, es obligatorio ingresar el número de factura o documento del proveedor.")
                    else:
                        from datetime import timedelta
                        subtotal = cantidad * costo_unitario
                        
                        if tipo_doc == "Factura Fiscal":
                            iva = subtotal * 0.16
                            porcentaje_ret = dic_prov[prov_seleccionado]["ret"]
                            retencion_iva = iva * (porcentaje_ret / 100.0)
                        else:
                            iva = 0.0
                            retencion_iva = 0.0

                        total_pagar = (subtotal + iva) - retencion_iva
                        
                        if condicion == "Crédito" and dias_cred > 0:
                            fecha_venc = fecha_compra + timedelta(days=int(dias_cred))
                        else:
                            fecha_venc = fecha_compra

                        sku_extraido = prod_sel.split(" - ")[0]
                        rif_prov_actual = dic_prov[prov_seleccionado]["rif"]
                        doc_final = num_doc.strip() if num_doc else "S/N (Crédito)"

                        cursor.execute('''
                            INSERT INTO compras (empresa_id, fecha, proveedor, rif_proveedor, num_documento, tipo_documento, condicion_pago, dias_credito, fecha_vencimiento, sku, cantidad, costo, subtotal, iva, retencion_iva, total_pagar)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        ''', (empresa_actual, str(fecha_compra), prov_seleccionado, rif_prov_actual, doc_final, tipo_doc, condicion, dias_cred, str(fecha_venc), sku_extraido, cantidad, costo_unitario, subtotal, iva, retencion_iva, total_pagar))

                        try:
                            cursor.execute('''
                                UPDATE inventario 
                                SET "INV INICIAL" = "INV INICIAL" + ? 
                                WHERE SKU = ? AND empresa_id = ?
                            ''', (cantidad, sku_extraido, empresa_actual))
                        except:
                            pass

                        if condicion == "Crédito":
                            cursor.execute('''
                                INSERT INTO cuentas_por_pagar (empresa_id, proveedor, rif_proveedor, num_documento, fecha_emision, fecha_vencimiento, monto_total, estado)
                                VALUES (?, ?, ?, ?, ?, ?, ?, 'Pendiente')
                            ''', (empresa_actual, prov_seleccionado, rif_prov_actual, doc_final, str(fecha_compra), str(fecha_venc), total_pagar))

                        conn.commit()
                        st.success(f"✅ ¡Compra a {condicion} registrada con éxito! Stock actualizado.")
                        st.rerun()

        st.markdown("### 📊 Historial de Compras Registradas")
        try:
            import pandas as pd
            df_historial = pd.read_sql("SELECT fecha, proveedor, num_documento, tipo_documento, condicion_pago, fecha_vencimiento, total_pagar FROM compras WHERE empresa_id = ? ORDER BY id DESC LIMIT 10", conn, params=(empresa_actual,))
            if not df_historial.empty:
                st.dataframe(df_historial, use_container_width=True)
            else:
                st.info("No hay compras registradas todavía.")
        except:
            st.info("Aún no se visualiza el historial.")
        finally:
            conn.close()

elif menu == "Cuentas por Pagar":
    st.header("💳 Gestión de Cuentas por Pagar")
    # 🌟 Definir la empresa activa aquí también
    empresa_actual = st.session_state.get("empresa_actual", st.session_state.get("empresa", "shaddai"))
    
    conn = sqlite3.connect("mi_negocio.db")
    cursor = conn.cursor()
    
    conn = sqlite3.connect("mi_negocio.db")
    cursor = conn.cursor()
    
    # Asegurar tabla cuentas_por_pagar
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS cuentas_por_pagar (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            empresa_id TEXT NOT NULL,
            proveedor TEXT,
            rif_proveedor TEXT,
            num_documento TEXT,
            fecha_emision TEXT,
            fecha_vencimiento TEXT,
            monto_total REAL,
            moneda_texto TEXT,
            tasa_aplicada REAL,
            estado TEXT DEFAULT 'Pendiente'
        )
    ''')
    try:
        cursor.execute("ALTER TABLE cuentas_por_pagar ADD COLUMN empresa_id TEXT DEFAULT 'shaddai'")
    except Exception:
        pass
    conn.commit()

    tab_pendientes, tab_pagadas = st.tabs(["📌 Facturas Pendientes por Pagar", "✅ Historial de Pagos / Liquidadas"])

    with tab_pendientes:
        st.subheader("Compromisos Crediticios Vigentes")
        
        import pandas as pd
        df_cxp = pd.read_sql("SELECT id, proveedor, rif_proveedor, num_documento, fecha_emision, fecha_vencimiento, monto_total, estado FROM cuentas_por_pagar WHERE empresa_id = ? AND estado = 'Pendiente'", conn, params=(empresa_actual,))
        
        if df_cxp.empty:
            st.info("🎉 ¡Excelente noticia! No hay cuentas por pagar pendientes en este momento.")
        else:
            st.dataframe(df_cxp, use_container_width=True)
            
            st.markdown("---")
            st.subheader("Registrar Abono o Pago de Factura")
            st.info("💡 Nota: Ingrese obligatoriamente la referencia bancaria del pago o el número de recibo manual emitido.")
            
            lista_facturas_pendientes = [f"ID: {row[0]} | Prov: {row[1]} | Doc: {row[3]} | Monto: {row[6]:,.2f}" for row in df_cxp.itertuples(index=False)]
            
            factura_a_pagar_sel = st.selectbox("Seleccione la Factura a Pagar / Abonar", lista_facturas_pendientes)
            
            if factura_a_pagar_sel:
                id_cxp = int(factura_a_pagar_sel.split(" | ")[0].replace("ID: ", ""))
                
                cursor.execute("SELECT monto_total, proveedor, num_documento FROM cuentas_por_pagar WHERE id = ? AND empresa_id = ?", (id_cxp, empresa_actual))
                datos_fact = cursor.fetchone()
                
                if datos_fact:
                    monto_actual_deuda = datos_fact[0]
                    st.write(f"Proveedor: {datos_fact[1]} | Documento N°: {datos_fact[2]} | Monto Pendiente: {monto_actual_deuda:,.2f}")
                    
                    ref_pago_cxp = st.text_input("Nro. de Referencia Bancaria o Recibo de Pago (OBLIGATORIO)", placeholder="Ej: Ref 987654 o Recibo #12")
                    
                    accion_pago = st.radio("Acción a realizar", ["Marcar como Pagada Totalmente", "Registrar Abono Parcial"])
                    
                    if accion_pago == "Marcar como Pagada Totalmente":
                        if st.button("💾 Liquidar Deuda por Completo"):
                            if not ref_pago_cxp.strip():
                                st.error("❌ ¡Atención! Debe ingresar el número de referencia o recibo del pago para liquidar la deuda.")
                            else:
                                cursor.execute("UPDATE cuentas_por_pagar SET estado = 'Pagada' WHERE id = ? AND empresa_id = ?", (id_cxp, empresa_actual))
                                conn.commit()
                                st.success(f"✅ ¡Deuda liquidada exitosamente usando la referencia/recibo: {ref_pago_cxp.strip()}!")
                                st.rerun()
                    else:
                        monto_abono = st.number_input("Monto del Abono", min_value=0.01, max_value=float(monto_actual_deuda), step=1.00, format="%.2f")
                        if st.button("💾 Registrar Abono"):
                            if not ref_pago_cxp.strip():
                                st.error("❌ ¡Atención! Debe ingresar el número de referencia o recibo del abono.")
                            else:
                                nuevo_monto = monto_actual_deuda - monto_abono
                                if nuevo_monto <= 0.01:
                                    cursor.execute("UPDATE cuentas_por_pagar SET estado = 'Pagada', monto_total = 0 WHERE id = ? AND empresa_id = ?", (id_cxp, empresa_actual))
                                    st.success(f"✅ ¡Deuda completamente liquidada con este abono! (Ref/Recibo: {ref_pago_cxp.strip()})")
                                else:
                                    cursor.execute("UPDATE cuentas_por_pagar SET monto_total = ? WHERE id = ? AND empresa_id = ?", (nuevo_monto, id_cxp, empresa_actual))
                                    st.success(f"✅ Abono registrado. Nuevo saldo pendiente: {nuevo_monto:,.2f} (Ref/Recibo: {ref_pago_cxp.strip()})")
                                conn.commit()
                                st.rerun()

    with tab_pagadas:
        st.subheader("Historial de Cuentas Liquidadas")
        df_pagadas = pd.read_sql("SELECT proveedor, rif_proveedor, num_documento, monto_total FROM cuentas_por_pagar WHERE empresa_id = ? AND estado = 'Pagada'", conn, params=(empresa_actual,))
        if not df_pagadas.empty:
            st.dataframe(df_pagadas, use_container_width=True)
        else:
            st.info("No hay facturas pagadas registradas en el historial.")
            
    conn.close()

elif menu == "Cuentas por Cobrar":
    st.header("💵 Gestión de Cuentas por Cobrar")
    
    # 🌟 Definir la empresa activa al entrar al módulo
    empresa_actual = st.session_state.get("empresa_actual", st.session_state.get("empresa", "shaddai"))
    
    conn = sqlite3.connect("mi_negocio.db")
    cursor = conn.cursor()
    
    # Asegurar que la tabla exista con el campo empresa_id
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS cuentas_por_cobrar (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            empresa_id TEXT,
            cliente TEXT,
            rif_cliente TEXT,
            num_documento TEXT,
            fecha_emision TEXT,
            fecha_vencimiento TEXT,
            monto_total REAL,
            moneda_texto TEXT,
            tasa_aplicada REAL,
            estado TEXT DEFAULT 'Pendiente'
        )
    ''')
    conn.commit()

    # Pestañas para organizar la visualización y los cobros
    tab_por_cobrar, tab_cobradas = st.tabs(["📌 Facturas Pendientes por Cobrar", "✅ Historial de Cobros / Liquidadas"])

    with tab_por_cobrar:
        st.subheader("Créditos Vigentes Otorgados a Clientes")
        
        # Consultar cuentas por cobrar pendientes filtradas por la empresa actual
        import pandas as pd
        df_cxc = pd.read_sql(
            "SELECT id, cliente, rif_cliente, num_documento, fecha_emision, fecha_vencimiento, monto_total, moneda_texto, tasa_aplicada, estado FROM cuentas_por_cobrar WHERE estado = 'Pendiente' AND empresa_id = ?", 
            conn, 
            params=(empresa_actual,)
        )
        
        if df_cxc.empty:
            st.info("🎉 No hay cuentas por cobrar pendientes en este momento. ¡Todo al día!")
        else:
            st.dataframe(df_cxc, use_container_width=True)
            
            st.markdown("---")
            st.subheader("Registrar Abono o Pago de Cliente")
            
            # Selector de factura pendiente para cobrar o abonar
            lista_facturas_cxc = [f"ID: {row[0]} | Cliente: {row[1]} | Doc: {row[3]} | Monto: {row[6]:,.2f}" for row in df_cxc.itertuples(index=False)]
            
            factura_a_cobrar_sel = st.selectbox("Seleccione la Factura del Cliente a Cobrar / Abonar", lista_facturas_cxc)
            
            if factura_a_cobrar_sel:
                # Extraer el ID seleccionado
                id_cxc = int(factura_a_cobrar_sel.split(" | ")[0].replace("ID: ", ""))
                
                # Obtener detalles de esa cuenta por cobrar validando la empresa
                cursor.execute("SELECT monto_total, cliente, num_documento FROM cuentas_por_cobrar WHERE id = ? AND empresa_id = ?", (id_cxc, empresa_actual))
                datos_cxc = cursor.fetchone()
                
                if datos_cxc:
                    monto_actual_saldo = datos_cxc[0]
                    st.write(f"Cliente: {datos_cxc[1]} | Documento N°: {datos_cxc[2]} | Saldo Pendiente: {monto_actual_saldo:,.2f}")
                    
                    accion_cobro = st.radio("Acción a realizar", ["Marcar como Pagada Totalmente (Liquidada)", "Registrar Abono Parcial"])
                    
                    if accion_cobro == "Marcar como Pagada Totalmente (Liquidada)":
                        if st.button("💾 Liquidar Deuda del Cliente"):
                            cursor.execute("UPDATE cuentas_por_cobrar SET estado = 'Pagada' WHERE id = ? AND empresa_id = ?", (id_cxc, empresa_actual))
                            conn.commit()
                            st.success("✅ ¡La cuenta del cliente ha sido marcada como Pagada exitosamente!")
                            st.rerun()
                    else:
                        monto_abono_cliente = st.number_input("Monto del Abono Recibido", min_value=0.01, max_value=float(monto_actual_saldo), step=1.00, format="%.2f")
                        if st.button("💾 Registrar Abono de Cliente"):
                            nuevo_saldo = monto_actual_saldo - monto_abono_cliente
                            if nuevo_saldo <= 0.01:
                                cursor.execute("UPDATE cuentas_por_cobrar SET estado = 'Pagada', monto_total = 0 WHERE id = ? AND empresa_id = ?", (id_cxc, empresa_actual))
                                st.success("✅ ¡Deuda del cliente completamente liquidada con este abono!")
                            else:
                                cursor.execute("UPDATE cuentas_por_cobrar SET monto_total = ? WHERE id = ? AND empresa_id = ?", (nuevo_saldo, id_cxc, empresa_actual))
                                st.success(f"✅ Abono registrado. Nuevo saldo por cobrar: {nuevo_saldo:,.2f}")
                            conn.commit()
                            st.rerun()

    with tab_cobradas:
        st.subheader("Historial de Créditos Cobrados")
        df_cobradas = pd.read_sql(
            "SELECT cliente, rif_cliente, num_documento, fecha_emision, fecha_vencimiento, monto_total, moneda_texto FROM cuentas_por_cobrar WHERE estado = 'Pagada' AND empresa_id = ?", 
            conn, 
            params=(empresa_actual,)
        )
        if not df_cobradas.empty:
            st.dataframe(df_cobradas, use_container_width=True)
        else:
            st.info("No hay facturas cobradas registradas en el historial.")
            
    conn.close()

elif menu == "Bancos":
    st.header("🏦 Bancos y tesoreria")


    # 🌟 Definir la empresa activa al entrar al módulo
    empresa_actual = st.session_state.get("empresa_actual", st.session_state.get("empresa", "shaddai"))
    
    conn = sqlite3.connect("mi_negocio.db")
    cursor = conn.cursor()

        # 🔍 DIAGNÓSTICO RÁPIDO DE BANCOS Y VENTAS
    with st.expander("🛠️ Diagnóstico de Conexión de Ventas y Bancos"):
        conn_diag = sqlite3.connect("mi_negocio.db")
        cursor_diag = conn_diag.cursor()
        
        st.write(f"*Empresa actual activa en sesión:* {empresa_actual}")
        
        # Ver los últimos movimientos registrados en la base de datos sin filtrar
        df_todos_movs = pd.read_sql("SELECT id, empresa_id, fecha, cuenta_destino, monto FROM movimientos_bancarios ORDER BY id DESC LIMIT 5", conn_diag)
        st.write("*Últimos 5 movimientos en la base de datos (Sin filtro):*")
        st.dataframe(df_todos_movs, use_container_width=True)
        
        # Ver las últimas ventas registradas
        try:
            df_todas_ventas = pd.read_sql("SELECT id, empresa_id, fecha, total, banco_metodo FROM ventas ORDER BY id DESC LIMIT 5", conn_diag)
            st.write("*Últimas 5 ventas en la base de datos:*")
            st.dataframe(df_todas_ventas, use_container_width=True)
        except Exception as e:
            st.warning(f"No se pudo leer la tabla ventas: {e}")
            
        conn_diag.close()
    
    # 1. Tabla para el saldo o movimientos de cuentas bancarias y Cashea (con empresa_id)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS movimientos_bancarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            empresa_id TEXT,
            fecha TEXT,
            cuenta_destino TEXT, -- Banesco, Venezuela, BNC, Cashea
            tipo_movimiento TEXT, -- Ingreso, Egreso
            concepto TEXT,
            referencia TEXT,
            monto REAL
        )
    ''')
    
    # 2. Tabla específica para operaciones Cashea (con empresa_id)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS operaciones_cashea (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            empresa_id TEXT,
            fecha TEXT,
            cliente TEXT,
            rif_cliente TEXT,
            nivel_cashea TEXT,
            monto_total_venta REAL,
            inicial_pagada REAL,
            monto_financiado REAL,
            estado_cashea TEXT DEFAULT 'Pendiente Liquidación'
        )
    ''')
    conn.commit()

    # Pestañas de organización
    tab_saldos, tab_total, tab_egresos, tab_cashea, tab_historico = st.tabs([
        "📊 Resumen en Bolívares", 
        "💰 Totalización General y Divisas",
        "📤 Registrar Gasto / Salida", 
        "📱 Control Especial Cashea", 
        "📜 Historial de Movimientos"
    ])

    with tab_saldos:
        st.subheader("Saldo Actual por Entidad (En Bolívares)")
        
        # Desplegable para registrar saldo inicial en Bs filtrado por empresa
        with st.expander("⚙️ Registrar / Ajustar Saldo Inicial en Bancos (Bs)"):
            with st.form("form_saldo_inicial"):
                banco_inicial = st.selectbox("Seleccione Banco o Cuenta", ["Banesco", "Venezuela", "BNC", "Cashea"])
                monto_inicial = st.number_input("Monto Inicial en Bolívares (Bs.)", min_value=0.00, step=1.00, format="%.2f")
                obs_inicial = st.text_input("Observación", value="Saldo inicial de arrastre")
                
                if st.form_submit_button("💾 Guardar Saldo Inicial"):
                    cursor.execute('''
                        INSERT INTO movimientos_bancarios (empresa_id, fecha, cuenta_destino, tipo_movimiento, concepto, referencia, monto)
                        VALUES (?, date('now'), ?, 'Ingreso', ?, 'INICIAL', ?)
                    ''', (empresa_actual, banco_inicial, obs_inicial, monto_inicial))
                    conn.commit()
                    st.success(f"✅ Saldo inicial de Bs. {monto_inicial:,.2f} registrado en {banco_inicial}.")
                    st.rerun()
        
        # Consulta y cálculo de saldos netos en Bolívares filtrados por empresa actual
        import pandas as pd
        df_movs = pd.read_sql("SELECT cuenta_destino, tipo_movimiento, monto FROM movimientos_bancarios WHERE LOWER(empresa_id) LIKE '%shaddai%'", conn)
        
        cuentas_empresa = ["Banesco", "Venezuela", "BNC", "Cashea"]
        
        saldos_data = []
        for cuenta in cuentas_empresa:
            saldo_cuenta = 0.0
            if not df_movs.empty:
                df_cta = df_movs[df_movs['cuenta_destino'] == cuenta]
                for _, row in df_cta.iterrows():
                    m = row['monto']
                    tipo = row['tipo_movimiento']
                    if tipo == 'Ingreso':
                        saldo_cuenta += m
                    else:
                        saldo_cuenta -= m
            
            saldos_data.append({
                "Entidad / Banco": cuenta, 
                "Saldo Disponible (Bs.)": saldo_cuenta
            })
            
        df_saldos = pd.DataFrame(saldos_data)
        st.dataframe(df_saldos, use_container_width=True, hide_index=True)

    with tab_total:
        st.subheader("💰 Consolidado General y Equivalente en Divisas")
        st.markdown("Suma de todos los bancos en Bolívares y su conversión global a dólares según la tasa del día.")
        
        tasa_dia = st.number_input("Ingrese la Tasa del Día (Ej: BCV o Paralelo)", min_value=1.0, value=784.66, step=0.01)
        
        if not df_saldos.empty:
            total_bs_general = df_saldos["Saldo Disponible (Bs.)"].sum()
            equivalente_dolares = total_bs_general / tasa_dia if tasa_dia > 0 else 0.0
            
            col_t1, col_t2 = st.columns(2)
            with col_t1:
                st.metric("Total General en Bolívares", f"Bs. {total_bs_general:,.2f}")
            with col_t2:
                st.metric("Equivalente Total en Divisas", f"$ {equivalente_dolares:,.2f}")
                
            st.markdown("---")
            st.info(f"📊 Resumen Global: Sus cuentas suman un total de Bs. {total_bs_general:,.2f}. Aplicando la tasa de *{tasa_dia}, representa un valor estimado de $ {equivalente_dolares:,.2f}*.")
        else:
            st.warning("⚠️ No hay datos suficientes para la totalización.")

    with tab_egresos:
        st.subheader("Registro Manual de Egresos / Salidas de Dinero (En Bolívares)")
        
        with st.form("form_egreso_banco"):
            col1, col2 = st.columns(2)
            with col1:
                fecha_egreso = st.date_input("Fecha del Movimiento")
                banco_origen = st.selectbox("Entidad de Origen (Salida)", ["Banesco", "Venezuela", "BNC"])
                tipo_gasto = st.selectbox("Tipo de Salida / Concepto", [
                    "Pago a Proveedor", 
                    "Gastos Operativos (Local/Galpón)", 
                    "Servicios (Luz, Internet, etc.)", 
                    "Nomina / Personal", 
                    "Caja Chica / Retiro", 
                    "Otros Gastos"
                ])
            with col2:
                monto_egreso = st.number_input("Monto del Egreso en Bs.", min_value=0.01, step=1.00, format="%.2f")
                ref_egreso = st.text_input("Nro. de Referencia / Comprobante")
                
            detalle_gasto = st.text_area("Descripción detallada del gasto o motivo")
            
            if st.form_submit_button("💾 Registrar Salida de Dinero"):
                if monto_egreso > 0 and ref_egreso:
                    cursor.execute('''
                        INSERT INTO movimientos_bancarios (empresa_id, fecha, cuenta_destino, tipo_movimiento, concepto, referencia, monto)
                        VALUES (?, ?, ?, 'Egreso', ?, ?, ?)
                    ''', (empresa_actual, str(fecha_egreso), banco_origen, f"{tipo_gasto}: {detalle_gasto}", ref_egreso, monto_egreso))
                    conn.commit()
                    st.success(f"✅ Egreso de Bs. {monto_egreso:,.2f} registrado en {banco_origen}.")
                    st.rerun()
                else:
                    st.warning("⚠️ Complete el monto y el número de referencia.")

    with tab_cashea:
        st.subheader("📱 Módulo de Control y Retenciones Cashea")
        df_cashea_pend = pd.read_sql("SELECT id, fecha, cliente, rif_cliente, nivel_cashea, monto_total_venta, inicial_pagada, monto_financiado FROM operaciones_cashea WHERE estado_cashea = 'Pendiente Liquidación' AND empresa_id = ?", conn, params=(empresa_actual,))
        
        if df_cashea_pend.empty:
            st.info("No hay operaciones de Cashea pendientes de liquidación para esta empresa.")
        else:
            st.dataframe(df_cashea_pend, use_container_width=True)
            st.markdown("---")
            lista_liq = [f"ID: {row[0]} | Cliente: {row[2]} | Financiado por Recibir: Bs. {row[7]:,.2f}" for row in df_cashea_pend.itertuples(index=False)]
            sel_liq = st.selectbox("Seleccione operación Cashea liquidada", lista_liq)
            
            if sel_liq:
                id_cashea = int(sel_liq.split(" | ")[0].replace("ID: ", ""))
                cursor.execute("SELECT monto_financiado, cliente FROM operaciones_cashea WHERE id = ? AND empresa_id = ?", (id_cashea, empresa_actual))
                datos_c = cursor.fetchone()
                if datos_c:
                    monto_a_ingresar = datos_c[0]
                    banco_destino_cashea = st.selectbox("Banco receptor de la liquidación", ["Banesco", "Venezuela", "BNC"])
                    if st.button("✅ Confirmar Recepción de Fondos Cashea"):
                        cursor.execute("UPDATE operaciones_cashea SET estado_cashea = 'Liquidado' WHERE id = ? AND empresa_id = ?", (id_cashea, empresa_actual))
                        cursor.execute('''
                            INSERT INTO movimientos_bancarios (empresa_id, fecha, cuenta_destino, tipo_movimiento, concepto, referencia, monto)
                            VALUES (?, date('now'), ?, 'Ingreso', ?, 'Liquidacion Cashea', ?)
                        ''', (empresa_actual, banco_destino_cashea, f"Liquidacion Cashea - Cliente: {datos_c[1]}", monto_a_ingresar))
                        conn.commit()
                        st.success("🎉 ¡Fondos de Cashea acreditados en bolívares con éxito!")
                        st.rerun()

    with tab_historico:
        st.subheader("Historial Completo de Movimientos Bancarios")
        df_hist = pd.read_sql("SELECT fecha, cuenta_destino, tipo_movimiento, concepto, referencia, monto FROM movimientos_bancarios WHERE empresa_id = ? ORDER BY id DESC", conn, params=(empresa_actual,))
        if not df_hist.empty:
            st.dataframe(df_hist, use_container_width=True)
        else:
            st.info("Aún no hay movimientos registrados para esta empresa.")
            
    conn.close()

elif menu == "Gastos":
    st.header("📤 Módulo de Gestión de Gastos")
    st.markdown("Registro y clasificación de salidas, costos fijos, variables y obligaciones tributarias descontadas directamente de los bancos.")
    
    # 🌟 Definir la empresa activa al entrar al módulo
    empresa_actual = st.session_state.get("empresa_actual", st.session_state.get("empresa", "shaddai"))
    
    conn = sqlite3.connect("mi_negocio.db")
    cursor = conn.cursor()
    
    # Tabla específica para el módulo de gastos con empresa_id
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS gastos_negocio (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            empresa_id TEXT,
            fecha TEXT,
            banco_origen TEXT,
            categoria TEXT,
            subcategoria TEXT,
            referencia TEXT,
            monto REAL,
            descripcion TEXT
        )
    ''')
    conn.commit()

    # Pestañas del módulo de Gastos
    tab_reg_gasto, tab_hist_gasto = st.tabs(["➕ Registrar Gasto Bancario", "📜 Historial y Reporte de Gastos"])

    with tab_reg_gasto:
        st.subheader("Registrar Nueva Salida / Gasto (Post-Pago)")
        st.info("💡 Nota: Realice primero el pago y tenga a la mano el comprobante. Si no hay número de referencia o recibo físico, el sistema no permitirá el registro.")
        
        # Selección de categoría principal
        categoria_g = st.selectbox("Seleccione la Categoría Principal del Gasto", [
            "Gastos Fijos", 
            "Gastos Variables / Extraordinarios", 
            "Impuestos y Tributos (Ley)"
        ])
        
        col1, col2 = st.columns(2)
        with col1:
            fecha_gasto = st.date_input("Fecha en que se efectuó el pago")
            banco_salida = st.selectbox("Banco o Medio de Origen del Dinero", ["Banesco", "Venezuela", "BNC", "Efectivo Caja"])
        
        with col2:
            monto_g = st.number_input("Monto Pagado en Bolívares (Bs.)", min_value=0.01, step=1.00, format="%.2f")
            # Campo obligatorio de referencia / recibo
            ref_g = st.text_input("Nro. de Referencia Bancaria / Recibo Manual (OBLIGATORIO)", placeholder="Ej: Ref 123456 o Recibo #0045")
        
        # Campo dinámico según la categoría elegida
        if categoria_g == "Gastos Fijos":
            sub_g = st.selectbox("Concepto Fijo", ["Nómina / Personal", "Electricidad (Corpoelec)", "Aseo Urbano", "Servicio de Agua", "Alquiler"])
        elif categoria_g == "Gastos Variables / Extraordinarios":
            sub_g = st.text_input("Escriba el Nombre / Concepto del Gasto Variable", placeholder="Ej: Gastos de representación, reparación...")
        else:
            sub_g = st.selectbox("Tributo / Obligación", ["SENIAT (IVA / ISLR)", "Hacienda Municipal", "Seguro Social (IVSS / FAOV / INCES)"])

        detalle_g = st.text_area("Descripción detallada o beneficiario (Ej: A nombre de quién, motivo, etc.)")
        
        if st.button("💾 Registrar Gasto en el Sistema"):
            # Validación estricta: Si no colocó referencia o recibo, no lo deja pasar
            if not ref_g.strip():
                st.error("❌ ¡Atención! No puede registrar el gasto sin un número de referencia bancaria o recibo de pago válido.")
            elif monto_g <= 0:
                st.warning("⚠️ El monto debe ser mayor a cero.")
            else:
                # 1. Guardar en la tabla de gastos del negocio asociado a la empresa actual
                cursor.execute('''
                    INSERT INTO gastos_negocio (empresa_id, fecha, banco_origen, categoria, subcategoria, referencia, monto, descripcion)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (empresa_actual, str(fecha_gasto), banco_salida, categoria_g, sub_g, ref_g.strip(), monto_g, detalle_g))
                
                # 2. Reflejar automáticamente el egreso en la tesorería de la empresa si salió de un banco
                if banco_salida != "Efectivo Caja":
                    concepto_mov = f"[{categoria_g}] {sub_g}: {detalle_g}"
                    cursor.execute('''
                        INSERT INTO movimientos_bancarios (empresa_id, fecha, cuenta_destino, tipo_movimiento, concepto, referencia, monto)
                        VALUES (?, ?, ?, 'Egreso', ?, ?, ?)
                    ''', (empresa_actual, str(fecha_gasto), banco_salida, concepto_mov, ref_g.strip(), monto_g))
                
                conn.commit()
                st.success(f"✅ Gasto por Bs. {monto_g:,.2f} registrado y validado con éxito (Ref/Recibo: {ref_g}).")
                st.rerun()

    with tab_hist_gasto:
        st.subheader("Historial de Gastos Registrados")
        import pandas as pd
        df_gastos = pd.read_sql("SELECT fecha, banco_origen, categoria, subcategoria, referencia, monto, descripcion FROM gastos_negocio WHERE empresa_id = ? ORDER BY id DESC", conn, params=(empresa_actual,))
        
        if not df_gastos.empty:
            st.dataframe(df_gastos, use_container_width=True)
            
            # Resumen rápido por categoría
            st.markdown("---")
            st.subheader("📊 Totales por Categoría de Gasto")
            resumen_cat = df_gastos.groupby("categoria")["monto"].sum().reset_index()
            resumen_cat.columns = ["Categoría", "Total Gastado (Bs.)"]
            st.dataframe(resumen_cat, use_container_width=True, hide_index=True)
        else:
            st.info("Aún no hay gastos registrados en el sistema para esta empresa.")
            
    conn.close()

elif menu == "Reportes":
    st.header("📊 Módulo Gerencial de Reportes y Estadísticas")
    st.markdown("Resumen financiero, comercial y operativo del negocio en tiempo real.")
    
    # 🌟 Definir la empresa activa al entrar al módulo
    empresa_actual = st.session_state.get("empresa_actual", st.session_state.get("empresa", "shaddai"))
    
    import sqlite3
    import pandas as pd
    from datetime import datetime
    
    conn = sqlite3.connect("mi_negocio.db")
    cursor = conn.cursor()
    
    # Selector de Mes y Año para filtrar los reportes
    col_f1, col_f2 = st.columns(2)
    with col_f1:
        mes_filtro = st.selectbox("Seleccionar Mes", ["01", "02", "03", "04", "05", "06", "07", "08", "09", "10", "11", "12"], index=datetime.now().month - 1)
    with col_f2:
        anio_filtro = st.text_input("Año", value=str(datetime.now().year))
    
    periodo_str = f"{anio_filtro}-{mes_filtro}"
    
    st.markdown("---")
    
    # 1. SECCIÓN DE VENTAS (Filtrado por empresa_id)
    st.subheader("💰 Resumen Comercial (Ventas)")
    try:
        cursor.execute("SELECT SUM(total) FROM ventas WHERE fecha LIKE ? AND empresa_id = ?", (f"{periodo_str}%", empresa_actual))
        total_ventas_mes = cursor.fetchone()[0] or 0.0
        
        cursor.execute("""
            SELECT sku, SUM(cantidad) as total_cant 
            FROM ventas 
            WHERE fecha LIKE ? AND empresa_id = ? 
            GROUP BY sku 
            ORDER BY total_cant DESC 
            LIMIT 1
        """, (f"{periodo_str}%", empresa_actual))
        prod_vendido = cursor.fetchone()
        mas_vendido = f"{prod_vendido[0]} (Cant: {prod_vendido[1]})" if prod_vendido else "Sin registros en el período"

        cursor.execute("""
            SELECT sku, SUM((precio_unitario - costo_unitario) * cantidad) as ganancia_total 
            FROM ventas 
            WHERE fecha LIKE ? AND empresa_id = ? 
            GROUP BY sku 
            ORDER BY ganancia_total DESC 
            LIMIT 1
        """, (f"{periodo_str}%", empresa_actual))
        prod_ganancia = cursor.fetchone()
        mayor_ganancia = f"{prod_ganancia[0]} (Ganancia: Bs. {prod_ganancia[1]:,.2f})" if prod_ganancia and prod_ganancia[1] else "Sin registros suficientes"

    except Exception as e:
        total_ventas_mes = 0.0
        mas_vendido = "Calculándose..."
        mayor_ganancia = "Calculándose..."

    col_v1, col_v2, col_v3 = st.columns(3)
    col_v1.metric("Total Ventas del Mes", f"Bs. {total_ventas_mes:,.2f}")
    col_v2.metric("Producto Más Vendido", mas_vendido)
    col_v3.metric("Mayor Margen de Ganancia", mayor_ganancia)

    st.markdown("---")

    # 2. SECCIÓN DE COMPRAS Y PROVEEDORES (Filtrado por empresa_id)
    st.subheader("🛒 Resumen de Adquisiciones (Compras)")
    try:
        cursor.execute("SELECT SUM(total_pagar) FROM compras WHERE fecha LIKE ? AND empresa_id = ?", (f"{periodo_str}%", empresa_actual))
        total_compras_mes = cursor.fetchone()[0] or 0.0

        cursor.execute("""
            SELECT sku, proveedor, SUM(cantidad) as cant_comprada 
            FROM compras 
            WHERE fecha LIKE ? AND empresa_id = ? 
            GROUP BY sku, proveedor 
            ORDER BY cant_comprada DESC 
            LIMIT 1
        """, (f"{periodo_str}%", empresa_actual))
        compra_frecuente = cursor.fetchone()
        prod_proveedor_frecuente = f"SKU: {compra_frecuente[0]} | Prov: {compra_frecuente[1]} (Cant: {compra_frecuente[2]})" if compra_frecuente else "Sin compras registradas"
    except Exception as e:
        total_compras_mes = 0.0
        prod_proveedor_frecuente = "Sin registros"

    col_c1, col_c2 = st.columns(2)
    col_c1.metric("Total Compras del Mes", f"Bs. {total_compras_mes:,.2f}")
    col_c2.metric("Producto más Comprado y Proveedor", prod_proveedor_frecuente)

    st.markdown("---")

    # 3. SECCIÓN DE GASTOS (Usando gastos_negocio y filtrado por empresa_id)
    st.subheader("📉 Control de Gastos Operativos")
    try:
        cursor.execute("SELECT SUM(monto) FROM gastos_negocio WHERE fecha LIKE ? AND empresa_id = ?", (f"{periodo_str}%", empresa_actual))
        total_gastos = cursor.fetchone()[0] or 0.0

        cursor.execute("SELECT SUM(monto) FROM gastos_negocio WHERE categoria LIKE '%Fijo%' AND fecha LIKE ? AND empresa_id = ?", (f"{periodo_str}%", empresa_actual))
        gastos_fijos = cursor.fetchone()[0] or 0.0

        cursor.execute("SELECT SUM(monto) FROM gastos_negocio WHERE categoria LIKE '%Variable%' AND fecha LIKE ? AND empresa_id = ?", (f"{periodo_str}%", empresa_actual))
        gastos_variables = cursor.fetchone()[0] or 0.0
    except Exception as e:
        total_gastos = 0.0
        gastos_fijos = 0.0
        gastos_variables = 0.0

    col_g1, col_g2, col_g3 = st.columns(3)
    col_g1.metric("Total Gastos del Mes", f"Bs. {total_gastos:,.2f}")
    col_g2.metric("Gastos Fijos", f"Bs. {gastos_fijos:,.2f}")
    col_g3.metric("Gastos Variables", f"Bs. {gastos_variables:,.2f}")

    st.markdown("---")

    # 4. SECCIÓN DE MONEDAS Y TASA
    st.subheader("💵 Variación del Dólar y Tasas")
    try:
        df_tasas = pd.read_sql("SELECT * FROM tasas WHERE empresa_id = ? ORDER BY fecha DESC LIMIT 5", conn, params=(empresa_actual,))
        if not df_tasas.empty:
            st.dataframe(df_tasas, use_container_width=True)
        else:
            st.info("💡 No hay registros históricos de variación de tasas almacenados todavía para esta empresa.")
    except Exception as e:
        st.info("💡 Módulo de seguimiento de tasas listo para sincronizar.")

    conn.close()
