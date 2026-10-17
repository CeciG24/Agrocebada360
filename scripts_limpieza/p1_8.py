"""
Tarea: P1.8 — Features temporales/fenológicas
Proyecto: Cebada360
"""

import os
import numpy as np
import pandas as pd


# Definir la carpeta de los archivos procesados
BASE_DIR = "DATASET_RETO_AGRO_2026_LIMPIO"

# Establecer el periodo del ciclo agrícola de abril a octubre de 2025
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
    "fenologia_features.csv"
)


# Calcular el área bajo la curva de NDVI utilizando las fechas reales
def calcular_auc(fecha, valores):
    """
    Calcula el área bajo la curva utilizando las fechas
    reales de las observaciones.
    """

    # Se requieren al menos dos observaciones para calcular el área
    if len(valores) < 2:
        return np.nan

    # Convertir las fechas en días transcurridos desde la primera observación
    # para considerar los intervalos reales entre las capturas
    dias = (
        fecha - fecha.iloc[0]
    ).dt.total_seconds() / 86400.0

    # Aplicar el método trapezoidal para calcular el área bajo la curva
    return np.trapezoid(
        valores.to_numpy(),
        dias.to_numpy()
    )


# Procesar las observaciones de un sensor y calcular sus características fenológicas
def procesar_sensor(df, sensor):

    # Mostrar el nombre del sensor que se está procesando
    print(f"\nProcesando: {sensor}")

    # Filtrar los registros correspondientes al sensor seleccionado
    datos = df[
        df["sensor"] == sensor
    ].copy()

    # Mostrar la cantidad de registros y parcelas disponibles
    print(
        f"Registros: {len(datos):,}"
    )

    print(
        f"Parcelas:  "
        f"{datos['parcel_id'].nunique():,}"
    )

    # Convertir los valores de NDVI a formato numérico
    # Los valores que no puedan convertirse se tratarán como nulos
    datos["ndvi_promedio"] = pd.to_numeric(
        datos["ndvi_promedio"],
        errors="coerce"
    )

    # Convertir la fecha de captura a un formato de fecha válido
    datos["fecha_captura"] = pd.to_datetime(
        datos["fecha_captura"],
        errors="coerce"
    )

    # Contar las observaciones que tienen valores válidos de NDVI
    valores_validos = datos[
        "ndvi_promedio"
    ].notna().sum()

    print(
        f"NDVI válidos: {valores_validos:,}"
    )

    # Omitir el sensor si no dispone de valores válidos de NDVI
    if valores_validos == 0:

        print(
            "  ⚠ Este sensor no tiene NDVI."
        )

        print(
            "  ⚠ Se omite de las features "
            "fenológicas."
        )

        return None

    # Eliminar las observaciones que no tienen fecha o valor de NDVI
    datos = datos.dropna(
        subset=[
            "fecha_captura",
            "ndvi_promedio",
        ]
    )

    # Ordenar las observaciones por parcela y fecha
    # para conservar la secuencia temporal del ciclo agrícola
    datos = datos.sort_values(
        [
            "parcel_id",
            "fecha_captura",
        ]
    )

    # Crear una lista para almacenar las características de cada parcela
    resultados = []

    # Procesar por separado las observaciones de cada parcela
    for parcel_id, grupo in datos.groupby(
        "parcel_id"
    ):

        grupo = grupo.copy()

        # Si existen varias observaciones en una misma fecha,
        # calcular el promedio diario de NDVI
        grupo = (
            grupo
            .groupby(
                "fecha_captura",
                as_index=False
            )["ndvi_promedio"]
            .mean()
            .sort_values(
                "fecha_captura"
            )
        )

        # Omitir la parcela si no quedan observaciones disponibles
        if len(grupo) == 0:
            continue

        # Separar las fechas y los valores de NDVI en series independientes
        # y reiniciar sus índices para facilitar los cálculos posteriores
        fechas = grupo[
            "fecha_captura"
        ].reset_index(drop=True)

        ndvi = grupo[
            "ndvi_promedio"
        ].reset_index(drop=True)

        # Identificar el valor máximo de NDVI durante el ciclo analizado
        indice_pico = ndvi.idxmax()

        # Obtener el valor de NDVI correspondiente al máximo
        ndvi_peak = ndvi.iloc[
            indice_pico
        ]

        # Obtener la fecha en la que se registró el máximo de NDVI
        peak_date = fechas.iloc[
            indice_pico
        ]

        # Obtener el día del año correspondiente a la fecha del máximo
        peak_doy = (
            peak_date.dayofyear
        )

        # Calcular la variabilidad temporal de los valores de NDVI
        # Si solo existe una observación, asignar una desviación estándar de cero
        if len(ndvi) > 1:

            ndvi_std_temporal = ndvi.std(
                ddof=1
            )

        else:

            ndvi_std_temporal = 0.0

        # Calcular el área bajo la curva de NDVI durante el periodo observado
        auc = calcular_auc(
            fechas,
            ndvi
        )

        # Calcular la tasa de crecimiento desde la primera observación
        # hasta la fecha en que se alcanza el máximo de NDVI
        if indice_pico > 0:

            # Obtener el valor inicial de NDVI de la parcela
            ndvi_inicio = ndvi.iloc[0]

            # Calcular los días transcurridos entre el inicio y el pico
            dias_crecimiento = (
                fechas.iloc[indice_pico]
                - fechas.iloc[0]
            ).total_seconds() / 86400.0

            # Dividir el cambio de NDVI entre los días transcurridos
            # para obtener la tasa media de crecimiento
            if dias_crecimiento > 0:

                growth_rate = (
                    ndvi_peak
                    - ndvi_inicio
                ) / dias_crecimiento

            else:

                growth_rate = np.nan

        else:

            # No se calcula el crecimiento si el máximo ocurre
            # en la primera observación disponible
            growth_rate = np.nan

        # Preparar las observaciones válidas para calcular la caída de NDVI
        # después del máximo registrado durante el ciclo
        posteriores = pd.DataFrame({
            "fecha": fechas,
            "ndvi": ndvi
        }).dropna(subset=["fecha", "ndvi"])

        # Obtener la fecha en la que se registró el máximo de NDVI
        fecha_pico = fechas.iloc[indice_pico]

        # Conservar únicamente las observaciones posteriores al máximo
        # y ordenarlas cronológicamente
        posteriores = posteriores[
            posteriores["fecha"] > fecha_pico
        ].sort_values("fecha")

        # Calcular la tasa de caída cuando existen observaciones posteriores
        if not posteriores.empty:

            # Obtener la última fecha y su valor correspondiente de NDVI
            fecha_final = posteriores["fecha"].iloc[-1]
            ndvi_final = posteriores["ndvi"].iloc[-1]

            # Calcular los días transcurridos desde el pico hasta la última fecha
            dias_decay = (
                fecha_final - fecha_pico
            ).total_seconds() / 86400.0

            # Calcular el cambio de NDVI por día después del máximo
            if dias_decay > 0:

                decay_rate = (
                    ndvi_final - ndvi_peak
                ) / dias_decay

            else:

                decay_rate = np.nan

        else:

            # Asignar un valor nulo si no hay observaciones posteriores al pico
            decay_rate = np.nan

        # Guardar las características fenológicas calculadas para la parcela
        resultados.append({

            "parcel_id": parcel_id,

            "ndvi_peak": ndvi_peak,

            "ndvi_peak_date":
                peak_date.strftime(
                    "%Y-%m-%d"
                ),

            "ndvi_peak_doy":
                peak_doy,

            "ndvi_auc":
                auc,

            "ndvi_growth_rate":
                growth_rate,

            "ndvi_decay_rate":
                decay_rate,

            "ndvi_std_temporal":
                ndvi_std_temporal,
        })

    # Verificar si se generaron resultados para alguna parcela
    if not resultados:

        print(
            "  ⚠ No se pudieron generar "
            "features."
        )

        return None

    # Convertir los resultados calculados en un DataFrame
    resultado = pd.DataFrame(
        resultados
    )

    # Informar cuántas parcelas tienen características fenológicas generadas
    print(
        f"  ✓ Features generadas para "
        f"{len(resultado):,} parcelas."
    )

    # Devolver las características calculadas para el sensor
    return resultado


