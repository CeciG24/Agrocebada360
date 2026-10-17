"""
Tarea: P1.10 — Construcción de FEATURES_MASTER
Proyecto: Cebada360
"""

import pandas as pd
from pathlib import Path


# Directorio donde se encuentran los archivos procesados
BASE_DIR = Path("DATASET_RETO_AGRO_2026_LIMPIO")

# Archivos de entrada con las características de cada parcela
PARCEL_MASTER = BASE_DIR / "parcel_master.csv"
SATELLITE = BASE_DIR / "satellite_features.csv"
FENOLOGIA = BASE_DIR / "fenologia_features.csv"
CLIMATE = BASE_DIR / "climate_features.csv"
TOPOGRAPHY = BASE_DIR / "topography_master.csv"

# Archivo de salida que contendrá todas las características integradas
OUTPUT = BASE_DIR / "features_master.csv"


print("P1.10 — Construcción de FEATURES_MASTER")

# Se leen los archivos CSV y se convierte parcel_id a texto para
# mantener el mismo tipo de dato en todos los datasets y evitar
# inconsistencias al comparar o combinar los identificadores.

parcel = pd.read_csv(PARCEL_MASTER, dtype={"parcel_id": str})
satellite = pd.read_csv(SATELLITE, dtype={"parcel_id": str})
fenologia = pd.read_csv(FENOLOGIA, dtype={"parcel_id": str})
climate = pd.read_csv(CLIMATE, dtype={"parcel_id": str})
topography = pd.read_csv(TOPOGRAPHY, dtype={"parcel_id": str})


# Mostrar la cantidad de registros cargados desde cada archivo
print("\nArchivos cargados:")
print(f"  parcel_master:        {len(parcel):,} filas")
print(f"  satellite_features:   {len(satellite):,} filas")
print(f"  fenologia_features:   {len(fenologia):,} filas")
print(f"  climate_features:     {len(climate):,} filas")
print(f"  topography_master:    {len(topography):,} filas")



# Se agrupan los DataFrames en un diccionario para ejecutar las mismas
# validaciones sobre cada archivo sin repetir el código.

datasets = {
    "parcel_master": parcel,
    "satellite_features": satellite,
    "fenologia_features": fenologia,
    "climate_features": climate,
    "topography_master": topography,
}

for nombre, df in datasets.items():

    # Verificar que el archivo contenga la columna identificadora
    if "parcel_id" not in df.columns:
        raise ValueError(
            f"{nombre} no contiene la columna parcel_id."
        )

    # Contar los identificadores repetidos para garantizar que
    # exista un solo registro por parcela en cada dataset.
    duplicados = df["parcel_id"].duplicated().sum()

    if duplicados > 0:
        raise ValueError(
            f"{nombre} contiene {duplicados} IDs duplicados."
        )

    # Mostrar la cantidad de identificadores diferentes
    print(
        f"  {nombre}: "
        f"{df['parcel_id'].nunique()} IDs únicos"
    )


# Se toma parcel_master como referencia para comprobar que los demás
# archivos contengan exactamente los mismos identificadores.
ids_base = set(parcel["parcel_id"])

for nombre, df in datasets.items():

    # Obtener los identificadores presentes en el archivo actual
    ids_actuales = set(df["parcel_id"])

    # Identificar parcelas de referencia que no aparecen en el archivo
    faltantes = ids_base - ids_actuales

    # Identificar parcelas que no existen en el archivo de referencia
    extras = ids_actuales - ids_base

    # Detener el proceso si faltan parcelas
    if faltantes:
        raise ValueError(
            f"{nombre}: faltan {len(faltantes)} parcelas: "
            f"{sorted(faltantes)}"
        )

    # Detener el proceso si existen parcelas adicionales
    if extras:
        raise ValueError(
            f"{nombre}: existen {len(extras)} parcelas "
            f"que no están en parcel_master: "
            f"{sorted(extras)}"
        )


print("\nTodos los datasets contienen exactamente las mismas parcelas.")

