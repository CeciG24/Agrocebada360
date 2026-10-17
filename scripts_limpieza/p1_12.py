"""
Tarea: P1.12 — Generar features por cada corte temporal
Proyecto: Cebada360

Descripción:
Genera características satelitales, climáticas y topográficas
para cada corte temporal de predicción temprana del ciclo agrícola
2025. Integra las variables en un dataset maestro independiente
para cada mes de corte.
"""

import pandas as pd
import numpy as np
from pathlib import Path


# Directorio que contiene los archivos procesados del proyecto
BASE_DIR = Path("DATASET_RETO_AGRO_2026_LIMPIO")

# Directorio donde se encuentran los datasets de predicción temprana
PRED_DIR = BASE_DIR / "prediccion_temprana"

# Archivos maestros con la información general de las parcelas
PARCEL_MASTER_PATH = BASE_DIR / "parcel_master.csv"
TOPOGRAPHY_PATH = BASE_DIR / "topography_master.csv"

# Directorio de salida para guardar las características de cada corte
OUTPUT_DIR = BASE_DIR / "prediccion_temprana" / "features"

# Crear el directorio de salida si todavía no existe
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


# Meses para los que se generarán datasets de predicción temprana
CORTES = [
    "junio",
    "julio",
    "agosto",
    "septiembre",
    "octubre",
]


# Índices satelitales que se utilizarán para calcular las características
INDICES = [
    "ndvi",
    "evi",
    "savi",
]


def generar_features_satelitales(df):
    """
    Calcula estadísticas de los índices satelitales para cada parcela.

    Agrupa las observaciones por identificador de parcela y calcula
    la media, mediana, máximo, mínimo, desviación estándar y rango
    de los índices disponibles.

    Parámetros:
        df: DataFrame con observaciones satelitales y sus identificadores.

    Retorna:
        DataFrame con una fila por parcela y sus características satelitales.
    """

    # Lista donde se almacenarán las características calculadas
    features = []

    # Procesar por separado las observaciones de cada parcela
    for parcel_id, grupo in df.groupby("parcel_id"):

        # Inicializar el registro con el identificador de la parcela
        fila = {
            "parcel_id": parcel_id
        }

        # Calcular estadísticas para cada índice satelital configurado
        for indice in INDICES:

            # Nombre de la columna que contiene el valor promedio del índice
            columna = f"{indice}_promedio"

            # Omitir el índice si no existe en el archivo de entrada
            if columna not in grupo.columns:
                continue

            # Convertir los valores a formato numérico y excluir
            # aquellos que sean nulos o no puedan convertirse.
            valores = pd.to_numeric(
                grupo[columna],
                errors="coerce"
            ).dropna()

            # Si no hay observaciones válidas, asignar NaN a todas
            # las estadísticas del índice correspondiente.
            if len(valores) == 0:

                fila[f"satelite_{indice}_mean"] = np.nan
                fila[f"satelite_{indice}_median"] = np.nan
                fila[f"satelite_{indice}_max"] = np.nan
                fila[f"satelite_{indice}_min"] = np.nan
                fila[f"satelite_{indice}_std"] = np.nan
                fila[f"satelite_{indice}_range"] = np.nan

            else:

                # Calcular la media aritmética de las observaciones
                fila[f"satelite_{indice}_mean"] = valores.mean()

                # Calcular el valor central de las observaciones
                fila[f"satelite_{indice}_median"] = valores.median()

                # Obtener el valor máximo registrado
                fila[f"satelite_{indice}_max"] = valores.max()

                # Obtener el valor mínimo registrado
                fila[f"satelite_{indice}_min"] = valores.min()

                # Medir la dispersión de los valores mediante
                # la desviación estándar muestral.
                fila[f"satelite_{indice}_std"] = valores.std()

                # Calcular la diferencia entre el máximo y el mínimo
                fila[f"satelite_{indice}_range"] = (
                    valores.max() - valores.min()
                )

        # Agregar las características de la parcela a la lista final
        features.append(fila)

    # Convertir los registros calculados en un DataFrame
    return pd.DataFrame(features)


