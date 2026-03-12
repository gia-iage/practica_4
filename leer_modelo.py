import pandas as pd
import sys

# 1. Validación de argumentos (cero hardcodeo)
if len(sys.argv) < 2:
    print("Error: Debes indicar la ruta local del archivo Parquet.")
    print("Uso: python leer_local.py /ruta/local/fichero.parquet")
    sys.exit(1)

ruta_local = sys.argv[1]

print(f"\n>>> Leyendo el fichero local con Pandas: {ruta_local}")

try:
    # 2. Leemos el Parquet
    df_modelo = pd.read_parquet(ruta_local)

    # 3. Mostramos las columnas disponibles
    print("\n--- Las columnas que ha encontrado Pandas ---")
    print(df_modelo.columns.tolist())

    print("\n--- El contenido de la Ecuación Matemática ---")
    
    # 4. Extraemos la primera fila (solo hay un modelo)
    fila_modelo = df_modelo.iloc[0]
    
    # Extraemos los diccionarios y los formateamos en vertical
    if 'coefficientMatrix' in df_modelo.columns:
        # Accedemos a la clave 'values' dentro del diccionario de la matriz
        coeficientes = fila_modelo['coefficientMatrix']['values']
        print("\n>> Coeficientes (Pesos de Edad y Saldo):")
        for i, coef in enumerate(coeficientes):
            print(f"   - Peso {i+1}: {coef:.6f}")
            
    if 'interceptVector' in df_modelo.columns:
        # Accedemos a la clave 'values' del diccionario del vector
        intercepto = fila_modelo['interceptVector']['values'][0]
        print(f"\n>> Intercepto (Punto de partida):")
        print(f"   - Valor: {intercepto:.6f}")
        print("\n" + "="*50 + "\n")

except Exception as e:
    print(f"Error al intentar leer el archivo Parquet: {e}")
