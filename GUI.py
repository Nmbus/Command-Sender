import streamlit as st  # Versión recomendada: 1.12.0
    import pandas as pd # Versión recomendada: 1.3.3
    from logic import dataDB, queryColumn, ejecutarComandos, ipList
    # Configuración de la página con título y layout ancho.
    st.set_page_config(page_title="Gestión de Equipos", layout="wide")

    # =============================================================================
    # Bloque CSS Personalizado
    # =============================================================================
    #
    # El siguiente bloque de CSS define el estilo visual de la aplicación.
    # Se explican a continuación las secciones principales:
    #
    # 1. Contenedor Principal:
    #    - Selector: [data-testid="stAppViewContainer"]
    #    - Establece un fondo con un degradado lineal (de #FF5C00 a #F47C2E).
    #    - Elimina márgenes y padding para que el fondo cubra toda la ventana.
    #
    # 2. Encabezado y Barra de Herramientas:
    #    - Selectores: [data-testid="stHeader"], [data-testid="stToolbar"]
    #    - Se establece un fondo transparente para no interferir con el diseño principal.
    #
    # 3. Contenedores de Bloques:
    #    - Selector: .block-container
    #    - Aplica fondo blanco, texto en gris oscuro (#333333), padding generoso,
    #      bordes redondeados, márgenes verticales y una sombra suave para dar profundidad.
    #
    # 4. Encabezados (h1 a h6):
    #    - Se asigna un color naranja (#FF5C00) y un peso de fuente fuerte (700) para destacar títulos.
    #
    # 5. Elementos de Entrada (input, textarea, select y selectbox internos):
    #    - Se definen fondo blanco, texto gris oscuro y un borde naranja.
    #
    # 6. Botones:
    #    - Selector: .stButton>button
    #    - Se aplica un fondo naranja, texto blanco, sin borde y bordes redondeados.
    #    - En el estado hover, el fondo cambia a un tono ligeramente más claro (#F47C2E).
    #
    # 7. Estilos para DataFrames:
    #    - Los encabezados de la tabla usan un degradado similar al contenedor principal.
    #    - Las filas alternan colores (blanco y un gris muy claro) para mejorar la legibilidad.
    #    - Todas las celdas tienen un borde de 1px en color naranja.
    #
    
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

    """
    Retorna un valor de filtro modificado para las consultas SQL.

    Descripción:
    -------------
    Esta función recibe un valor proveniente de un selector y lo transforma en un patrón SQL.
    Si el valor es "Todos", se devuelve el comodín "%" para representar que no se aplica filtro. 
    En caso contrario, se retorna el valor tal cual.

    Parámetros de entrada:
    ------------------------
    val : str
        Valor obtenido del estado de sesión o seleccionado por el usuario.
    Salida:
    --------
    str
        "%" si val es "Todos"; de lo contrario, retorna val.

    Ejemplo:
    --------
    >>> get_filter("Todos")
    '%'
    >>> get_filter("Bogota")
    'Bogota'
    """
    def get_filter(val):
        return "%" if val == "Todos" else val


    """
    Construye dinámicamente una consulta SQL para extraer opciones de filtro basadas en una columna específica.
    Descripción:
    -------------
    La función recibe el nombre de la columna para la cual se desea obtener opciones (por ejemplo, CIUDAD, NODO, etc.),
    el nombre de la tabla (que puede ser *ipcol.switches* o *ipcol.routers*) y un diccionario con los filtros actuales.
    Se excluye la columna de la cual se quieren obtener las opciones y, en el caso de la tabla de routers, se ignora la columna 'Vendor' ya que no aplica. Se generan condiciones SQL del tipo "columna LIKE %s" para cada filtro activo y se retorna la consulta y los parámetros en forma de tupla.

    Parámetros de entrada:
    ------------------------
    col_name : str
        Nombre de la columna para la cual se desea obtener las opciones (por ejemplo, "CIUDAD").
    table_name : str
        Nombre de la tabla sobre la que se hará la consulta (ejemplo: "ipcol.switches" o "ipcol.routers").
    filters : dict
        Diccionario que contiene los filtros actuales aplicados, con claves que son nombres de columnas y valores que son los patrones a buscar.

    Salida:
    --------
    tuple
        (query, params): 
          - query: Consulta SQL (str) para obtener opciones distintas de la columna.
          - params: Tupla de parámetros a aplicar en la consulta.
        Si la columna es "Vendor" en la tabla de routers, retorna (None, None).

    Ejemplo:
    --------
    >>> filtros = {"CIUDAD": "%", "NODO": "NODO1", "hostname": "%", "IP_DCN": "%", "Vendor": "%", "OS_TYPE": "%", "Modelo": "%"}
    >>> build_filter_query("CIUDAD", "ipcol.switches", filtros)
    ('SELECT DISTINCT CIUDAD FROM ipcol.switches WHERE NODO LIKE %s AND hostname LIKE %s AND IP_DCN LIKE %s AND Vendor LIKE %s AND OS_TYPE LIKE %s AND Modelo LIKE %s',
     ('NODO1', '%', '%', '%', '%', '%'))
    """
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


     """
    Ejecuta la consulta para obtener opciones de filtro y ajusta la lista de opciones
    para asegurar una selección consistente en la interfaz.
    Descripción:
    -------------
    Esta función toma una consulta SQL (query) y sus parámetros (params) para extraer valores únicos de una columna específica (por ejemplo, "CIUDAD" o "NODO"). Utiliza la función queryColumn para ejecutar dicha consulta y obtener la lista de resultados.

    Realiza dos acciones
      1. Se asegura de que la opción "Todos" esté presente al inicio de la lista, ya que esta opción permite seleccionar la totalidad de los datos (sin aplicar filtro).
      2. Verifica si el valor actualmente seleccionado (current_val) se encuentra en la lista de opciones. Si el valor seleccionado no está presente (y no es "Todos"), lo añade al final. Al aplicar nuevos filtros, la opción previamente seleccionada puede haber 
         quedado fuera del nuevo conjunto de resultados, pero se desea mantenerla visible y seleccionada.

    Parámetros:
    -----------
    query : str or None
        Consulta SQL para extraer los valores únicos de una columna. Si es None, se utiliza un valor por defecto.
    params : tuple
        Parámetros que se aplicarán a la consulta SQL para filtrar los resultados.
    current_val : str
        Valor actualmente seleccionado en el filtro (por ejemplo, "Bogota" o "Todos").

    Retorna:
    --------
    list
        Lista de opciones para el filtro que incluye "Todos" al inicio y garantiza que el valor actualmente seleccionado se encuentre en la lista, incluso si no aparece en los resultados de la consulta.

    Ejemplo:
    --------
    Supongamos que:
      - Tenemos la siguiente consulta:
            query = "SELECT DISTINCT CIUDAD FROM ipcol.switches"
      - Los parámetros son:
            params = ()
      - Y el valor actualmente seleccionado es:
            current_val = "Bogota"
      - Además, la función queryColumn(query, params) retorna la lista:
            ["Medellin", "Cali"]

    Entonces, la función realizará lo siguiente:
      a. Llamará a queryColumn y obtendrá: ["Medellin", "Cali"].
      b. Insertará "Todos" al inicio, resultando en: ["Todos", "Medellin", "Cali"].
      c. Como "Bogota" no está en la lista y current_val no es "Todos", se añadirá al final.

    Resultado final:
        ["Todos", "Medellin", "Cali", "Bogota"]
    """
    def safe_options(query, params, current_val):
        options = queryColumn(query, params) if query else ["Todos"]
        if "Todos" not in options:
            options.insert(0, "Todos")
        if current_val != "Todos" and current_val not in options:
            options.append(current_val)
        return options

    """
    Renderiza un selectbox de Streamlit con la opción actualmente seleccionada según el estado de sesión (st.session_state).
    Descripción:
    -------------
    Esta función se utiliza para mostrar un selectbox en la interfaz de Streamlit.
    Para ello, se recupera el valor actualmente almacenado en st.session_state con la clave especificada (key).
    Se busca este valor dentro de la lista de opciones (options) para determinar el índice correspondiente.
    Si se encuentra, se utiliza ese índice como valor predeterminado en el selectbox; de lo contrario, se establece el índice 0 (la opción "Todos").

    Parámetros:
    -----------
    label : str
        Texto que se muestra junto al selectbox, sirviendo como etiqueta descriptiva.
    options : list
        Lista de opciones (strings) que se desplegarán en el selectbox.
    key : str
        Clave utilizada en st.session_state para almacenar y recuperar el valor seleccionado por el usuario.

    Retorna:
    --------
    str
        El valor seleccionado actualmente a través del selectbox.

    Ejemplo:
    --------
    Supongamos que:
      - st.session_state["CIUDAD"] contiene el valor "Medellin".
      - La lista de opciones es: ["Todos", "Bogota", "Medellin", "Cali"].
      - La clave proporcionada es "CIUDAD".

    Entonces, la función realizará lo siguiente:
      1. Recupera el valor "Medellin" desde st.session_state["CIUDAD"].
      2. Busca "Medellin" en la lista de opciones y encuentra que está en la posición 2 
      3. Renderiza el selectbox con la etiqueta dada, utilizando la opción "Medellin" como la opción seleccionada por defecto.

    Resultado:
      Se mostrará un selectbox etiquetado con las opciones ["Todos", "Bogota", "Medellin", "Cali"], y "Medellin" estará preseleccionada.

    """
    def select_with_index(label, options, key):
        current_val = st.session_state[key]
        try:
            idx = options.index(current_val)
        except ValueError:
            idx = 0
        return st.selectbox(label, options=options, index=idx, key=key)
    
    def render():
        """
        Función principal que configura y renderiza la interfaz de la aplicación Streamlit.
        
        Esta función organiza la interfaz en varias secciones:
          - Inicialización de variables en el session state.
          - Configuración del título y descripción.
          - División de la pantalla en columnas para filtros y resultados.
          - Configuración de selectboxes de filtros.
          - Consulta a la base de datos y visualización de resultados.
          - Sección para ingresar y ejecutar comandos vía SSH en los dispositivos filtrados.
        """

        # =============================================================================
        # 1. Inicialización del Session State
        # =============================================================================
        # Se inicializan claves en el session state si aún no existen.
        # "tipo_equipo" se inicializa en "Switches" y los demás en "Todos".
        for key in ["tipo_equipo", "CIUDAD", "NODO", "hostname", "IP_DCN", "Vendor", "OS_TYPE", "Modelo"]:
            if key not in st.session_state:
                st.session_state[key] = "Todos" if key != "tipo_equipo" else "Switches"

        # =============================================================================
        # 2. Configuración del Encabezado y Descripción
        # =============================================================================
        st.title("Gestión de Equipos")
        st.markdown("**Seleccione a través de los siguientes filtros.**")
        st.divider()
        
        # =============================================================================
        # 3. División de la Interfaz en Columnas: Filtros y Resultados
        # =============================================================================
        col_filters, col_results = st.columns(2, gap="large")
        
        # =============================================================================
        # 4. Sección de Filtros (col_filters)
        # =============================================================================
        with col_filters:
            st.subheader("Filtros de Búsqueda")
            
            # Selección del tipo de equipo usando un selectbox.
            # Se utiliza la función select_with_index, que toma el valor actual desde st.session_state.
            tipo_equipo = select_with_index("Tipo de Equipo", ["Switches", "Routers"], "tipo_equipo")
            
            # Se define la tabla a consultar según el tipo de equipo seleccionado.
            table_name = "ipcol.switches" if tipo_equipo == "Switches" else "ipcol.routers"
    
            # Preparar los filtros para la consulta, convirtiendo "Todos" en "%" (comodín SQL)
            filters = {
                "CIUDAD": get_filter(st.session_state["CIUDAD"]),
                "NODO": get_filter(st.session_state["NODO"]),
                "hostname": get_filter(st.session_state["hostname"]),
                "IP_DCN": get_filter(st.session_state["IP_DCN"]),
                "Vendor": get_filter(st.session_state["Vendor"]),
                "OS_TYPE": get_filter(st.session_state["OS_TYPE"]),
                "Modelo": get_filter(st.session_state["Modelo"])
            }
            
            # Organizar los filtros en tres columnas para una mejor presentación visual
            f1, f2, f3 = st.columns(3, gap="small")
            
            # ---------------------------
            # Columna f1: CIUDAD, NODO, hostname
            # ---------------------------
            with f1:
                # CIUDAD: Se construye la consulta y se obtienen opciones seguras para el filtro
                query_ciudad, params_ciudad = build_filter_query("CIUDAD", table_name, filters)
                ciudad_options = safe_options(query_ciudad, params_ciudad, st.session_state["CIUDAD"])
                ciudad = select_with_index("Ciudad", ciudad_options, "CIUDAD")
                
                # NODO: 
                query_nodo, params_nodo = build_filter_query("NODO", table_name, filters)
                nodo_options = safe_options(query_nodo, params_nodo, st.session_state["NODO"])
                nodo = select_with_index("Nodo", nodo_options, "NODO")
                
                # hostname: 
                query_hostname, params_hostname = build_filter_query("hostname", table_name, filters)
                hostname_options = safe_options(query_hostname, params_hostname, st.session_state["hostname"])
                hostname = select_with_index("Hostname", hostname_options, "hostname")
            
            # ---------------------------
            # Columna f2: IP_DCN y Vendor
            # ---------------------------
            with f2:
                # IP_DCN:
                query_ip, params_ip = build_filter_query("IP_DCN", table_name, filters)
                ip_options = safe_options(query_ip, params_ip, st.session_state["IP_DCN"])
                ip_val = select_with_index("IP", ip_options, "IP_DCN")
                
                # Vendor: Solo se muestra para "Switches", en caso contrario se fija en "No Aplica"
                if tipo_equipo == "Switches":
                    query_vendor, params_vendor = build_filter_query("Vendor", table_name, filters)
                    vendor_options = safe_options(query_vendor, params_vendor, st.session_state["Vendor"])
                else:
                    vendor_options = ["No Aplica"]
                vendor = select_with_index("Vendor", vendor_options, "Vendor")
            
            # ---------------------------
            # Columna f3: OS_TYPE y Modelo
            # ---------------------------
            with f3:
                # OS_TYPE:
                query_os, params_os = build_filter_query("OS_TYPE", table_name, filters)
                os_options = safe_options(query_os, params_os, st.session_state["OS_TYPE"])
                os_val = select_with_index("IOS", os_options, "OS_TYPE")
                
                # Modelo:
                query_modelo, params_modelo = build_filter_query("Modelo", table_name, filters)
                modelo_options = safe_options(query_modelo, params_modelo, st.session_state["Modelo"])
                modelo = select_with_index("Modelo", modelo_options, "Modelo")
        
        # =============================================================================
        # 5. Sección de Resultados (col_results)
        # =============================================================================
        with col_results:
            st.subheader("Resultados")
            # Se consulta la base de datos usando la función dataDB, aplicando los filtros obtenidos.
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
            # Si no se obtienen resultados o se produce un error, se muestra una advertencia.
            if resultado is None or isinstance(resultado, str):
                st.warning("No se encontraron resultados o se produjo un error.")
            else:
                rows, columns = resultado
                # Se convierte el resultado en un DataFrame y se filtran las columnas relevantes.
                df = pd.DataFrame(rows, columns=columns)
                df = df[["CIUDAD", "NODO", "hostname", "IP_DCN", "Vendor", "OS_TYPE", "Modelo"]]
                # Se muestra el DataFrame en la interfaz, adaptado al ancho del contenedor y sin índice.
                st.dataframe(df, use_container_width=True, hide_index=True)
        
        # =============================================================================
        # 6. Sección de Ejecución de Comandos
        # =============================================================================
        st.divider()
        st.header("Ejecución de Comandos")
        st.markdown("Ingrese los comandos que desea ejecutar en los equipos filtrados.")
        
        # Dividir en dos columnas: una para ingresar comandos y otra para mostrar los resultados.
        col_command, col_execution = st.columns(2, gap="large")
        resultados_comandos = None  # Variable que almacenará los resultados de la ejecución de comandos.
        
        # ---------------------------
        # Columna de Comandos: Ingreso de Comandos
        # ---------------------------
        with col_command:
            # Área de texto para que el usuario ingrese comandos (uno por línea)
            comandos_str = st.text_area("Comandos (uno por línea):", height=150)
            # Botón para ejecutar los comandos
            ejecutar = st.button("Ejecutar comandos")
            # Si se presiona el botón pero no se ingresan comandos, se muestra una advertencia.
            if ejecutar and not comandos_str:
                st.warning("Ingrese al menos un comando.")
        
        # ---------------------------
        # Procesamiento y Ejecución de Comandos
        # ---------------------------
        if ejecutar and comandos_str:
            # Se separan las líneas y se eliminan aquellas vacías para formar la lista de comandos.
            comandos = [line.strip() for line in comandos_str.splitlines() if line.strip()]
            # Determinar el valor de vendor para la conexión SSH:
            # Si se ha seleccionado un valor distinto de "Todos", se usa ese valor en minúsculas; de lo contrario, se usa "cisco".
            vendor_val = st.session_state["Vendor"]
            vendor_ssh = vendor_val.lower() if vendor_val != "Todos" else "cisco"
            # Ejecutar los comandos en las IPs filtradas usando la función ejecutarComandos.
            resultados_comandos = ejecutarComandos(ipList, comandos, vendor_default=vendor_ssh)
        
        # ---------------------------
        # Columna de Resultados: Mostrar Salida de Comandos
        # ---------------------------
        with col_execution:
            if resultados_comandos:
                st.markdown("### Resultados de la Ejecución:")
                # Iterar sobre cada IP y mostrar sus resultados.
                for ip_addr, cmds in resultados_comandos.items():
                    st.markdown(f"**{ip_addr}:**")
                    if isinstance(cmds, dict):
                        # Si cmds es un diccionario, mostrar cada comando y su salida.
                        for cmd, salida in cmds.items():
                            st.markdown(f"**Comando:** {cmd}")
                            st.text(salida)
                    else:
                        # En caso de error o formato inesperado, mostrar el mensaje directamente.
                        st.text(cmds)
    
    
    if __name__ == '__main__':
        render()