def generar_features_climaticas(df):
    """
    Calcula características climáticas para cada parcela.

    Obtiene estadísticas de precipitación, temperatura mínima,
    temperatura máxima y amplitud térmica a partir de los registros
    climáticos disponibles.

    Parámetros:
        df: DataFrame con registros climáticos por parcela y fecha.

    Retorna:
        DataFrame con una fila por parcela y sus características climáticas.
    """

    # Lista donde se almacenarán las características climáticas
    features = []

    # Procesar los registros de cada parcela de forma independiente
    for parcel_id, grupo in df.groupby("parcel_id"):

        # Convertir la precipitación a valores numéricos.
        # Los valores no válidos se convierten en NaN.
        precip = pd.to_numeric(
            grupo["precip_mm"],
            errors="coerce"
        )

        # Convertir la temperatura mínima a valores numéricos
        tmin = pd.to_numeric(
            grupo["tmin_c"],
            errors="coerce"
        )

        # Convertir la temperatura máxima a valores numéricos
        tmax = pd.to_numeric(
            grupo["tmax_c"],
            errors="coerce"
        )

        # Calcular la amplitud térmica de cada registro como
        # la diferencia entre la temperatura máxima y la mínima.
        amplitud = tmax - tmin

        # Construir el registro de características climáticas
        # correspondiente a la parcela actual.
        fila = {
            "parcel_id": parcel_id,

            # Sumar la precipitación de los registros disponibles
            "climate_precip_accumulated_mm":
                precip.sum(),

            # Calcular la precipitación media por registro
            "climate_precip_mean_mm":
                precip.mean(),

            # Obtener la temperatura mínima media
            "climate_tmin_mean_c":
                tmin.mean(),

            # Obtener la temperatura máxima media
            "climate_tmax_mean_c":
                tmax.mean(),

            # Calcular la amplitud térmica media
            "climate_amplitud_termica_mean_c":
                amplitud.mean(),

            # Calcular la desviación estándar de la amplitud térmica
            "climate_amplitud_termica_std_c":
                amplitud.std(),
        }

        # Agregar las características calculadas a la lista
        features.append(fila)

    # Devolver un DataFrame con las características de todas las parcelas
    return pd.DataFrame(features)


