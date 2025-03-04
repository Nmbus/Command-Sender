import paramiko
import mariadb
import pandas as pd
import time


ipList = []

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
        return f"Error connecting to DB: {e}"

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
