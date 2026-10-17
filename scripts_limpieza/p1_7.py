"""
Tarea: P1.7 — Agregados satelitales por parcela
Proyecto: Cebada360
"""

import os
import pandas as pd


# Definir la carpeta donde se encuentran los archivos procesados
BASE_DIR = "DATASET_RETO_AGRO_2026_LIMPIO"

# Establecer el periodo del ciclo agrícola que se analizará
DATA_START = pd.Timestamp("2025-04-01")
DATA_CUTOFF = pd.Timestamp("2025-10-31 23:59:59.999999")


# Definir las rutas de los archivos de entrada y salida
BASICO_FILE = os.path.join(
    BASE_DIR,
    "basico_temporal_normalizado.csv"
)

PRO_FILE = os.path.join(
    BASE_DIR,
    "pro_temporal_normalizado.csv"
)

OUTPUT_FILE = os.path.join(
    BASE_DIR,
    "satellite_features.csv"
)


# Definir los índices satelitales disponibles para cada sensor
INDICES_POR_SENSOR = {
    "Sentinel-2": [
        "ndvi",
        "evi",
        "crc",
        "mcrc",
        "ndsvi",
        "srndi",
        "mra",
        "lai",
        "fapar",
        "savi",
        "ndti",
        "sti",
        "ndwi",
        "endwi",
        "msi",
        "emsi",
        "dswi2",
        "dswi3",
        "dswi4",
        "dswi5",
        "nddi",
        "enddi",
    ],

    "Landsat": [
        "vi6t",
    ],

    "Planet": [
        "ndvi",
        "evi",
        "lai",
        "msavi",
    ],
}


# Establecer las estadísticas que se calcularán para cada índice
ESTADISTICAS = [
    "mean",
    "median",
    "max",
    "min",
    "std",
]


# Mostrar el inicio del proceso y cargar el archivo BÁSICO
print("P1.7 — AGREGADOS SATELITALES")
print("\nCargando BÁSICO...")

# Leer los registros satelitales del conjunto BÁSICO
basico = pd.read_csv(BASICO_FILE)

# Mostrar la cantidad de registros y columnas cargadas
print(f"  Registros: {len(basico):,}")
print(f"  Columnas:  {len(basico.columns)}")


# Cargar el archivo PRO, que contiene los datos del sensor Planet
print("\nCargando PRO...")

pro = pd.read_csv(PRO_FILE)

# Mostrar las dimensiones del conjunto PRO
print(f"  Registros: {len(pro):,}")
print(f"  Columnas:  {len(pro.columns)}")


# Unificar el nombre del identificador de parcela en ambos conjuntos
basico = basico.rename(
    columns={"ID_POLIGONO": "parcel_id"}
)

pro = pro.rename(
    columns={"ID_POLIGONO": "parcel_id"}
)

# Filtrar los registros para conservar únicamente el ciclo agrícola
# comprendido entre abril y octubre de 2025
for nombre, df in [("BÁSICO", basico), ("PRO", pro)]:
    # Verificar que exista la columna con la fecha de captura
    if "fecha_captura" not in df.columns:
        raise ValueError(f"{nombre}: falta fecha_captura.")

    # Convertir las fechas a un formato que permita compararlas
    # Las fechas que no puedan convertirse se consideran inválidas
    df["fecha_captura"] = pd.to_datetime(
        df["fecha_captura"], errors="coerce"
    )

    # Detener el proceso si se encuentran fechas inválidas
    if df["fecha_captura"].isna().any():
        raise ValueError(
            f"{nombre}: existen fechas inválidas."
        )

    # Registrar la cantidad original de filas antes del filtrado
    antes = len(df)

    # Conservar únicamente las capturas realizadas dentro del periodo
    df = df.loc[
        df["fecha_captura"].between(
            DATA_START, DATA_CUTOFF, inclusive="both"
        )
    ].copy()

    # Mostrar cuántos registros permanecen después del filtrado
    print(
        f"{nombre}: {antes:,} registros originales; "
        f"{len(df):,} dentro del ciclo 2025."
    )

    # Actualizar el conjunto correspondiente con los datos filtrados
    if nombre == "BÁSICO":
        basico = df
    else:
        pro = df

    # Detener el proceso si no existen capturas en el periodo solicitado
    if df.empty:
        raise ValueError(
            f"{nombre}: no hay registros en abril-octubre de 2025."
        )


# Revisar qué sensores están presentes en cada conjunto de datos
print("\nSensores BÁSICO:")

