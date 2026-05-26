import streamlit as st
import pandas as pd
import requests
from datetime import datetime
import os
import base64

# ==============================================================================
# 1. CONFIGURACIÓN DE LA PÁGINA Y PANEL DE ESTILOS CSS
# ==============================================================================
icono_pestana = "logoBlumare.ico" if os.path.exists("logoBlumare.ico") else "logoBlumare.jpeg"
st.set_page_config(page_title="Blumare - SGE", page_icon=icono_pestana, layout="wide")

st.markdown("""
    <style>
    [data-testid="stHeader"] { display: none !important; }
    [data-testid="stToolbar"] { display: none !important; }
    .stAppDeployButton { display: none !important; }
    #MainMenu { display: none !important; }
    footer { display: none !important; }
    div[class*="viewerBadge"], [data-testid="stAppCreatorBadge"] { display: none !important; }
    
    .stApp { background-color: #0f172a; }
    .stTextInput > div > div > input, .stSelectbox > div > div > div {
        background-color: #1e293b !important;
        border: 1px solid #334155 !important;
        border-radius: 8px !important;
        color: #f8fafc !important;
    }
    
    div.stButton > button {
        border-radius: 8px !important;
        font-weight: 800 !important;
        border: none !important;
        transition: transform 0.1s ease !important;
    }
    div.stButton > button:active { transform: scale(0.98) !important; }
    div.stButton > button[kind="primary"] { background-color: #10b981 !important; color: white !important; }
    div.stButton > button[kind="primary"]:hover { background-color: #059669 !important; }
    div.stButton > button[kind="secondary"] { background-color: #3b82f6 !important; color: white !important; }
    div.stButton > button[kind="secondary"]:hover { background-color: #2563eb !important; }
    </style>
    """, unsafe_allow_html=True)

URL_API = "https://script.google.com/macros/s/AKfycbys2ymG2Ad5av2jtR3LFttFiJPkQS2LfiOGwuw7-RynhbuPvEE9R5G90xeS_bofoi-CCg/exec"

# ==============================================================================
# INICIALIZACIÓN ESTRICTA DEL ESTADO DE SESIÓN PARA LIMPIEZA DE FORMULARIOS
# ==============================================================================
if 'inventario_lotes' not in st.session_state: st.session_state.inventario_lotes = []
if 'nombres_productos' not in st.session_state: st.session_state.nombres_productos = []
if 'carrito_ventas' not in st.session_state: st.session_state.carrito_ventas = []
if 'precios_venta' not in st.session_state: st.session_state.precios_venta = {}

# Variables para limpiar los campos del Punto de Venta
if 'vta_cliente' not in st.session_state: st.session_state.vta_cliente = ""
if 'vta_placa' not in st.session_state: st.session_state.vta_placa = "Seleccione un vehículo"
if 'vta_prod' not in st.session_state: st.session_state.vta_prod = "Seleccione un producto"
if 'vta_lote' not in st.session_state: st.session_state.vta_lote = "Seleccione un lote"
if 'vta_cant' not in st.session_state: st.session_state.vta_cant = 0.0

# ==============================================================================
# 2. EXTRACTORES CON CACHÉ
# ==============================================================================
@st.cache_data(ttl=300)
def cargar_catalogo_nube():
    try:
        res = requests.get(f"{URL_API}?tipo_operacion=ObtenerProductos", timeout=10)
        return res.json() if isinstance(res.json(), list) else []
    except: return []

@st.cache_data(ttl=300)
def cargar_precios_nube():
    try:
        res = requests.get(f"{URL_API}?tipo_operacion=ObtenerPreciosVenta", timeout=10)
        datos = res.json()
        return datos if isinstance(datos, dict) else {}
    except: return {}

@st.cache_data(ttl=300)
def cargar_existencias_nube(sede):
    try:
        res = requests.get(f"{URL_API}?sede={sede}", timeout=10)
        datos = res.json()
        if isinstance(datos, list):
            return [{"Producto": d[0], "Stock": float(d[1]), "Sede": d[2], "Costo": float(d[3]), "ID_Lote": d[4]} for d in datos]
        return []
    except: return []

