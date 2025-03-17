 #Versión de Python 3.13
        # paramiko==2.11.0       -> Para la conexión SSH
        # mariadb==1.1.8         -> Para conectarse a la base de datos MariaDB
        # pandas==1.3.3          -> Para el manejo de DataFrames
        import paramiko
        import mariadb
        import pandas as pd
        import time
        # Lista global para almacenar direcciones IP extraídas de la base de datos.
        ipList = []


        """
        Ejecuta comandos vía SSH en una lista de equipos especificados por IP.
        Descripción:
        -------------
        Esta función se conecta a cada dirección IP de la lista 'ipList' usando el protocolo SSH. Para cada dispositivo, se establece una conexión y se invoca un shell interactivo para enviar comandos. Se espera un tiempo de 5 segundos para
        que los dispositivos procesen los comandos y se captura la salida (si está disponible). Toda la salida se almacena en
        un diccionario 'resultados', donde la clave es la IP y el valor es otro diccionario con los comandos ejecutados y
        sus respectivas salidas.
    
        Parámetros de entrada:
        ------------------------
        -> ipList: list
            Lista de direcciones IP (strings) de los dispositivos a los que se conectará.
        -> comandos: list
            Lista de comandos (strings) que se ejecutarán en cada dispositivo.
        -> endor_default: str (default "cisco")
            Valor para indicar el vendor por defecto;
            pero se deja como parámetro para posibles extensiones.
        port: str default 22
            Puerto de conexión SSH.
        username: str (default "mguzman")
            Nombre de usuario para autenticarse en el dispositivo vía SSH.
        password: str (default "4s7rRMaq")
            Contraseña para la autenticación SSH.
    
        Variables modificadas:
        ------------------------
        resultados: dict
            Diccionario que se va llenando con las salidas de cada comando ejecutado por cada dispositivo.
        Salidas:
        --------
        dict
            Un diccionario con la estructura:
            {
                "ip_del_dispositivo": {
                    "comando1": "salida1",
                    "comando2": "salida2",
                    ...
                },
                "ip_del_dispositivo_2": {
                    "comando1": "salida1",
                    "comando2": "salida2",
                    ...
                },
                ...
            }
            Si ocurre un error en la conexión, la salida para esa IP será un mensaje de error.
        
        Ejemplo de uso:
        ----------------
        >>> ips = ["172.18.49.9", "172.18.49.10"]
        >>> cmds = ["show version", "show ip interface brief"]
        >>> resultados = ejecutarComandos(ips, cmds)
        >>> print(resultados)
        {
            "172.18.49.9": {
                "show version": "Cisco IOS Software, ...",
                "show ip interface brief": "Interface, IP-Address, ..."
            },
            "172.18.49.10": {
                "show version": "Cisco IOS Software, ...",
                "show ip interface brief": "Interface, IP-Address, ..."
            }
        }
        """

        def ejecutarComandos(ipList, comandos, vendor_default="cisco", port="22", username="mguzman", password="4s7rRMaq"):
            resultados = {}
            for ip in ipList:
                resultados[ip] = {}
                ssh_client = paramiko.SSHClient()
                try:
                    ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                    ssh_client.connect(ip, port=port, username=username, password=password)
                    if ssh_client.get_transport().is_active():
                        shell = ssh_client.invoke_shell()
                        #if vendor_default.lower() == "cisco":
                        shell.send("\n")
                        time.sleep(1)
                        for comando in comandos:
                            shell.send(f"{comando}\n")
                            time.sleep(5)
                            if shell.recv_ready():
                                salida = shell.recv(20000).decode("utf-8")
                            else:
                                salida = "No se obtuvo salida."
                            resultados[ip][comando] = salida
                    else:
                        resultados[ip] = "Conexión inactiva."
                except Exception as e:
                    resultados[ip] = f"Error: {e}"
                finally:
                    ssh_client.close()
            return resultados





        """
        Consulta la base de datos MariaDB para extraer información de dispositivos y actualiza la lista global de IPs.
    
        Descripción:
        -------------
        Esta función se conecta a la base de datos MariaDB utilizando parámetros predefinidos y ejecuta una consulta SQL para obtener datos de la tabla correspondiente, que puede ser la de "switches" o la de "routers" dependiendo del 
        parámetro 'tipo_equipo'. Se aplican filtros en las columnas mediante patrones (usualmente '%') para realizar búsquedas flexibles. Además, actualiza la variable global 'ipList' con las IPs únicas extraídas de la columna 'IP_DCN'.
    
        Parámetros de entrada:
        ------------------------
        ciudad: str (default '%')
            Patrón para filtrar la columna CIUDAD.
        nodo: str (default '%')
            Patrón para filtrar la columna NODO.
        hostname: str (default '%')
            Patrón para filtrar la columna hostname.
        ip: str (default '%')
            Patrón para filtrar la columna IP_DCN.
        vendor: str (default '%')
            Patrón para filtrar la columna Vendor (aplicable para switches).
        os: str (default '%')
            Patrón para filtrar la columna OS_TYPE.
        modelo: str (default '%')
            Patrón para filtrar la columna Modelo.
        tipo_equipo: str (default "Switches")
            Determina de qué tabla se extraerán los datos. Si es "Switches", se consulta la tabla ipcol.switches; 
            de lo contrario, se consulta la tabla ipcol.routers.
    
        Variables modificadas:
        ------------------------
        ipList (global): list
            Se actualiza con la lista de direcciones IP únicas obtenidas de la columna "IP_DCN" de la consulta.
    
        Salidas:
        --------
        tuple (rows, columns)
            - rows: Lista de tuplas con los registros obtenidos de la consulta.
            - columns: Lista de nombres de columnas correspondientes a los registros.
        None
            Si la consulta no devuelve registros.
        str
            Mensaje de error si ocurre un fallo al conectar con la base de datos.
    
        Ejemplo de uso:
        ----------------
        >>> resultado = dataDB(ciudad='Bogota', nodo='BIOMX')
        >>> if resultado:
        ...     rows, columns = resultado
        ...     print("Columnas:", columns)
        ...     print("Primer registro:", rows[0])
        >>> else:
        ...     print("No se encontraron registros.")
        """
        def dataDB(ciudad='%', nodo='%', hostname='%', ip='%', vendor='%', os='%', modelo='%', tipo_equipo="Switches"):
            global ipList
            try:
                conn = mariadb.connect(
                    user="root",
                    password="Trul-f87",
                    host="172.18.93.210",
                    port=3306,
                    database="ipcol"
                )
                cur = conn.cursor()
                if tipo_equipo == "Switches":
                    query = (
                        "SELECT * FROM ipcol.switches WHERE CIUDAD LIKE %s AND NODO LIKE %s AND hostname LIKE %s "
                        "AND IP_DCN LIKE %s AND Vendor LIKE %s AND OS_TYPE LIKE %s AND Modelo LIKE %s"
                    )
                    params = (ciudad, nodo, hostname, ip, vendor, os, modelo)
                else:
                    query = (
                        "SELECT CIUDAD, NODO, hostname, IP_DCN, NULL AS Vendor, OS_TYPE, Modelo FROM ipcol.routers "
                        "WHERE CIUDAD LIKE %s AND NODO LIKE %s AND hostname LIKE %s "
                        "AND IP_DCN LIKE %s AND OS_TYPE LIKE %s AND Modelo LIKE %s"
                    )
                    params = (ciudad, nodo, hostname, ip, os, modelo)
                cur.execute(query, params)
                rows = cur.fetchall()
                columns = [desc[0] for desc in cur.description]
                cur.close()
                conn.close()
                if not rows:
                    return None
                else:
                    index_ip = columns.index("IP_DCN")
                    ipList = list({row[index_ip] for row in rows})
                    return rows, columns
            except mariadb.Error as e:
                return f"Error connecting to DB: {e}



        """
        Ejecuta una consulta SQL y retorna una lista de opciones para uso en filtros, anteponiendo el valor "Todos".
    
        Descripción:
        -------------
        Esta función se conecta a la base de datos MariaDB y ejecuta una consulta SQL que se espera retorne un conjunto de resultados de una única columna (por ejemplo, todas las ciudades, nodos o modelos disponibles en la tabla *switches* o *routers*).
        La función procesa el resultado y retorna una lista en la que el primer elemento es la opción "Todos" y los siguientes elementos son los resultados obtenidos de la consulta.
        
        El uso de esta función es flexible, de modo que la consulta y sus parámetros pueden construirse dinámicamente según los filtros aplicados en la interfaz. Por ejemplo, si ya se ha filtrado por "nodo" o "ciudad" en otra parte, la consulta que 
        se pase a *queryColumn* devolverá únicamente los valores correspondientes a ese subconjunto. Así, la función se adapta a los filtros activos, permitiendo que los usuarios seleccionen valores específicos en función de otros criterios.
    
        Parámetros de entrada:
        ------------------------
        query: str
            Consulta SQL que se ejecutará, la cual debe retornar un conjunto de resultados de una sola columna.
        params: tuple (default vacío)
            Parámetros a utilizar en la consulta SQL, que permiten filtrar los resultados según otros criterios.
    
        Salidas:
        --------
        list
            Una lista de cadenas que comienza con "Todos" seguido de los valores obtenidos de la consulta.
            Ejemplo: ["Todos", "Bogota", "Medellin", "Cali"]
            En caso de error, se retorna una lista con un mensaje de error.
    
        Ejemplo de uso
        -------------------------
        # Supongamos que queremos obtener la lista de ciudades disponibles en la tabla de switches,
        # pero solo para aquellos registros que cumplen con un filtro de 'ios' específico.
        >>> consulta = "SELECT DISTINCT CIUDAD FROM ipcol.switches WHERE IOS LIKE %s"
        >>> parametros = ('XR')  # Podrían ser dinámicos según la selección del usuario.
        >>> opciones_ciudad = queryColumn(consulta, parametros)
        >>> print(opciones_ciudad)
        ["Todos", "Bogota", "Medellin"]
        
        # Si se desea obtener todos los nodos sin aplicar filtro previo:
        >>> consulta_nodos = "SELECT DISTINCT NODO FROM ipcol.switches"
        >>> opciones_nodo = queryColumn(consulta_nodos)
        >>> print(opciones_nodo)
        ["Todos", "NODO1", "NODO2", "NODO3"]
        """
        
        def queryColumn(query, params=()):
            try:
                conn = mariadb.connect(
                    user="root",
                    password="Trul-f87",
                    host="172.18.93.210",
                    port=3306,
                    database="ipcol"
                )
                cur = conn.cursor()
                cur.execute(query, params)
                rows = cur.fetchall()
                cur.close()
                conn.close()
                if not rows:
                    return ["Todos"]
                else:
                    return ["Todos"] + [str(row[0]) for row in rows]
            except mariadb.Error as e:
                return [f"Error connecting to DB: {e}"]