# Contabilizar los registros por sensor, incluyendo los valores nulos
print(
    basico["sensor"].value_counts(
        dropna=False
    )
)

print("\nSensores PRO:")

# Mostrar la distribución de registros por sensor en el conjunto PRO
print(
    pro["sensor"].value_counts(
        dropna=False
    )
)


# Definir una función para calcular las estadísticas satelitales
def calcular_agregados(
    df,
    sensor,
    indices,
):
    """
    Calcula estadísticas temporales por parcela
    para un sensor determinado.

    Se utilizan las columnas *_promedio de cada índice.
    """

    # Mostrar el sensor que se está procesando
    print("\n" + "-" * 60)
    print(f"Procesando: {sensor}")
    print("-" * 60)

    # Filtrar los registros correspondientes al sensor seleccionado
    datos = df[
        df["sensor"] == sensor
    ].copy()

    # Mostrar el número de registros y parcelas que se van a analizar
    print(
        f"Registros: {len(datos):,}"
    )

    print(
        f"Parcelas:  {datos['parcel_id'].nunique():,}"
    )

    # Crear el DataFrame inicial con los identificadores únicos
    # de las parcelas que tienen registros para este sensor
    resultado = pd.DataFrame({
        "parcel_id": datos[
            "parcel_id"
        ].drop_duplicates()
    })

    # Recorrer los índices satelitales definidos para el sensor
    for indice in indices:

        # Construir el nombre de la columna con el valor promedio
        columna = f"{indice}_promedio"

        # Comprobar que la columna exista antes de calcular estadísticas
        if columna not in datos.columns:
            print(
                f"  ⚠ No existe: {columna}"
            )
            continue

        # Convertir los valores del índice a formato numérico
        # Los valores que no puedan convertirse se transforman en NaN
        datos[columna] = pd.to_numeric(
            datos[columna],
            errors="coerce"
        )

        # Contar cuántos valores válidos existen para el índice
        valores_validos = (
            datos[columna]
            .notna()
            .sum()
        )

        # Omitir el índice cuando no contiene valores numéricos válidos
        if valores_validos == 0:
            print(
                f"  ⚠ Sin datos: {columna}"
            )
            continue

        # Informar cuántos valores válidos se utilizarán
        print(
            f"  ✓ {indice.upper():<6} "
            f"{valores_validos:,} valores"
        )

        # Agrupar los registros por parcela para calcular sus estadísticas
        grupo = datos.groupby(
            "parcel_id"
        )[columna]

        # Calcular la media, mediana, máximo, mínimo y desviación estándar
        agregados = grupo.agg(
            ESTADISTICAS
        )

        # Calcular el rango como la diferencia entre el máximo y el mínimo
        agregados["range"] = (
            agregados["max"]
            - agregados["min"]
        )

        # Definir el prefijo que identificará las columnas de cada sensor
        prefijos = {
            "Sentinel-2": "sentinel2",
            "Landsat": "landsat",
            "Planet": "planet",
        }

        # Obtener el prefijo correspondiente al sensor procesado
        prefijo_sensor = prefijos[sensor]

        # Renombrar las columnas para identificar el sensor,
        # el índice satelital y la estadística calculada
        agregados = agregados.rename(
            columns={
                "mean":
                    f"{prefijo_sensor}_{indice}_mean",

                "median":
                    f"{prefijo_sensor}_{indice}_median",

                "max":
                    f"{prefijo_sensor}_{indice}_max",

                "min":
                    f"{prefijo_sensor}_{indice}_min",

                "std":
                    f"{prefijo_sensor}_{indice}_std",

                "range":
                    f"{prefijo_sensor}_{indice}_range",
            }
        )

        # Incorporar las estadísticas calculadas al resultado
        # utilizando parcel_id como identificador de unión
        resultado = resultado.merge(
            agregados,
            left_on="parcel_id",
            right_index=True,
            how="left",
        )

    # Devolver la tabla con las estadísticas calculadas por parcela
    return resultado


# Calcular las estadísticas de los índices correspondientes a Sentinel-2
sentinel_features = calcular_agregados(
    basico,
    "Sentinel-2",
    INDICES_POR_SENSOR["Sentinel-2"],
)


# Calcular las estadísticas del índice VI6T para Landsat
landsat_features = calcular_agregados(
    basico,
    "Landsat",
    INDICES_POR_SENSOR["Landsat"],
)


