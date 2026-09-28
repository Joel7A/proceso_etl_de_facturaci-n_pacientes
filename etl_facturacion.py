import csv
import mysql.connector
from mysql.connector import Error


def ejecutar_etl_facturacion():

    conexion = None
    cursor = None

    try:
        # conexion a la base de datos MySql
        conexion = mysql.connector.connect(
            host="localhost", database="saludMedica", user="root", password=""
        )

        if conexion.is_connected():
            cursor = conexion.cursor()

            # crear la tabla si no existe
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS facturacion_citas (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    paciente VARCHAR(100),
                    especialidad VARCHAR(100),
                    costo_base DECIMAL(10,2),
                    descuento DECIMAL(10,2) DEFAULT 0.00,
                    igv DECIMAL(10,2) DEFAULT 0.00,
                    total DECIMAL(10,2) 
                )
            """)

            # limpiar la tabla antes de insertar nuevos datos
            cursor.execute("TRUNCATE TABLE facturacion_citas")

            registros_exitosos = 0
            registros_fallidos = 0

            # 1 ----- EXTRACCION

            with open("citas_dia.csv", mode="r", encoding="utf-8") as archivoCSV:
                lector_csv = csv.DictReader(archivoCSV)

                # 2 ------ TRANSFORMACION
                for fila in lector_csv:
                    try:
                        # conevrsion de tipos, calculos, validaciones,etc..
                        paciente = fila["paciente"]
                        especialidad = fila["especialidad"]
                        costo_base = float(fila["costo_base"])

                        # validaciones
                        if not paciente or not especialidad:
                            registros_fallidos += 1
                            continue  # saltar a la siguiente fila si hay error de validacion

                        if costo_base <= 0:
                            registros_fallidos += 1
                            continue

                        # calcular valores
                        if especialidad == "Pediatria":
                            descuento = costo_base * 0.10
                        else:
                            descuento = 0

                        costo_con_descuento = costo_base - descuento

                        igv = costo_con_descuento * 0.18

                        total = costo_con_descuento + igv

                        # 3 -------- cargar
                        #

                        query = """
                            INSERT INTO facturacion_citas(
                                paciente,
                                especialidad,
                                costo_base,
                                descuento,
                                igv,
                                total
                            )
                            VALUES(%s, %s, %s, %s, %s, %s)
                        """
                        cursor.execute(
                            query,
                            (paciente, especialidad, costo_base, descuento, igv, total),
                        )

                        registros_exitosos += 1

                    except ValueError:
                        registros_fallidos += 1
                        continue
                        # saltar a la siguiente fila si hay error

            # confirmar las inserciones
            conexion.commit()
            print(f"Total de registros procesados con exito: {registros_exitosos}")
            print(f"Total de registros descartado por errores: {registros_fallidos}")

    # 4 ----- manejo de errores

    except Error as e:
        print(f"error de conexion{e}")
    finally:
        if cursor is not None:
            cursor.close()
        if conexion is not None and conexion.is_connected():
            conexion.close()
        print("conexion a mysql cerrada.")


ejecutar_etl_facturacion()
