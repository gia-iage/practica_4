from pyspark.sql import SparkSession
from pyspark.sql.functions import explode, split, col, lower, regexp_replace
import sys
import os
import time  # <--- Importamos para medir el tiempo

# 1. Validación de argumentos
if len(sys.argv) < 2:
    print("Error: Indica la ruta del fichero en HDFS.")
    sys.exit(1)

input_path = sys.argv[1]
base_name = os.path.basename(input_path).split('.')[0]
output_path = f"/resultados/{base_name}_counts"

# 2. Inicializar sesión
spark = SparkSession.builder.appName(f"WordCount_Timer_{base_name}").getOrCreate()

try:
    print(f"\n>>> Iniciando procesamiento: {input_path}")
    
    # --- INICIO DEL TIEMPO ---
    start_time = time.time()

    # 3. Leer el fichero
    df = spark.read.text(input_path)

    # 4. Procesamiento (Limpieza y filtrado)
    stop_words = ["sus", "o", "al", "con", "lo", "le", "me", "mi", "su", "de", 
                  "la", "que", "el", "en", "y", "a", "los", "del", "se", "las", 
                  "por", "un", "una", "es", "no", "más", "como", "dijo", "su"]

    words = df.select(
        explode(
            split(regexp_replace(lower(col("value")), r'[^\w\s]', ''), r'\s+')
        ).alias("word")
    ).filter(col("word") != "")

    resultado = words.filter(~col("word").isin(stop_words)) \
                     .groupBy("word") \
                     .count() \
                     .orderBy(col("count").desc())

    # 5. Ejecutar y Guardar (Acciones que disparan el trabajo en los Workers)
    # Importante: Spark es "lazy", si no hacemos una acción, el cronómetro no medirá nada real.
    resultado.write.mode("overwrite").parquet(output_path)
    
    # --- FIN DEL TIEMPO ---
    end_time = time.time()
    
    duration = end_time - start_time

    # 6. Resultados
    print("\n" + "="*50)
    print("¡Proceso completado con éxito!")
    print(f"Tiempo total: {duration:.2f} segundos")
    print(f"Salida: {output_path}")
    print("="*50 + "\n")
    print(f"Top 20 palabras en {input_path}:")
    resultado.show(20)
    print("="*50 + "\n")
    
except Exception as e:
    print(f"Error: {e}")

finally:
    spark.stop()