@st.cache_data(ttl=300)
def cargar_historico_ventas():
    try:
        res = requests.get(f"{URL_API}?tipo_operacion=ObtenerDespachos", timeout=12)
        return res.json() if isinstance(res.json(), list) else []
    except: return []

@st.cache_data(ttl=300)
def cargar_vehiculos():
    try:
        res = requests.get(f"{URL_API}?tipo_operacion=ObtenerVehiculos", timeout=10)
        datos = res.json()
        if isinstance(datos, list):
            if len(datos) > 0 and isinstance(datos[0], list):
                return [str(d[0]).strip() for d in datos if str(d[0]).strip() not in ["Placa", ""]]
            else:
                return [str(d).strip() for d in datos if str(d).strip() not in ["Placa", ""]]
        return []
    except: return []

st.session_state.nombres_productos = cargar_catalogo_nube()
st.session_state.precios_venta = cargar_precios_nube()

# ==============================================================================
# 3. ENCABEZADO Y PESTAÑAS
# ==============================================================================
nombre_logo = "logoBlumare.jpeg"
if os.path.exists(nombre_logo):
    with open(nombre_logo, "rb") as image_file:
        encoded_string = base64.b64encode(image_file.read()).decode()
    logo_html = f'<img src="data:image/jpeg;base64,{encoded_string}" width="55" style="border-radius: 8px; box-shadow: 0 4px 8px rgba(0,0,0,0.5);">'
else:
    logo_html = "🏢" 

col_logo, col_sync = st.columns([8, 2])
with col_logo:
    st.markdown(
        f"""
        <div style="display: flex; align-items: center; justify-content: flex-start; gap: 15px; margin-bottom: 5px; margin-top: 5px;">
            {logo_html}
            <h1 style='color: #f8fafc; margin: 0; font-weight: 800; letter-spacing: 1px; font-size: 32px;'>SISTEMA INTEGRAL BLUMARE</h1>
        </div>
        """, unsafe_allow_html=True
    )