# Agregar un prefijo a las columnas para identificar el sensor de origen
def agregar_prefijo(
    df,
    prefijo
):

    # Si no se generaron resultados para el sensor, devolver None
    if df is None:
        return None

    # Crear un diccionario con los nuevos nombres de las columnas
    # y conservar parcel_id sin modificaciones
    columnas = {
        col: f"{prefijo}_{col}"
        for col in df.columns
        if col != "parcel_id"
    }

    # Renombrar las columnas y devolver el DataFrame actualizado
    return df.rename(
        columns=columnas
    )


# Mostrar el inicio de la tarea de generación de características fenológicas
print("\nP1.8 — FEATURES TEMPORALES / FENOLÓGICAS")


# Cargar el conjunto BÁSICO con las observaciones satelitales
print("\nCargando BÁSICO...")

basico = pd.read_csv(
    BASICO_FILE
)

# Mostrar la cantidad de registros y columnas del conjunto BÁSICO
print(
    f"  Registros: {len(basico):,}"
)

print(
    f"  Columnas:  {len(basico.columns)}"
)


# Cargar el conjunto PRO con las observaciones satelitales
print("\nCargando PRO...")

pro = pd.read_csv(
    PRO_FILE
)

# Mostrar la cantidad de registros y columnas del conjunto PRO
print(
    f"  Registros: {len(pro):,}"
)

