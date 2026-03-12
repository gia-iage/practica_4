from pyspark.sql import SparkSession
import sys

if len(sys.argv) < 2:
    print("Error: Debes indicar la ruta del fichero en HDFS.")
    print("Uso: spark-submit spark_test.py /ruta/al/fichero.txt")
    sys.exit(1)

path_hdfs = sys.argv[1]

# Inicializamos la sesión (Spark Connect)
spark = SparkSession.builder.appName("SparkHDFS").getOrCreate()

try:
    print("---------------------------------------------------")
    print(f"--- Procesando fichero: {path_hdfs} ---")
    print("---------------------------------------------------")
    # Leemos el fichero
    df = spark.read.text(path_hdfs)
    # Contamos las líneas
    lineas = df.count()
    
    print(f"El fichero tiene {lineas} líneas")
    print("---------------------------------------------------\n")

except Exception as e:
    print(f"Error al leer el fichero en HDFS: {e}")

finally:
    # Cerramos la sesión
    spark.stop()
