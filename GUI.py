import streamlit as st
import pandas as pd
from logic import dataDB, queryColumn, ejecutarComandos, ipList

st.set_page_config(page_title="Gestión de Equipos", layout="wide")

st.markdown(
    """
    <style>
    [data-testid="stAppViewContainer"] {
        background: linear-gradient(to right, #FF5C00, #F47C2E) !important;
        margin: 0;
        padding: 0;
    }


    [data-testid="stHeader"], [data-testid="stToolbar"] {
        background: none !important;
    }

    .block-container {
        background-color: #FFFFFF !important; /* Fondo blanco */
        color: #333333 !important;           /* Texto gris oscuro */
        padding: 2rem !important;
        border-radius: 8px !important;
        margin: 2rem auto !important;
        box-shadow: 0 0 10px rgba(0,0,0,0.1) !important; /* Sombra suave */
    }

    h1, h2, h3, h4, h5, h6 {
        color: #FF5C00 !important;
        font-weight: 700 !important;
    }

    input, textarea, select {
        background-color: #FFFFFF !important;
        color: #333333 !important;
        border: 1px solid #FF5C00 !important;
    }
    .stTextInput>div>div>input,
    .stTextArea>div>textarea,
    .stSelectbox>div>div>div>button {
        background-color: #FFFFFF !important;
        color: #333333 !important;
        border: 1px solid #FF5C00 !important;
    }

    .stButton>button {
        background-color: #FF5C00 !important;
        color: #FFFFFF !important;
        border: none !important;
        border-radius: 4px !important;
    }
    .stButton>button:hover {
        background-color: #F47C2E !important;
        color: #FFFFFF !important;
    }

    .dataframe thead th {
        background: linear-gradient(to right, #FF5C00, #F47C2E) !important;
        color: #FFFFFF !important;
    }
    .dataframe tbody tr:nth-child(even) {
        background-color: #f9f9f9 !important;
    }
    .dataframe tbody tr:nth-child(odd) {
        background-color: #ffffff !important;
    }
    .dataframe td, .dataframe th {
        border: 1px solid #FF5C00 !important;
    }
    </style>
    """,
    unsafe_allow_html=True
)

def get_filter(val):
    return "%" if val == "Todos" else val

def build_filter_query(col_name, table_name, filters):
    if table_name == "ipcol.routers" and col_name == "Vendor":
        return None, None
    conditions = []
    params = []
    for key, value in filters.items():
        if key == col_name:
            continue
        if table_name == "ipcol.routers" and key == "Vendor":
            continue
        conditions.append(f"{key} LIKE %s")
        params.append(value)
    if conditions:
        cond_str = " AND ".join(conditions)
        query = f"SELECT DISTINCT {col_name} FROM {table_name} WHERE {cond_str}"
    else:
        query = f"SELECT DISTINCT {col_name} FROM {table_name}"
    return query, tuple(params)

def safe_options(query, params, current_val):
    options = queryColumn(query, params) if query else ["Todos"]
    if "Todos" not in options:
        options.insert(0, "Todos")
    if current_val != "Todos" and current_val not in options:
        options.append(current_val)
    return options

def select_with_index(label, options, key):
    current_val = st.session_state[key]
    try:
        idx = options.index(current_val)
    except ValueError:
        idx = 0
    return st.selectbox(label, options=options, index=idx, key=key)