print(
    f"  Columnas:  {len(pro.columns)}"
)


# Normalizar el identificador de parcela en ambos conjuntos
basico = basico.rename(
    columns={
        "ID_POLIGONO": "parcel_id"
    }
)

pro = pro.rename(
    columns={
        "ID_POLIGONO": "parcel_id"
    }
)

# Filtrar las observaciones para conservar únicamente el ciclo de abril
# a octubre de 2025 antes de calcular los indicadores fenológicos
for nombre, df in [("BÁSICO", basico), ("PRO", pro)]:

    # Convertir la fecha de captura a formato de fecha
    df["fecha_captura"] = pd.to_datetime(
        df["fecha_captura"], errors="coerce"
    )

    # Detener el proceso si existen fechas que no se pudieron interpretar
    if df["fecha_captura"].isna().any():
        raise ValueError(
            f"{nombre}: existen fechas inválidas."
        )

    # Registrar la cantidad de observaciones antes del filtrado
    antes = len(df)

    # Conservar únicamente las observaciones dentro del ciclo agrícola
    df = df.loc[
        df["fecha_captura"].between(
            DATA_START, DATA_CUTOFF, inclusive="both"
        )
    ].copy()

    # Informar cuántas observaciones permanecen en el periodo solicitado
    print(
        f"{nombre}: {len(df):,} observaciones "
        f"de {antes:,} dentro del ciclo."
    )

    # Actualizar el conjunto correspondiente con los registros filtrados
    if nombre == "BÁSICO":
        basico = df
    else:
        pro = df

    # Detener el proceso si el conjunto no contiene observaciones del ciclo
    if df.empty:
        raise ValueError(
            f"{nombre}: no hay datos en el ciclo 2025."
        )


# Definir las columnas necesarias para calcular las características fenológicas
columnas_requeridas = [
    "parcel_id",
    "fecha_captura",
    "sensor",
    "ndvi_promedio",
]

# Comprobar que ambos conjuntos contengan todas las columnas requeridas
for nombre, df in [
    ("BÁSICO", basico),
    ("PRO", pro),
]:

    # Obtener la lista de columnas que no están presentes en el conjunto
    faltantes = [
        col
        for col in columnas_requeridas
        if col not in df.columns
    ]

    # Detener el proceso si falta alguna columna obligatoria
    if faltantes:

        raise ValueError(
            f"{nombre}: faltan columnas "
            f"{faltantes}"
        )


