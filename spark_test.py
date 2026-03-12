from pyspark.sql import SparkSession
import sys

# 1. Verificamos si se ha pasado el argumento del fichero
if len(sys.argv) < 2:
    print("Error: Debes indicar la ruta del fichero en HDFS.")
    print("Uso: spark-submit spark_test.py /ruta/al/fichero.txt")
    sys.exit(1)

# Capturamos la ruta del primer argumento
path_hdfs = sys.argv[1]

# 2. Inicializamos la sesión (Spark Connect)
spark = SparkSession.builder.appName("SparkHDFS").getOrCreate()

try:
    print("---------------------------------------------------")
    print(f"--- Procesando fichero: {path_hdfs} ---")
    print("---------------------------------------------------")
    
    # 3. Leemos el fichero dinámicamente
    df = spark.read.text(path_hdfs)

    # 4. Contamos las líneas
    lineas = df.count()
    
    print(f"El fichero tiene {lineas} líneas")
    print("---------------------------------------------------\n")

except Exception as e:
    print(f"Error al leer el fichero en HDFS: {e}")

finally:
    # 5. Cerramos la sesión
    spark.stop()
