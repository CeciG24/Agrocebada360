"""
Tarea: P1.9 — Features climáticas por ventanas
Proyecto: Cebada360
"""

import pandas as pd
import numpy as np
from pathlib import Path


# Definir las rutas de los archivos de entrada y salida
BASE_DIR = Path("DATASET_RETO_AGRO_2026_LIMPIO")
INPUT_FILE = BASE_DIR / "climate_timeseries.csv"
OUTPUT_FILE = BASE_DIR / "climate_features.csv"


# Cargar los datos climáticos por parcela
print("P1.9 — FEATURES CLIMÁTICAS POR VENTANAS")

# Leer el archivo que contiene las series temporales climáticas
df = pd.read_csv(INPUT_FILE)

# Mostrar información general del conjunto de datos cargado
print(f"\nArchivo de entrada: {INPUT_FILE}")
print(f"Filas iniciales: {len(df):,}")
print(f"Parcelas: {df['parcel_id'].nunique()}")


# Validar que existan las columnas necesarias para el procesamiento
required_columns = [
    "parcel_id",
    "fecha_captura",
    "precip_mm",
    "tmin_c",
    "tmax_c",
]

# Identificar las columnas requeridas que no están presentes
missing_columns = [
    col for col in required_columns
    if col not in df.columns
]

# Detener la ejecución si falta alguna columna obligatoria
if missing_columns:
    raise ValueError(
        f"Faltan columnas requeridas: {missing_columns}"
    )


# Convertir las fechas a un formato compatible con pandas
df["fecha_captura"] = pd.to_datetime(
    df["fecha_captura"],
    errors="coerce"
)

# Detener el proceso si existen fechas que no pudieron convertirse
if df["fecha_captura"].isna().any():
    raise ValueError(
        "Existen fechas inválidas en fecha_captura."
    )


# Calcular la amplitud térmica como la diferencia entre
# la temperatura máxima y la temperatura mínima
df["amplitud_termica_c"] = (
    df["tmax_c"] - df["tmin_c"]
)


# Verificar que todos los registros tengan un identificador de parcela
if df["parcel_id"].isna().any():
    raise ValueError(
        "Existen registros sin parcel_id."
    )

# Revisar si existen valores faltantes en las variables climáticas
if df[required_columns[2:]].isna().any().any():
    print("\nADVERTENCIA: existen valores faltantes climáticos.")

    # Mostrar la cantidad de valores nulos por variable climática
    print(
        df[required_columns[2:]]
        .isna()
        .sum()
    )


# Calcular las características climáticas de una ventana temporal
def calcular_features(grupo, sufijo):
    """
    Calcula features climáticas para una ventana temporal.

    Obtiene la precipitación acumulada y promedio, las temperaturas
    medias y las estadísticas de la amplitud térmica.
    """

    # Calcular las estadísticas de las variables climáticas
    resultado = {
        # Sumar la precipitación registrada durante la ventana
        "precip_total_mm": grupo["precip_mm"].sum(),

        # Calcular la precipitación media del periodo
        "precip_mean_mm": grupo["precip_mm"].mean(),

        # Calcular la temperatura mínima media
        "tmin_mean_c": grupo["tmin_c"].mean(),

        # Calcular la temperatura máxima media
        "tmax_mean_c": grupo["tmax_c"].mean(),

        # Calcular la amplitud térmica media
        "amplitud_termica_mean_c": (
            grupo["amplitud_termica_c"].mean()
        ),

        # Calcular la desviación estándar de la amplitud térmica
        "amplitud_termica_std_c": (
            grupo["amplitud_termica_c"].std()
        ),
    }

    # Agregar el sufijo correspondiente a cada nombre de columna
    # para identificar el año o la ventana temporal analizada
    return {
        f"{nombre}_{sufijo}": valor
        for nombre, valor in resultado.items()
    }


# Definir las fechas que delimitan el ciclo agrícola de 2025
DATA_START = pd.Timestamp("2025-04-01")
DATA_CUTOFF = pd.Timestamp("2025-10-31 23:59:59.999999")

# Establecer los años que se analizarán individualmente
# y conservar un esquema fijo de columnas para todos los años
ANIOS = [2022, 2023, 2024, 2025]

# Obtener el año de cada observación a partir de su fecha
df["anio"] = df["fecha_captura"].dt.year