def render():
    # Inicialización de variables de sesión
    for key in ["tipo_equipo", "CIUDAD", "NODO", "hostname", "IP_DCN", "Vendor", "OS_TYPE", "Modelo"]:
        if key not in st.session_state:
            st.session_state[key] = "Todos" if key != "tipo_equipo" else "Switches"

    st.title("Gestión de Equipos")
    st.markdown("**Seleccione a través de los siguientes filtros.**")
    st.divider()
    
    col_filters, col_results = st.columns(2, gap="large")
    with col_filters:
        st.subheader("Filtros de Búsqueda")
        tipo_equipo = select_with_index("Tipo de Equipo", ["Switches", "Routers"], "tipo_equipo")
        table_name = "ipcol.switches" if tipo_equipo == "Switches" else "ipcol.routers"
        
        filters = {
            "CIUDAD": get_filter(st.session_state["CIUDAD"]),
            "NODO": get_filter(st.session_state["NODO"]),
            "hostname": get_filter(st.session_state["hostname"]),
            "IP_DCN": get_filter(st.session_state["IP_DCN"]),
            "Vendor": get_filter(st.session_state["Vendor"]),
            "OS_TYPE": get_filter(st.session_state["OS_TYPE"]),
            "Modelo": get_filter(st.session_state["Modelo"])
        }
        
        f1, f2, f3 = st.columns(3, gap="small")
        with f1:
            query_ciudad, params_ciudad = build_filter_query("CIUDAD", table_name, filters)
            ciudad_options = safe_options(query_ciudad, params_ciudad, st.session_state["CIUDAD"])
            ciudad = select_with_index("Ciudad", ciudad_options, "CIUDAD")
            
            query_nodo, params_nodo = build_filter_query("NODO", table_name, filters)
            nodo_options = safe_options(query_nodo, params_nodo, st.session_state["NODO"])
            nodo = select_with_index("Nodo", nodo_options, "NODO")
            
            query_hostname, params_hostname = build_filter_query("hostname", table_name, filters)
            hostname_options = safe_options(query_hostname, params_hostname, st.session_state["hostname"])
            hostname = select_with_index("Hostname", hostname_options, "hostname")
        with f2:
            query_ip, params_ip = build_filter_query("IP_DCN", table_name, filters)
            ip_options = safe_options(query_ip, params_ip, st.session_state["IP_DCN"])
            ip_val = select_with_index("IP", ip_options, "IP_DCN")
            
            if tipo_equipo == "Switches":
                query_vendor, params_vendor = build_filter_query("Vendor", table_name, filters)
                vendor_options = safe_options(query_vendor, params_vendor, st.session_state["Vendor"])
            else:
                vendor_options = ["No Aplica"]
            vendor = select_with_index("Vendor", vendor_options, "Vendor")
        with f3:
            query_os, params_os = build_filter_query("OS_TYPE", table_name, filters)
            os_options = safe_options(query_os, params_os, st.session_state["OS_TYPE"])
            os_val = select_with_index("IOS", os_options, "OS_TYPE")
            
            query_modelo, params_modelo = build_filter_query("Modelo", table_name, filters)
            modelo_options = safe_options(query_modelo, params_modelo, st.session_state["Modelo"])
            modelo = select_with_index("Modelo", modelo_options, "Modelo")

    with col_results:
        st.subheader("Resultados")
        resultado = dataDB(
            get_filter(st.session_state["CIUDAD"]),
            get_filter(st.session_state["NODO"]),
            get_filter(st.session_state["hostname"]),
            get_filter(st.session_state["IP_DCN"]),
            get_filter(st.session_state["Vendor"]),
            get_filter(st.session_state["OS_TYPE"]),
            get_filter(st.session_state["Modelo"]),
            tipo_equipo=tipo_equipo
        )
        if resultado is None or isinstance(resultado, str):
            st.warning("No se encontraron resultados o se produjo un error.")
        else:
            rows, columns = resultado
            df = pd.DataFrame(rows, columns=columns)
            df = df[["CIUDAD", "NODO", "hostname", "IP_DCN", "Vendor", "OS_TYPE", "Modelo"]]
            st.dataframe(df, use_container_width=True, hide_index=True)
    
    st.divider()
    st.header("Ejecución de Comandos")
    st.markdown("Ingrese los comandos que desea ejecutar en los equipos filtrados.")
    
    col_command, col_execution = st.columns(2, gap="large")
    resultados_comandos = None
    with col_command:
        comandos_str = st.text_area("Comandos (uno por línea):", height=150)
        ejecutar = st.button("Ejecutar comandos")
        if ejecutar and not comandos_str:
            st.warning("Ingrese al menos un comando.")
    
    if ejecutar and comandos_str:
        comandos = [line.strip() for line in comandos_str.splitlines() if line.strip()]
        # Ajustamos la referencia a "vendor" para evitar error si no existe:
        vendor_val = st.session_state["Vendor"]
        vendor_ssh = vendor_val.lower() if vendor_val != "Todos" else "cisco"
        resultados_comandos = ejecutarComandos(ipList, comandos, vendor_default=vendor_ssh)
    
    with col_execution:
        if resultados_comandos:
            st.markdown("### Resultados de la Ejecución:")
            for ip_addr, cmds in resultados_comandos.items():
                st.markdown(f"**{ip_addr}:**")
                if isinstance(cmds, dict):
                    for cmd, salida in cmds.items():
                        st.markdown(f"**Comando:** {cmd}")
                        st.text(salida)
                else:
                    st.text(cmds)


if __name__ == '__main__':
    render()