# Calcular las características fenológicas para cada sensor disponible
# Sentinel-2 y Landsat se procesan con el conjunto BÁSICO
sentinel_features = procesar_sensor(
    basico,
    "Sentinel-2"
)

landsat_features = procesar_sensor(
    basico,
    "Landsat"
)

# Planet se procesa con el conjunto PRO
planet_features = procesar_sensor(
    pro,
    "Planet"
)


# Agregar prefijos para distinguir las características de cada sensor
sentinel_features = agregar_prefijo(
    sentinel_features,
    "sentinel2"
)

landsat_features = agregar_prefijo(
    landsat_features,
    "landsat"
)

planet_features = agregar_prefijo(
    planet_features,
    "planet"
)


# Crear una lista con los resultados que sí contienen características
# y excluir los sensores cuyo procesamiento devolvió None
resultados = [
    resultado
    for resultado in [
        sentinel_features,
        landsat_features,
        planet_features,
    ]
    if resultado is not None
]


# Detener el proceso si ningún sensor generó características fenológicas
if not resultados:

    raise ValueError(
        "No se generaron features fenológicas."
    )


# Combinar las características fenológicas generadas por los sensores
print("\nCombinando features fenológicas...")

# Copiar los resultados del primer sensor disponible como tabla inicial
features = resultados[0].copy()

# Incorporar las características de los demás sensores por parcel_id
# mediante una unión externa para conservar todas las parcelas
for resultado in resultados[1:]:

    features = features.merge(
        resultado,
        on="parcel_id",
        how="outer"
    )

# Ordenar las parcelas por identificador y reiniciar el índice
features = (
    features
    .sort_values("parcel_id")
    .reset_index(drop=True)
)


# Mostrar las dimensiones y validar los identificadores del resultado
print("\nValidación P1.8")

print(
    f"Parcelas únicas: "
    f"{features['parcel_id'].nunique()}"
)

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


# Comparar los identificadores generados con el maestro de parcelas
parcel_master = pd.read_csv(
    os.path.join(
        BASE_DIR,
        "parcel_master.csv"
    ),
    usecols=["parcel_id"]
)

# Convertir los identificadores en conjuntos para compararlos
ids_master = set(
    parcel_master["parcel_id"]
)

ids_features = set(
    features["parcel_id"]
)

# Identificar las parcelas del maestro que no aparecen en P1.8
faltantes = (
    ids_master - ids_features
)

# Identificar las parcelas generadas que no están en el maestro
extras = (
    ids_features - ids_master
)

# Mostrar los resultados de la comparación de identificadores
print(
    f"\nParcelas en parcel_master: "
    f"{len(ids_master)}"
)

print(
    f"Parcelas en P1.8:          "
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

# Mostrar los identificadores faltantes, si existen
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


# Contabilizar los valores nulos presentes en la tabla final
total_nulos = (
    features
    .isna()
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

    # Contar los valores nulos por columna y ordenar de mayor a menor
    nulos = (
        features
        .isna()
        .sum()
        .sort_values(
            ascending=False
        )
    )

    # Mostrar únicamente las columnas que tienen valores nulos
    print(
        nulos[
            nulos > 0
        ].to_string()
    )


# Guardar las características fenológicas en un archivo CSV
features.to_csv(
    OUTPUT_FILE,
    index=False
)


# Mostrar el resumen final de la tarea
print("\nP1.8 COMPLETADO")

# Indicar la ruta del archivo generado
print(
    f"\nArchivo generado:"
    f"\n{OUTPUT_FILE}"
)

# Mostrar las dimensiones finales del conjunto de características
print(
    f"\nDimensiones:"
    f" {features.shape[0]:,} filas × "
    f"{features.shape[1]:,} columnas"
)
print("\nColumnas generadas:")

print(
    features.columns.tolist()
)