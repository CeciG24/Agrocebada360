"""
Tarea: P1.3 — Normalizar fechas y campos temporales
Proyecto: Cebada360
"""

import os
import pandas as pd

# Definicion de las rutas del dataset original y de la carpeta de salida para datos limpios
RUTA_DATASET = "DATASET_RETO_AGRO_2026"
RUTA_SALIDA = "DATASET_RETO_AGRO_2026_LIMPIO"

# Diccionario de configuracion con las rutas de entrada y salida para los conjuntos basico y pro
ARCHIVOS = {
    "basico": {
        "entrada": os.path.join(
            RUTA_DATASET,
            "Conjunto_datos_BASICO_AgroCebada2026.csv"
        ),
        "salida": os.path.join(
            RUTA_SALIDA,
            "basico_temporal_normalizado.csv"
        )
    },
    "pro": {
        "entrada": os.path.join(
            RUTA_DATASET,
            "Conjunto_datos_PRO_AgroCebada.csv"
        ),
        "salida": os.path.join(
            RUTA_SALIDA,
            "pro_temporal_normalizado.csv"
        )
    }
}


def normalizar_temporal(ruta_entrada, ruta_salida, nombre_dataset):
    """
    Funcion para cargar, validar y normalizar la columna de fecha de captura,
    extrayendo variables temporales derivadas y exportando el resultado limpio.
    """

    print(f"NORMALIZANDO: {nombre_dataset}")

    print("Leyendo archivo...")

    # Carga del archivo CSV original en un DataFrame de pandas
    df = pd.read_csv(ruta_entrada)

    print(f"Registros originales: {len(df)}")

    # Validacion de la existencia de la columna obligatoria de fecha
    if "fecha_captura" not in df.columns:
        raise ValueError(
            f"El archivo {nombre_dataset} no contiene "
            f"la columna 'fecha_captura'."
        )

    # Conversion de la columna de texto a formato de fecha (DD/MM/YYYY) manejando errores
    fecha = pd.to_datetime(
        df["fecha_captura"],
        format="%d/%m/%Y",
        errors="coerce"
    )

    fechas_invalidas = fecha.isna().sum()

    print(f"Fechas inválidas: {fechas_invalidas}")

    # Control de errores si se detectan fechas que no pudieron ser convertidas
    if fechas_invalidas > 0:
        raise ValueError(
            f"Se encontraron {fechas_invalidas} fechas inválidas "
            f"en {nombre_dataset}."
        )

    # Normalización de la fecha al formato estándar YYYY-MM-DD
    df["fecha_captura"] = (
        fecha.dt.strftime("%Y-%m-%d")
        .str.replace("/", "-", regex=False)
    )
   
    # Creación de variables temporales derivadas para análisis y modelado
    # Año
    df["anio"] = fecha.dt.year

    # Mes
    df["mes"] = fecha.dt.month

    # Día del año (1 de enero = 1, 31 de diciembre = 365 o 366)
    df["dia_anio"] = fecha.dt.dayofyear

    # Día de la semana basado en el estándar ISO (Lunes = 1 hasta Domingo = 7)
    df["dia_semana"] = fecha.dt.isocalendar().day.astype(int)

    # Impresión de estadísticas y validaciones básicas del resultado
    print(f"Fecha mínima: {df['fecha_captura'].min()}")
    print(f"Fecha máxima: {df['fecha_captura'].max()}")

    print("\nAños:")
    print(df["anio"].value_counts().sort_index())

    print("\nMeses:")
    print(df["mes"].value_counts().sort_index())

    print("\nDías de la semana:")
    print(df["dia_semana"].value_counts().sort_index())

    print("\nParcelas únicas:")
    print(df["ID_POLIGONO"].nunique())

    print("\nSensores:")
    print(df["sensor"].value_counts(dropna=False))

    # Muestra de un ejemplo con las columnas temporales generadas
    print("\nEjemplo de normalización:")

    columnas_temporales = [
        "fecha_captura",
        "anio",
        "mes",
        "dia_anio",
        "dia_semana"
    ]

    print(
        df[columnas_temporales]
        .head(10)
        .to_string(index=False)
    )

    # Creación automática de la carpeta de salida si no existe previamente
    os.makedirs(RUTA_SALIDA, exist_ok=True)

    # Exportación del DataFrame normalizado a un nuevo archivo CSV
    df.to_csv(
        ruta_salida,
        index=False,
        encoding="utf-8-sig"
    )

    print("\nArchivo generado:")
    print(ruta_salida)

    print(f"Registros guardados: {len(df)}")

    return df


if __name__ == "__main__":
    # Procesamiento del conjunto básico
    normalizar_temporal(
        ARCHIVOS["basico"]["entrada"],
        ARCHIVOS["basico"]["salida"],
        "BÁSICO"
    )

    # Procesamiento del conjunto pro
    normalizar_temporal(
        ARCHIVOS["pro"]["entrada"],
        ARCHIVOS["pro"]["salida"],
        "PRO"
    )
