"""
Tarea: P1.4 — Separar datasets por sensor
Proyecto: Cebada360
"""

import pandas as pd
from pathlib import Path


def separar_datasets_por_sensor():
    """
    Funcion para separar los datasets normalizados basicos y pro en archivos 
    independientes segun el sensor satelital correspondiente (Sentinel-2, Landsat y Planet).
    """

    # Definicion de rutas de carpetas y archivos de entrada y salida
    carpeta_datos = Path("DATASET_RETO_AGRO_2026_LIMPIO")
    carpeta_salida = carpeta_datos / "sensores"

    archivo_basico = carpeta_datos / "basico_temporal_normalizado.csv"
    archivo_pro = carpeta_datos / "pro_temporal_normalizado.csv"

    # Creacion automatica de la carpeta de salida si no existe
    carpeta_salida.mkdir(parents=True, exist_ok=True)

    # Validacion previa de la existencia de los archivos limpios base
    if not archivo_basico.exists():
        raise FileNotFoundError(
            f"No se encontró el dataset básico:\n{archivo_basico}"
        )

    if not archivo_pro.exists():
        raise FileNotFoundError(
            f"No se encontró el dataset PRO:\n{archivo_pro}"
        )

    print("\n[1/5] Cargando datasets...")

    # Carga de los archivos CSV normalizados en DataFrames de pandas
    df_basico = pd.read_csv(archivo_basico)
    df_pro = pd.read_csv(archivo_pro)

    print(f"Dataset básico: {len(df_basico):,} registros")
    print(f"Dataset PRO:    {len(df_pro):,} registros")

    print("\n[2/5] Verificando columna 'sensor'...")

    # Validacion de que la columna sensor se encuentre en ambos datasets
    for nombre, df in [
        ("básico", df_basico),
        ("PRO", df_pro)
    ]:
        if "sensor" not in df.columns:
            raise ValueError(
                f"El dataset {nombre} no contiene la columna 'sensor'."
            )

    # Normalizacion de los valores de la columna sensor (texto, minusculas y sin espacios)
    df_basico["sensor"] = (
        df_basico["sensor"]
        .astype(str)
        .str.strip()
        .str.lower()
    )

    df_pro["sensor"] = (
        df_pro["sensor"]
        .astype(str)
        .str.strip()
        .str.lower()
    )

    print("\n[3/5] Sensores encontrados:")

    print("\nDataset BÁSICO:")
    print(df_basico["sensor"].value_counts())

    print("\nDataset PRO:")
    print(df_pro["sensor"].value_counts())

    print("\n[4/5] Separando datasets...")

    # Filtrado y separacion de registros para el conjunto basico segun el sensor correspondiente
    df_sentinel2 = df_basico[
        df_basico["sensor"] == "sentinel-2"
    ].copy()

    df_landsat = df_basico[
        df_basico["sensor"] == "landsat"
    ].copy()

    # Filtrado para el conjunto pro
    df_planet = df_pro[
        df_pro["sensor"] == "planet"
    ].copy()

    print("\n[5/5] Generando archivos...")

    # Definicion de las rutas de salida para cada archivo independiente por sensor
    archivo_sentinel2 = (
        carpeta_salida / "sentinel2_timeseries.csv"
    )

    archivo_landsat = (
        carpeta_salida / "landsat_timeseries.csv"
    )

    archivo_planet = (
        carpeta_salida / "planet_timeseries.csv"
    )

    # Exportacion de los DataFrames separados a archivos CSV independientes
    df_sentinel2.to_csv(
        archivo_sentinel2,
        index=False
    )

    df_landsat.to_csv(
        archivo_landsat,
        index=False
    )

    df_planet.to_csv(
        archivo_planet,
        index=False
    )

    print("RESULTADO P1.4")

    print(
        f"\nSentinel-2 : {len(df_sentinel2):,} registros"
    )

    print(
        f"Landsat    : {len(df_landsat):,} registros"
    )

    print(
        f"Planet     : {len(df_planet):,} registros"
    )

    print("\nArchivos generados:")

    print(f"  {archivo_sentinel2}")
    print(f"  {archivo_landsat}")
    print(f"  {archivo_planet}")

    print("VALIDACIONES")

    # Validacion del conjunto basico (la suma de registros separados debe coincidir con el total original)
    total_basico_separado = (
        len(df_sentinel2) +
        len(df_landsat)
    )

    if total_basico_separado == len(df_basico):
        print("Dataset básico: todos los registros separados correctamente.")
    else:
        diferencia = len(df_basico) - total_basico_separado

        print(
            f"Dataset básico: {diferencia:,} "
            "registros no fueron clasificados."
        )

    # Validacion del conjunto PRO
    if len(df_planet) == len(df_pro):
        print("Dataset PRO: todos los registros son Planet.")
    else:
        diferencia = len(df_pro) - len(df_planet)

        print(
            f"Dataset PRO: {diferencia:,} "
            "registros no fueron clasificados como Planet."
        )

if __name__ == "__main__":
    separar_datasets_por_sensor()