# Filtrar los registros históricos y las observaciones del ciclo 2025
# Para 2022-2024 se conservan todos los meses disponibles
# Para 2025 únicamente se consideran los registros de abril a octubre
df_historico = df.loc[
    (df["anio"] < 2025)
    | (
        (df["anio"] == 2025)
        & df["fecha_captura"].between(
            DATA_START, DATA_CUTOFF, inclusive="both"
        )
    )
].copy()

# Informar qué periodos se utilizarán para calcular las características
print("\nVentanas utilizadas:")
print("2022, 2023 y 2024: datos históricos disponibles.")
print("2025: 2025-04-01 a 2025-10-31.")
print("2022_2025: históricos 2022-2024 + abril-octubre 2025.")


# Calcular las características climáticas para cada parcela
features = []

# Agrupar los registros por identificador de parcela
for parcel_id, grupo in df_historico.groupby("parcel_id"):

    # Crear el registro que almacenará las características de la parcela
    fila = {"parcel_id": parcel_id}

    # Procesar individualmente cada uno de los años establecidos
    for anio in ANIOS:

        # Seleccionar los registros correspondientes al año actual
        grupo_anual = grupo.loc[grupo["anio"] == anio]

        # Mantener las columnas del año aunque no existan observaciones
        if grupo_anual.empty:

            # Asignar NaN a las características que no se pueden calcular
            # por ausencia de datos para ese año
            for nombre in [
                "precip_total_mm",
                "precip_mean_mm",
                "tmin_mean_c",
                "tmax_mean_c",
                "amplitud_termica_mean_c",
                "amplitud_termica_std_c",
            ]:
                fila[f"{nombre}_{anio}"] = np.nan

        else:

            # Calcular las características climáticas del año
            # y agregarlas al registro de la parcela
            fila.update(
                calcular_features(grupo_anual, str(anio))
            )

    # Calcular las características de la ventana combinada:
    # años históricos disponibles de 2022-2024 y abril-octubre de 2025
    fila.update(
        calcular_features(grupo, "2022_2025")
    )

    # Agregar el registro completo a la lista de resultados
    features.append(fila)

# Convertir la lista de resultados en un DataFrame
features_df = pd.DataFrame(features)


# Definir el orden fijo de las columnas del archivo de salida
columnas_ordenadas = ["parcel_id"]

# Incorporar las seis características correspondientes a cada año
for anio in ANIOS:
    columnas_ordenadas.extend([
        f"precip_total_mm_{anio}",
        f"precip_mean_mm_{anio}",
        f"tmin_mean_c_{anio}",
        f"tmax_mean_c_{anio}",
        f"amplitud_termica_mean_c_{anio}",
        f"amplitud_termica_std_c_{anio}",
    ])

# Agregar las seis características de la ventana combinada
columnas_ordenadas.extend([
    "precip_total_mm_2022_2025",
    "precip_mean_mm_2022_2025",
    "tmin_mean_c_2022_2025",
    "tmax_mean_c_2022_2025",
    "amplitud_termica_mean_c_2022_2025",
    "amplitud_termica_std_c_2022_2025",
])

# Reordenar las columnas y ordenar las parcelas por identificador
features_df = features_df.reindex(columns=columnas_ordenadas)
features_df = features_df.sort_values("parcel_id").reset_index(drop=True)


# Validar las dimensiones y los identificadores del resultado
print("\nValidación P1.9")

# Mostrar el número de filas, columnas y parcelas únicas
print(f"Filas: {len(features_df)}")
print(f"Columnas: {len(features_df.columns)}")
print(f"Parcelas únicas: {features_df['parcel_id'].nunique()}")

# Contabilizar los valores nulos de toda la tabla
print(f"NaN totales: {features_df.isna().sum().sum()}")

# Detener el proceso si existen identificadores de parcela duplicados
if features_df["parcel_id"].duplicated().any():
    raise ValueError("Hay parcel_id duplicados en climate_features.")

# Comprobar que el resultado tenga las 31 columnas esperadas
if len(features_df.columns) != 31:
    raise ValueError(
        f"Se esperaban 31 columnas, se obtuvieron "
        f"{len(features_df.columns)}."
    )


features_df.to_csv(OUTPUT_FILE, index=False)

print(f"\nArchivo generado: {OUTPUT_FILE}")