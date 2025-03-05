import streamlit as st
from logic import dataDB, queryColumn, ejecutarComandos, ipList
import pandas as pd

st.set_page_config(page_title="Gestión de Equipos", layout="wide")
st.markdown(
    """
    <style>
    .main .block-container {
        padding-left: 2rem;
        padding-right: 2rem;
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
    for key in ["tipo_equipo", "CIUDAD", "NODO", "hostname", "IP_DCN", "Vendor", "OS_TYPE", "Modelo"]:
        if key not in st.session_state:
            st.session_state[key] = "Todos" if key != "tipo_equipo" else "Switches"

    st.title("Gestión de Equipos")
    st.markdown("**Seleccione a través de los siguientes filtros.**")
    st.divider()
    tipo_equipo = st.radio("Tipo de Equipo", options=["Switches", "Routers"], key="tipo_equipo")
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

    col_filters, col_results = st.columns(2, gap="large")
    with col_filters:
        st.subheader("Filtros de Búsqueda")
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
    cmd_col, btn_col = st.columns([3, 1], gap="large")
    with cmd_col:
        comandos_str = st.text_area("Comandos (uno por línea):", height=150)
    with btn_col:
        st.write("")
        ejecutar = st.button("Ejecutar comandos")
    
    if ejecutar:
        if comandos_str:
            comandos = [line.strip() for line in comandos_str.splitlines() if line.strip()]
            vendor_ssh = vendor.lower() if vendor != "Todos" else "cisco"
            resultados = ejecutarComandos(ipList, comandos, vendor_default=vendor_ssh)
            st.markdown("### Resultados de la Ejecución:")
            for ip_addr, cmds in resultados.items():
                st.markdown(f"**{ip_addr}:**")
                if isinstance(cmds, dict):
                    for cmd, salida in cmds.items():
                        st.markdown(f"**Comando:** {cmd}")
                        st.text(salida)
                else:
                    st.text(cmds)
        else:
            st.warning("Ingrese al menos un comando.")
            
            
if __name__ == '__main__':
    render()
