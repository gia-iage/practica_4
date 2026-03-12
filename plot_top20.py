from pyspark.sql import SparkSession
import matplotlib.pyplot as plt

spark = SparkSession.builder.getOrCreate()

# 1. Leemos el Parquet de HDFS
df = spark.read.parquet("/resultados/quijote_large_counts")

# 2. Tomamos solo las 20 palabras más frecuentes
top_20 = df.limit(20).toPandas()

# 3. Creamos un gráfico de barras
plt.figure(figsize=(12,7))
plt.bar(top_20['word'], top_20['count'], color='skyblue')
plt.xlabel('Palabra')
plt.ylabel('Frecuencia')
plt.title('Top 20 palabras más frecuentes en El Quijote (filtradas)')
plt.xticks(rotation=45)

# 4. Guardarlo como imagen en la VM
plt.savefig('/vagrant/grafico_quijote.png')
print("¡Gráfico generado en /vagrant/grafico_quijote.png!")