with col_sync:
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("🔄 Sincronizar Datos", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

st.markdown("<hr style='border-color: #334155; margin-top: 10px; margin-bottom: 25px;'>", unsafe_allow_html=True)

tab1, tab2, tab3, tab4 = st.tabs(["📥 Entrada de Mercancía", "📦 Inventario", "🛒 Punto de Venta", "📊 Análisis de Utilidades"])

# ------------------------------------------------------------------------------
# MÓDULO 1: ENTRADA DE MERCANCÍA
# ------------------------------------------------------------------------------
with tab1:
    col_izq, col_der = st.columns([1, 1])
    with col_izq:
        st.subheader("DATOS DE ENTRADA")
        sede_ent = st.radio("Sede:", ["Cali", "Buenaventura"], horizontal=True)
        fecha_ent = st.text_input("Fecha (AAAAMMDD):", value=datetime.now().strftime("%Y%m%d"))
        prod_ent = st.selectbox("Producto:", ["Seleccione un producto"] + st.session_state.nombres_productos)
        
        col_lbs, col_precio = st.columns(2)
        lbs_ent = col_lbs.number_input("Libras (LBS):", min_value=0.0, value=0.0, step=10.0)
        precio_lb_ent = col_precio.number_input("Precio Unitario:", min_value=0.0, value=0.0, step=1.0)
        trm_ent = st.number_input("TRM (Tasa de Cambio - Si aplica):", min_value=0.0, value=0.0, step=50.0)

    es_fresco = "FRESCO" in prod_ent.upper()
    es_plaqueta = "PLAQUETA" in prod_ent.upper()
    kgs = lbs_ent / 2.2 if lbs_ent > 0 else 0
    c_proceso, c_logistica, peso_final, c_mp_cop, c_mp_usd = 0, 0, 0, 0, 0
    p_desc, p_pyd, p_hid, p_sec, p_gla = 0, 0, 0, 0, 0

    if prod_ent != "Seleccione un producto":
        if es_plaqueta:
            p_desc = kgs * 0.97; p_pyd = p_desc * 0.82; p_hid = p_pyd * 1.25
            c_proceso = round(p_hid * 4500, 0); peso_final = p_hid
            c_logistica = round(kgs * 2200, 0)
        elif es_fresco:
            p_pyd = kgs * 0.82; p_hid = p_pyd * 1.26; p_sec = p_hid * 0.97; p_gla = p_sec / 0.7
            c_proceso = round(p_gla * 6500, 0); peso_final = p_gla
        else:
            p_desc = kgs * 0.97; p_pyd = p_desc * 0.82; p_hid = p_pyd * 1.26; p_sec = p_hid * 0.97; p_gla = p_sec / 0.7
            c_proceso = round(p_gla * 6500, 0); peso_final = p_gla
            c_logistica = round(kgs * 2200, 0)
            
        c_mp_usd = lbs_ent * precio_lb_ent
        c_mp_cop = kgs * precio_lb_ent if es_fresco else round(c_mp_usd * trm_ent, 0)
    
    total_lote = c_mp_cop + c_logistica + c_proceso
    u_kg = total_lote / peso_final if peso_final > 0 else 0

    with col_der:
        st.subheader("PROCESO DE PLANTA (KGS)")
        st.info(f"Rendimiento calculado para: **{prod_ent}**")
        c1, c2 = st.columns(2)
        c1.metric("1. Descongelación", f"{p_desc:,.2f} KGS")
        c2.metric("2. Pelado/Desvenado", f"{p_pyd:,.2f} KGS")
        c1.metric("3. Hidratación", f"{p_hid:,.2f} KGS")
        c2.metric("4. Secado", f"{p_sec:,.2f} KGS")
        c1.metric("5. Glaseo", f"{p_gla:,.2f} KGS")

    st.markdown("### RESUMEN DE COSTOS")
    rc1, rc2, rc3, rc4 = st.columns(4)
    rc1.metric("Peso Base KGS", f"{kgs:,.2f}")
    rc2.metric("Costo Materia Prima", f"$ {c_mp_cop:,.0f} COP")
    rc3.metric("Costo Proceso + Logística", f"$ {c_proceso + c_logistica:,.0f} COP")
    rc4.metric("Costo TOTAL Lote", f"$ {total_lote:,.0f} COP", f"$ {u_kg:,.2f} / KG")

    if st.button("🚀 REGISTRAR ENTRADA EN BODEGA", type="primary", use_container_width=True):
        if prod_ent == "Seleccione un producto" or lbs_ent <= 0:
            st.warning("Completa el producto y las libras antes de registrar.")
        else:
            datos_compra = {
                "tipo_operacion": "RegistrarCompra", "id_venta": f"CMP-{int(datetime.now().timestamp())}",
                "fecha_hora": fecha_ent, "sede_despacho": sede_ent, "cliente": "PROVEEDOR",
                "producto": prod_ent, "libras": lbs_ent, "precio_materia_prima": precio_lb_ent,
                "descongelacion": p_desc, "pelado_desvenado": p_pyd, "hidratacion": p_hid,
                "secado": p_sec, "glaseo": p_gla, "id_lote_origen": f"{fecha_ent}_{prod_ent}",
                "cantidad_kgs": kgs, "materia_prima_usd": c_mp_usd, "trm": trm_ent,
                "materia_prima_cop": c_mp_cop, "logistica_envio": c_logistica, "costo_proceso_final": c_proceso,
                "ingreso_total_cop": total_lote, "precio_venta_cop": u_kg
            }
            with st.spinner("Enviando a la nube..."):
                res = requests.post(URL_API, json=datos_compra)
                if res.status_code == 200:
                    st.success("¡Registro Completo! Sábana mapeada en Historico_Compras.")
                    st.cache_data.clear()
                else:
                    st.error("Error al registrar en la base de datos.")

# ------------------------------------------------------------------------------
# MÓDULO 2: INVENTARIO POR LOTES
# ------------------------------------------------------------------------------
with tab2:
    st.subheader("CONTROL DE EXISTENCIAS POR LOTE")
    sede_inv = st.radio("Sede a consultar:", ["Cali", "Buenaventura"], horizontal=True, key="sede_inv")
    inventario_actual = cargar_existencias_nube(sede_inv)
    
    if inventario_actual:
        df_inv = pd.DataFrame(inventario_actual)
        kpi1, kpi2 = st.columns(2)
        kpi1.metric("Stock Total", f"{df_inv['Stock'].sum():,.2f} KGS")
        kpi2.metric("Capital en Bodega", f"$ {(df_inv['Stock'] * df_inv['Costo']).sum():,.0f} COP")
        st.dataframe(df_inv, use_container_width=True, hide_index=True)
    else:
        st.info("No hay inventario disponible en esta sede.")

# ------------------------------------------------------------------------------
# MÓDULO 3: PUNTO DE VENTA (CON LIMPIEZA FORZADA DE ESTADOS)
# ------------------------------------------------------------------------------
with tab3:
    c_form, c_cart = st.columns([1, 1.5])
    
    with c_form:
        st.subheader("REGISTRO DE VENTA")
        sede_vta = st.selectbox("Sede de Despacho:", ["Cali", "Buenaventura"])
        
        # Widgets anclados al session_state
        cliente_vta = st.text_input("Cliente:", key="vta_cliente")
        placas_disponibles = cargar_vehiculos()
        placa_vta = st.selectbox("Placa del Vehículo (Despacho):", ["Seleccione un vehículo"] + placas_disponibles, key="vta_placa")
        
        inv_sede = cargar_existencias_nube(sede_vta)
        productos_disp = list(set([item['Producto'] for item in inv_sede if item['Stock'] > 0]))
        
        prod_vta = st.selectbox("Producto:", ["Seleccione un producto"] + productos_disp, key="vta_prod")
        
        lotes_disp = [item for item in inv_sede if item['Producto'] == prod_vta and item['Stock'] > 0]
        opciones_lotes = [item['ID_Lote'] for item in lotes_disp]
        lote_vta = st.selectbox("Lote disponible:", ["Seleccione un lote"] + opciones_lotes, key="vta_lote")
        
        lote_obj = next((item for item in lotes_disp if item['ID_Lote'] == lote_vta), None)
        precio_sugerido = float(st.session_state.precios_venta.get(prod_vta, 0.0))
        
        if lote_obj:
            st.caption(f"🔵 Stock disponible: {lote_obj['Stock']:,.2f} KGS | Costo interno: $ {lote_obj['Costo']:,.0f}")
        
        cant_vta = st.number_input("Cantidad a vender (KGS):", min_value=0.0, step=1.0, key="vta_cant")
        precio_vta = st.number_input("Precio Venta (COP):", min_value=0.0, value=precio_sugerido, step=1000.0, key=f"vta_precio_{prod_vta}")
        
        if lote_obj:
            subt = cant_vta * precio_vta
            util = (precio_vta - lote_obj['Costo']) * cant_vta
            st.success(f"Subtotal: $ {subt:,.0f} | Utilidad: $ {util:,.0f}")
        
        if st.button("➕ AÑADIR A LA FACTURA", type="secondary", use_container_width=True):
            if prod_vta != "Seleccione un producto" and lote_vta != "Seleccione un lote" and placa_vta != "Seleccione un vehículo" and cant_vta > 0:
                if cant_vta <= lote_obj['Stock']:
                    st.session_state.carrito_ventas.append({
                        "producto": prod_vta, "lote": lote_vta, "cantidad": cant_vta,
                        "precio": precio_vta, "total": subt, "utilidad": util, "sede": sede_vta,
                        "placa": placa_vta 
                    })
                    # Magia: Forzamos el reset de los campos de producto sin borrar el cliente ni la placa
                    st.session_state.vta_prod = "Seleccione un producto"
                    st.session_state.vta_lote = "Seleccione un lote"
                    st.session_state.vta_cant = 0.0
                    st.rerun()
                else:
                    st.error("Inventario insuficiente en el lote seleccionado.")
            else:
                st.warning("Verifique: Cliente, Producto, Lote, Vehículo y Cantidad.")

    with c_cart:
        st.subheader("DETALLE DE LA FACTURA")
        if st.session_state.carrito_ventas:
            st.markdown("---")
            for i, item in enumerate(st.session_state.carrito_ventas):
                col_item1, col_item2, col_item3, col_item4 = st.columns([3, 1, 2, 1])
                col_item1.write(f"📦 **{item['producto']}**<br><span style='font-size:12px; color:gray;'>{item['lote']} | {item['placa']}</span>", unsafe_allow_html=True)
                col_item2.write(f"**{item['cantidad']} KGS**")
                col_item3.write(f"**$ {item['total']:,.0f}**")
                if col_item4.button("❌", key=f"del_{i}", help="Eliminar este ítem"):
                    st.session_state.carrito_ventas.pop(i)
                    st.rerun()
            st.markdown("---")

            tot_fact = sum(item['total'] for item in st.session_state.carrito_ventas)
            tot_util = sum(item['utilidad'] for item in st.session_state.carrito_ventas)
            
            st.markdown(f"### TOTAL FACTURA: $ {tot_fact:,.0f}")
            st.markdown(f"#### UTILIDAD: <span style='color:#10b981'>$ {tot_util:,.0f}</span>", unsafe_allow_html=True)
            
            if st.button("✅ FINALIZAR Y DESCONTAR INVENTARIO", type="primary", use_container_width=True):
                if not st.session_state.vta_cliente:
                    st.error("Debe escribir el nombre del cliente.")
                else:
                    payload = {"tipo_operacion": "RegistrarVenta", "cliente": st.session_state.vta_cliente, "items": st.session_state.carrito_ventas}
                    with st.spinner("Procesando Venta..."):
                        res = requests.post(URL_API, json=payload)
                        if res.status_code == 200:
                            st.success("¡Venta procesada exitosamente!")
                            # Reset absoluto de TODO al terminar la factura
                            st.session_state.carrito_ventas = [] 
                            st.session_state.vta_cliente = ""
                            st.session_state.vta_placa = "Seleccione un vehículo"
                            st.session_state.vta_prod = "Seleccione un producto"
                            st.session_state.vta_lote = "Seleccione un lote"
                            st.session_state.vta_cant = 0.0
                            st.cache_data.clear()
                            st.rerun()
        else:
            st.info("El carrito está vacío.")

# ------------------------------------------------------------------------------
# MÓDULO 4: ANÁLISIS DE UTILIDADES
# ------------------------------------------------------------------------------
with tab4:
    st.subheader("FILTROS DE AUDITORÍA")
    cf1, cf2, cf3 = st.columns(3)
    sede_ut = cf1.selectbox("Filtro Sede:", ["Todas las Sedes", "Cali", "Buenaventura"])
    prod_ut = cf2.selectbox("Filtro Producto:", ["Todos los Productos"] + st.session_state.nombres_productos)
    periodo_ut = cf3.selectbox("Filtro Periodo:", ["Todo el Historial", "Mes Actual", "Primera Quincena", "Segunda Quincena"])
    
    historico = cargar_historico_ventas()
    if historico:
        df_ut = pd.DataFrame(historico)
        df_ut = df_ut.rename(columns={1:'Fecha', 2:'Sede', 4:'Producto', 5:'Lote', 6:'Cantidad', 8:'Total', 9:'Utilidad'})
        df_ut['Total'] = pd.to_numeric(df_ut['Total'], errors='coerce').fillna(0)
        df_ut['Utilidad'] = pd.to_numeric(df_ut['Utilidad'], errors='coerce').fillna(0)
        df_ut['Cantidad'] = pd.to_numeric(df_ut['Cantidad'], errors='coerce').fillna(0)
        
        if sede_ut != "Todas las Sedes": df_ut = df_ut[df_ut['Sede'] == sede_ut]
        if prod_ut != "Todos los Productos": df_ut = df_ut[df_ut['Producto'] == prod_ut]
        
        u1, u2, u3 = st.columns(3)
        u1.metric("INGRESOS BRUTOS", f"$ {df_ut['Total'].sum():,.0f} COP")
        u2.metric("UTILIDAD NETA REAL", f"$ {df_ut['Utilidad'].sum():,.0f} COP")
        u3.metric("VOLUMEN VENDIDO", f"{df_ut['Cantidad'].sum():,.1f} KGS")
        
        st.dataframe(df_ut[['Fecha', 'Producto', 'Lote', 'Cantidad', 'Total', 'Utilidad', 'Sede']], use_container_width=True)
    else:
        st.info("Sincronizando histórico de ventas...")
