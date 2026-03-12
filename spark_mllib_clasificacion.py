from pyspark.sql import SparkSession
from pyspark.ml.feature import VectorAssembler
from pyspark.ml.classification import LogisticRegression
from pyspark.ml.evaluation import BinaryClassificationEvaluator
from pyspark.sql.functions import rand, when, col
import time
import sys

if len(sys.argv) < 2:
    print("Error: Debes indicar la ruta del dataset de entrenamiento en HDFS.")
    print("Uso: spark-submit spark_mllib_clasificacion.py /ruta/dataset.parquet")
    sys.exit(1)

ruta_entrada = sys.argv[1]

# Inicializamos Spark
spark = SparkSession.builder.appName("MLlib_PrediccionCompras").getOrCreate()

try:
    print("="*60)
    print("Spark MLlib: LogisticRegression")
    print("="*60 + "\n")
    print(f">>> 1. Leyendo datos históricos desde HDFS: {ruta_entrada}")
    df = spark.read.parquet(ruta_entrada)

    print(">>> 2. Preparando los datos (VectorAssembler)...")
    # Empaquetamos 'edad' y 'saldo' en una sola columna llamada 'features'
    assembler = VectorAssembler(inputCols=["edad", "saldo"], outputCol="features")
    df_transformado = assembler.transform(df)

    print(">>> 3. Dividiendo los datos: Train (70%) y Test (30%)...")
    # Es vital en IA no examinar al modelo con los datos que usó para estudiar
    train_data, test_data = df_transformado.randomSplit([0.7, 0.3], seed=42)

    print(">>> 4. Entrenando el modelo (Regresión Logística)...")
    start_time = time.time()
    
    # Configuramos el algoritmo
    lr = LogisticRegression(featuresCol="features", labelCol="comprara_producto", maxIter=30)
    # .fit() es la orden que desata el procesamiento intensivo en los Workers
    modelo = lr.fit(train_data)
    
    training_time = time.time() - start_time
    print(f"    Entrenamiento completado en {training_time:.2f} segundos")

    print(">>> 5. Evaluando el modelo con los datos de Test...")
    # Le pedimos al modelo que adivine si los clientes de Test comprarán o no
    predicciones = modelo.transform(test_data)
    # Medimos su precisión matemática (Área bajo la curva ROC)
    evaluador = BinaryClassificationEvaluator(labelCol="comprara_producto", rawPredictionCol="rawPrediction", metricName="areaUnderROC")
    precision = evaluador.evaluate(predicciones)

    print("\n" + "="*60)
    print("RESULTADOS DEL MODELO MLlib")
    print(f"Precisión del modelo: {precision * 100:.2f}%")
    print("\nComparativa real vs predicción (Primeros 10 casos):")
    # Mostramos: Edad, Saldo, Lo que realmente pasó, y la Adivinanza de la IA
    predicciones.select("edad", "saldo", "comprara_producto", "prediction").show(10)
    print("="*60)
    print(f"Ecuación aprendida - Coeficientes: {modelo.coefficients}")
    print(f"Ecuación aprendida - Intersección: {modelo.intercept}")
    print("="*60)
    
    ruta_modelo = "/modelos/clasificador_banco"
    print(f">>> 6. Guardando el modelo en HDFS: {ruta_modelo}")
    modelo.write().overwrite().save(ruta_modelo)
    print(">>> Modelo guardado con éxito! Proceso ML finalizado.")
    
except Exception as e:
    print(f"Error en el proceso ML: {e}")

finally:
    spark.stop()