# Calcular las estadísticas de los índices disponibles para Planet
planet_features = calcular_agregados(
    pro,
    "Planet",
    INDICES_POR_SENSOR["Planet"],
)


# Combinar las estadísticas de los tres sensores en una sola tabla
print("COMBINANDO FEATURES")

# Unir los resultados de Sentinel-2 y Landsat mediante el identificador
# Se utiliza una unión externa para conservar todas las parcelas
features = sentinel_features.merge(
    landsat_features,
    on="parcel_id",
    how="outer",
)

# Incorporar las estadísticas de Planet al resultado combinado
features = features.merge(
    planet_features,
    on="parcel_id",
    how="outer",
)


# Ordenar los registros por identificador y reiniciar el índice
features = (
    features
    .sort_values("parcel_id")
    .reset_index(drop=True)
)


# Validar la cantidad de parcelas, filas, columnas e IDs duplicados
print("VALIDACIÓN P1.7")

# Mostrar la cantidad de identificadores de parcela únicos
print(
    f"Parcelas únicas: "
    f"{features['parcel_id'].nunique()}"
)

# Mostrar la cantidad total de filas y columnas generadas
print(
    f"Filas finales:    "
    f"{len(features):,}"
)

print(
    f"Columnas finales: "
    f"{len(features.columns):,}"
)

# Contar los identificadores de parcela duplicados
duplicados = (
    features["parcel_id"]
    .duplicated()
    .sum()
)

print(
    f"IDs duplicados:   "
    f"{duplicados}"
)

# Detener el proceso si una parcela aparece más de una vez
if duplicados > 0:
    raise ValueError(
        "ERROR: existen IDs de parcela duplicados."
    )


# Comparar los identificadores generados con el maestro de parcelas
parcel_master = pd.read_csv(
    os.path.join(
        BASE_DIR,
        "parcel_master.csv"
    ),
    usecols=["parcel_id"]
)

# Convertir los identificadores de ambos archivos en conjuntos
# para facilitar la comparación de parcelas
ids_master = set(
    parcel_master["parcel_id"]
)

ids_features = set(
    features["parcel_id"]
)

# Identificar las parcelas del maestro que no aparecen en los agregados
faltantes = (
    ids_master - ids_features
)

# Identificar las parcelas de los agregados que no están en el maestro
extras = (
    ids_features - ids_master
)

# Mostrar los resultados de la comparación de identificadores
print(
    f"\nParcelas en parcel_master: "
    f"{len(ids_master)}"
)

print(
    f"Parcelas en P1.7:          "
    f"{len(ids_features)}"
)

print(
    f"Parcelas faltantes:        "
    f"{len(faltantes)}"
)

print(
    f"Parcelas extra:            "
    f"{len(extras)}"
)

# Mostrar los identificadores que faltan, si existen
if faltantes:
    print("\nIDs faltantes:")
    print(
        sorted(faltantes)
    )

# Mostrar los identificadores adicionales, si existen
if extras:
    print("\nIDs extra:")
    print(
        sorted(extras)
    )


# Revisar la cantidad total de valores nulos en el resultado
total_nulos = (
    features.isna()
    .sum()
    .sum()
)

print(
    f"\nValores NaN totales: "
    f"{total_nulos:,}"
)

# Mostrar las columnas que contienen valores nulos
if total_nulos > 0:

    print(
        "\nColumnas con NaN:"
    )

    # Contar los valores nulos por columna y ordenarlos de mayor a menor
    nulos = (
        features.isna()
        .sum()
        .sort_values(
            ascending=False
        )
    )

    # Mostrar únicamente las columnas que tienen al menos un valor nulo
    print(
        nulos[
            nulos > 0
        ].to_string()
    )


# Guardar la tabla final de agregados satelitales en formato CSV
features.to_csv(
    OUTPUT_FILE,
    index=False
)


# Mostrar el resumen de ejecución y la ubicación del archivo generado

print("P1.7 COMPLETADO")

print(
    f"\nArchivo generado:"
    f"\n{OUTPUT_FILE}"
)

# Mostrar las dimensiones finales del conjunto de datos
print(
    f"\nDimensiones:"
    f" {features.shape[0]:,} filas × "
    f"{features.shape[1]:,} columnas"
)

# Mostrar una muestra de los nombres de las primeras columnas
print("\nPrimeras 20 columnas:")

print(
    features.columns[
        :20
    ].tolist()
)

# Mostrar los nombres de las últimas columnas generadas
print("\nÚltimas 10 columnas:")

print(
    features.columns[
        -10:
    ].tolist()
)