def main():
    """
    Ejecuta el proceso completo de generación de características.

    Carga los archivos maestros, procesa cada corte temporal,
    calcula las características satelitales y climáticas,
    integra la información topográfica, valida los resultados
    y guarda un archivo independiente por cada corte.
    """

    print("P1.12 — Generación de features por corte temporal")

    # 1. Cargar datos maestros

    # Leer el archivo que contiene el identificador y la información
    # general de las parcelas.
    print("\nCargando datasets maestros...")

    parcel_master = pd.read_csv(
        PARCEL_MASTER_PATH
    )

    # Leer las características topográficas de las parcelas
    topography = pd.read_csv(
        TOPOGRAPHY_PATH
    )

    # Convertir parcel_id a texto para mantener un tipo de dato
    # consistente durante las comparaciones y las combinaciones.
    parcel_master["parcel_id"] = (
        parcel_master["parcel_id"].astype(str)
    )

    topography["parcel_id"] = (
        topography["parcel_id"].astype(str)
    )

    # 2. Validar archivos maestros

    # Verificar que cada parcela aparezca una sola vez en el
    # archivo maestro y en el archivo de topografía.
    if parcel_master["parcel_id"].duplicated().any():
        raise ValueError(
            "parcel_master contiene IDs duplicados."
        )

    if topography["parcel_id"].duplicated().any():
        raise ValueError(
            "topography_master contiene IDs duplicados."
        )

    # Crear el conjunto de identificadores que se utilizará
    # como referencia para validar todos los cortes.
    ids_master = set(
        parcel_master["parcel_id"]
    )

    print(
        f"Parcelas esperadas: {len(ids_master)}"
    )

    # 3. Procesar cada corte temporal

    # Ejecutar el mismo procedimiento para cada mes configurado.
    for corte in CORTES:

        print(
            f"\nProcesando corte: abril-{corte.upper()}"
        )

        # Construir las rutas de los archivos satelital y climático
        # correspondientes al corte actual.
        sat_path = (
            PRED_DIR
            / f"sentinel2_corte_{corte}.csv"
        )

        clima_path = (
            PRED_DIR
            / f"climate_corte_{corte}.csv"
        )

        # 4. Verificar que existan los archivos de entrada

        # Detener el proceso si falta alguno de los archivos
        # necesarios para generar las características.
        if not sat_path.exists():
            raise FileNotFoundError(
                f"No existe: {sat_path}"
            )

        if not clima_path.exists():
            raise FileNotFoundError(
                f"No existe: {clima_path}"
            )

        # 5. Cargar los datos del corte

        # Leer las observaciones satelitales y climáticas
        # correspondientes al mes que se está procesando.
        df_sat = pd.read_csv(
            sat_path
        )

        df_clima = pd.read_csv(
            clima_path
        )

        # 6. Validar la ventana temporal del corte

        # Relacionar cada mes de corte con su número para construir
        # los límites temporales del ciclo agrícola 2025.
        MESES_CORTE = {
            "junio": 6,
            "julio": 7,
            "agosto": 8,
            "septiembre": 9,
            "octubre": 10,
        }

        mes_corte = MESES_CORTE[corte]

        # Definir el inicio del ciclo agrícola que se analizará
        inicio_ciclo = pd.Timestamp("2025-04-01")

        # Establecer el primer día del mes correspondiente al corte
        inicio_mes_corte = pd.Timestamp(
            year=2025,
            month=mes_corte,
            day=1
        )

        # Calcular el último día del mes de corte para los datos
        # satelitales. Este límite se incluye en la validación.
        fin_satelital = (
            inicio_mes_corte + pd.offsets.MonthEnd(0)
        )

        # Validar las fechas de ambos archivos antes de calcular
        # las características temporales.
        for nombre, df, columna in [
            ("satélite", df_sat, "fecha_captura"),
            ("clima", df_clima, "fecha_captura"),
        ]:
            # Comprobar que exista la columna de fecha requerida
            if columna not in df.columns:
                raise ValueError(
                    f"El archivo de {nombre} del corte {corte} "
                    f"no contiene la columna {columna}."
                )

            # Convertir las fechas al formato datetime.
            # Los valores inválidos se convierten en NaT.
            df[columna] = pd.to_datetime(
                df[columna],
                errors="coerce"
            )

            # Detener el proceso si hay fechas que no pudieron
            # convertirse correctamente.
            if df[columna].isna().any():
                raise ValueError(
                    f"Hay fechas inválidas en los datos de "
                    f"{nombre}, corte {corte}."
                )

            # Comprobar que las fechas pertenezcan al año 2025
            # y estén dentro del ciclo agrícola permitido.
            if (
                (df[columna] < inicio_ciclo)
                | (df[columna] > fin_satelital)
                | (df[columna].dt.year != 2025)
            ).any():
                raise ValueError(
                    f"Hay fechas fuera del ciclo permitido "
                    f"en {nombre}, corte {corte}."
                )

        # Los registros climáticos deben corresponder a meses
        # completos anteriores al mes de corte. Por eso, no se
        # permiten fechas desde el primer día de ese mes.
        if (
            (df_clima["fecha_captura"] >= inicio_mes_corte)
        ).any():
            raise ValueError(
                f"El clima del corte {corte} contiene datos "
                f"del mes de corte o posteriores."
            )

        # Informar que las fechas pasaron las validaciones
        print(
            f"[OK] Ventana temporal validada para {corte}: "
            f"satélite hasta {fin_satelital.date()}, "
            f"clima hasta el mes anterior."
        )

        # 7. Normalizar identificadores de parcela

        # En los datos satelitales, ID_POLIGONO contiene el
        # identificador que se utilizará como parcel_id.
        # En los datos climáticos, parcel_id ya existe.
        # Convertir ambos a texto para facilitar su integración.
        df_sat["parcel_id"] = (
            df_sat["ID_POLIGONO"].astype(str)
        )

        df_clima["parcel_id"] = (
            df_clima["parcel_id"].astype(str)
        )

        # 8. Generar características satelitales

        # Agrupar las observaciones satelitales por parcela
        # y calcular las estadísticas de los índices disponibles.
        sat_features = generar_features_satelitales(
            df_sat
        )

        # 9. Generar características climáticas

        # Calcular las estadísticas de precipitación,
        # temperatura y amplitud térmica para cada parcela.
        climate_features = generar_features_climaticas(
            df_clima
        )

        # 10. Construir la matriz base de características

        # Partir de parcel_master para conservar todas las
        # parcelas y su información general.
        features = parcel_master.copy()

        # Seleccionar únicamente las variables topográficas
        # que se incorporarán al dataset final.
        topo_features = topography[
            [
                "parcel_id",
                "elevation_mean",
                "slope_mean",
            ]
        ].copy()

        # Integrar las características topográficas.
        # validate="one_to_one" comprueba que la combinación
        # mantenga una relación de un registro por parcela.
        features = features.merge(
            topo_features,
            on="parcel_id",
            how="left",
            validate="one_to_one"
        )

        # Incorporar las características satelitales calculadas
        features = features.merge(
            sat_features,
            on="parcel_id",
            how="left",
            validate="one_to_one"
        )

        # Incorporar las características climáticas calculadas
        features = features.merge(
            climate_features,
            on="parcel_id",
            how="left",
            validate="one_to_one"
        )

        # 11. Validar el resultado integrado

        # Comparar las parcelas del resultado con el conjunto
        # de identificadores del archivo maestro.
        ids_resultado = set(
            features["parcel_id"]
        )

        # Identificar parcelas que no aparecen en el resultado
        faltantes = ids_master - ids_resultado

        # Identificar parcelas adicionales que no están en la referencia
        extras = ids_resultado - ids_master

        # Contar los identificadores repetidos después de las combinaciones
        duplicados = (
            features["parcel_id"]
            .duplicated()
            .sum()
        )

        # Contar todos los valores nulos del DataFrame.
        # Esta comprobación es informativa y no elimina los faltantes.
        nan_total = (
            features.isna()
            .sum()
            .sum()
        )

        # Mostrar las dimensiones y el estado general del resultado
        print(
            f"Filas:              {len(features)}"
        )

        print(
            f"Columnas:           {len(features.columns)}"
        )

        print(
            f"Parcelas únicas:    "
            f"{features['parcel_id'].nunique()}"
        )

        print(
            f"IDs duplicados:     {duplicados}"
        )

        print(
            f"NaN totales:        {nan_total}"
        )

        print(
            f"Parcelas faltantes: {len(faltantes)}"
        )

        print(
            f"Parcelas adicionales: {len(extras)}"
        )
        
        # Comprobar que el resultado tenga el mismo número
        # de filas que el archivo maestro de parcelas.
        if len(features) != len(parcel_master):
            raise ValueError(
                f"El corte {corte} no tiene "
                f"{len(parcel_master)} parcelas."
            )

        # No permitir registros duplicados por parcela
        if duplicados != 0:
            raise ValueError(
                f"Existen IDs duplicados en {corte}."
            )

        # Detener el proceso si faltan parcelas de referencia
        if faltantes:
            raise ValueError(
                f"Faltan parcelas en {corte}: "
                f"{sorted(faltantes)}"
            )

        # Detener el proceso si aparecen parcelas que no
        # pertenecen al archivo maestro original.
        if extras:
            raise ValueError(
                f"Existen parcelas adicionales en {corte}: "
                f"{sorted(extras)}"
            )

        # Construir el nombre del archivo de salida e incluir
        # el mes para identificar el corte temporal.
        output_path = (
            OUTPUT_DIR
            / f"features_master_corte_{corte}.csv"
        )

        # Guardar las características sin el índice de pandas
        features.to_csv(
            output_path,
            index=False
        )

        print(
            f"Guardado: {output_path}"
        )

    # Informar que el proceso terminó y enumerar los archivos
    # que se generaron para cada corte temporal.
    print("\nP1.12 completada")
    print("\nFeatures generadas:")

    for corte in CORTES:
        print(
            f"features_master_corte_{corte}.csv"
        )

if __name__ == "__main__":
    main()