# topography_master también contiene información general de las
# parcelas que ya está disponible en parcel_master.
# Se seleccionan únicamente las variables topográficas necesarias
# para evitar incorporar columnas redundantes durante la integración.

topography_features = topography[
    [
        "parcel_id",
        "elevation_mean",
        "slope_mean",
    ]
].copy()

# Se utiliza parcel_master como base del archivo final.
# Cada dataset se combina mediante parcel_id para asociar las
# características correspondientes a cada parcela.
# how="left" conserva todas las parcelas de la tabla principal.
# validate="one_to_one" comprueba que la relación sea uno a uno.

master = parcel.copy()

master = master.merge(
    satellite,
    on="parcel_id",
    how="left",
    validate="one_to_one"
)

master = master.merge(
    fenologia,
    on="parcel_id",
    how="left",
    validate="one_to_one"
)

master = master.merge(
    climate,
    on="parcel_id",
    how="left",
    validate="one_to_one"
)

master = master.merge(
    topography_features,
    on="parcel_id",
    how="left",
    validate="one_to_one"
)


# Ordenar los registros por identificador facilita la revisión
# del archivo y mantiene un orden consistente entre ejecuciones.
# reset_index elimina el índice anterior y crea uno nuevo.

master = master.sort_values(
    "parcel_id"
).reset_index(drop=True)

# Mostrar las dimensiones del archivo integrado y comprobar
# la cantidad de parcelas y la existencia de IDs duplicados.

print("\nValidación final")

print(f"Filas: {len(master):,}")
print(f"Columnas: {len(master.columns):,}")
print(f"Parcelas únicas: {master['parcel_id'].nunique():,}")

duplicados = master["parcel_id"].duplicated().sum()

print(f"IDs duplicados: {duplicados}")

# Calcular el número total de valores nulos en el archivo.
# Si existen, mostrar cuántos faltan en cada columna, ordenando
# los resultados desde la columna con más faltantes hasta la menor.

nan_total = master.isna().sum().sum()

print(f"NaN totales: {nan_total}")


if nan_total > 0:

    print("\nColumnas con valores faltantes:")

    nan_columns = (
        master.isna()
        .sum()
        .loc[lambda x: x > 0]
        .sort_values(ascending=False)
    )

    print(nan_columns)

else:

    print("No existen valores faltantes.")


# Comprobar que el archivo no contenga nombres de columnas repetidos.
# Si se encuentran duplicados, mostrar sus nombres para revisarlos.

duplicated_columns = master.columns[
    master.columns.duplicated()
].tolist()

print(
    f"Columnas duplicadas: "
    f"{len(duplicated_columns)}"
)

if duplicated_columns:
    print(duplicated_columns)


# Comparar nuevamente los identificadores del resultado final
# con los del archivo maestro original para comprobar que la
# integración haya conservado el conjunto de parcelas.

ids_finales = set(master["parcel_id"])

faltantes_finales = ids_base - ids_finales
extras_finales = ids_finales - ids_base

print(
    f"Parcelas faltantes respecto a parcel_master: "
    f"{len(faltantes_finales)}"
)

print(
    f"Parcelas adicionales respecto a parcel_master: "
    f"{len(extras_finales)}"
)

# Exportar el DataFrame integrado a CSV sin incluir el índice
# numérico de pandas como una columna adicional.

master.to_csv(
    OUTPUT,
    index=False
)

print("\nArchivo generado:")
print(OUTPUT)

# Imprimir los primeros 30 nombres de columnas para revisar
# las variables que forman parte del conjunto de características.

print("\nPrimeras columnas:")

for i, columna in enumerate(master.columns[:30], start=1):
    print(f"{i:3}. {columna}")

# Indicar cuántas columnas adicionales existen, si las hay
if len(master.columns) > 30:
    print(
        f"\n... y {len(master.columns) - 30} columnas más."
    )


# Mostrar una muestra de cinco registros para revisar
# visualmente la estructura y el contenido del archivo generado.

print("\nPrimeras 5 filas:")
print(
    master.head().to_string(index=False)
)

print("\nP1.10 completado")