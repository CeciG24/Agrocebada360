"""
Tarea: P1.5 — Preparar clima por parcela
Proyecto: Cebada360
"""

from pathlib import Path

import numpy as np
import pandas as pd
import rasterio

# Definicion de rutas base para los directorios de datos y archivos de salida
BASE_DIR = Path("DATASET_RETO_AGRO_2026")
LIMPIO_DIR = BASE_DIR.parent / "DATASET_RETO_AGRO_2026_LIMPIO"

# Definicion de la ruta al archivo maestro que contiene los IDs y centroides de las parcelas
PARCEL_MASTER = LIMPIO_DIR / "parcel_master.csv"

# Rutas especificas para los datos de precipitacion CHIRPS
PREC_BASE_DIR = (
    BASE_DIR
    / "Reto_AgroCebada_CHIRPS_Precipitacion_2022_2025"
)
PREC_DIR = PREC_BASE_DIR / "Precipitacion_mensual"
PREC_INVENTARIO = (
    PREC_BASE_DIR
    / "inventario_CHIRPS_precipitacion_mensual_2022_2025.csv"
)

# Rutas especificas para los datos de temperatura
TEMP_BASE_DIR = (
    BASE_DIR
    / "Reto_AgroCebada_Temperatura_2022_2025"
)
TEMP_DIR = TEMP_BASE_DIR
TEMP_INVENTARIO = (
    TEMP_BASE_DIR
    / "inventario_temperatura_2022_2025.csv"
)

# Rutas de salida para las series de tiempo climaticas y los agregados por parcela
OUTPUT_TIMESERIES = (
    LIMPIO_DIR / "climate_timeseries.csv"
)
OUTPUT_AGGREGATES = (
    LIMPIO_DIR / "climate_aggregates.csv"
)

# Definicion del periodo de estudio, desde enero de 2022 hasta diciembre de 2025
YEARS = range(2022, 2026)
MONTHS = range(1, 13)

# Parametros espaciales esperados para validar los archivos raster climaticos
EXPECTED_CRS = "EPSG:4326"
EXPECTED_WIDTH = 65
EXPECTED_HEIGHT = 72
EXPECTED_RESOLUTION = 0.05
TEMPERATURE_NODATA = -9999


def obtener_archivo_precipitacion(year, month):
    """
    Devuelve la ruta del archivo GeoTIFF de precipitacion correspondiente
    al anio y mes especificados.
    """
    # Construccion de la ruta del archivo de precipitacion para el periodo indicado
    return (
        PREC_DIR
        / str(year)
        / f"PREC_{year}_{month:02d}.tif"
    )


def obtener_archivo_tmin(year, month):
    """
    Devuelve la ruta del archivo GeoTIFF de temperatura minima correspondiente
    al anio y mes especificados.
    """
    # Construccion de la ruta del archivo de temperatura minima para el periodo indicado
    return (
        TEMP_DIR
        / "Tmin"
        / str(year)
        / f"Tmin_{year}_{month:02d}.tif"
    )


def obtener_archivo_tmax(year, month):
    """
    Devuelve la ruta del archivo GeoTIFF de temperatura maxima correspondiente
    al anio y mes especificados.
    """
    # Construccion de la ruta del archivo de temperatura maxima para el periodo indicado
    return (
        TEMP_DIR
        / "Tmax"
        / str(year)
        / f"Tmax_{year}_{month:02d}.tif"
    )


def validar_inventarios():
    """
    Valida la existencia, estructura y contenido de los inventarios 
    CSV de precipitacion y temperatura.
    """
    print("\nVALIDANDO INVENTARIOS CLIMÁTICOS")

    # Comprobacion de la existencia del inventario de precipitacion
    if not PREC_INVENTARIO.exists():
        raise FileNotFoundError(
            f"No existe el inventario de precipitación:\n"
            f"{PREC_INVENTARIO}"
        )

    # Comprobacion de la existencia del inventario de temperatura
    if not TEMP_INVENTARIO.exists():
        raise FileNotFoundError(
            f"No existe el inventario de temperatura:\n"
            f"{TEMP_INVENTARIO}"
        )

    # Carga de los inventarios CSV para revisar su contenido y estructura
    df_prec = pd.read_csv(PREC_INVENTARIO)
    df_temp = pd.read_csv(TEMP_INVENTARIO)

    # Impresion del numero de registros encontrados en cada inventario
    print(
        f"Inventario precipitación: "
        f"{len(df_prec)} registros"
    )
    print(
        f"Inventario temperatura: "
        f"{len(df_temp)} registros"
    )

    # Validacion del numero de registros esperados (48 meses para precipitacion y 96 para temperatura)
    if len(df_prec) != 48:
        raise ValueError(
            "El inventario de precipitación debería "
            f"contener 48 registros, pero contiene "
            f"{len(df_prec)}."
        )

    if len(df_temp) != 96:
        raise ValueError(
            "El inventario de temperatura debería "
            f"contener 96 registros, pero contiene "
            f"{len(df_temp)}."
        )

    # Definicion de las columnas obligatorias para el inventario de precipitacion
    columnas_prec = {
        "anio",
        "mes",
        "archivo"
    }

    # Definicion de las columnas obligatorias para el inventario de temperatura
    columnas_temp = {
        "variable",
        "anio",
        "mes",
        "archivo"
    }

    # Identificacion de las columnas requeridas que no aparecen en cada inventario
    faltantes_prec = (
        columnas_prec
        - set(df_prec.columns)
    )

    faltantes_temp = (
        columnas_temp
        - set(df_temp.columns)
    )

    # Generacion de un error si faltan columnas necesarias en el inventario de precipitacion
    if faltantes_prec:
        raise ValueError(
            "Faltan columnas en el inventario de "
            f"precipitación: {faltantes_prec}"
        )

    # Generacion de un error si faltan columnas necesarias en el inventario de temperatura
    if faltantes_temp:
        raise ValueError(
            "Faltan columnas en el inventario de "
            f"temperatura: {faltantes_temp}"
        )

    # Creacion del conjunto de combinaciones de anio y mes que deben existir entre 2022 y 2025
    meses_esperados = {
        (year, month)
        for year in YEARS
        for month in MONTHS
    }

    # Obtencion de las combinaciones de anio y mes registradas en el inventario de precipitacion
    meses_prec = set(
        zip(
            df_prec["anio"],
            df_prec["mes"]
        )
    )

    # Verificacion de que el inventario de precipitacion contenga todos los meses esperados
    if meses_prec != meses_esperados:
        raise ValueError(
            "El inventario de precipitación no contiene "
            "exactamente los meses 2022-01 a 2025-12."
        )

    # Normalizacion de los nombres de las variables de temperatura para validar Tmin y Tmax
    variables_temp = set(
        df_temp["variable"]
        .astype(str)
        .str.lower()
    )

    # Comprobacion de que el inventario incluya temperatura minima y maxima
    if variables_temp != {"tmin", "tmax"}:
        raise ValueError(
            "El inventario de temperatura debería contener "
            "Tmin y Tmax."
        )

    print(
        "Inventarios climáticos validados correctamente."
    )

    # Devolucion de ambos inventarios para utilizarlos en el procesamiento
    return df_prec, df_temp


def validar_archivos_raster():
    """
    Comprueba la existencia fisica de los archivos GeoTIFF para precipitacion,
    temperatura minima y temperatura maxima.
    """
    print("\nVALIDANDO GEOTIFF CLIMÁTICOS")

    # Inicializacion de listas para almacenar las rutas de los archivos encontrados
    archivos_prec = []
    archivos_tmin = []
    archivos_tmax = []

    # Recorrido de todos los anios y meses del periodo de estudio
    for year in YEARS:
        for month in MONTHS:

            # Obtencion de las rutas de precipitacion y temperaturas del mes actual
            prec = obtener_archivo_precipitacion(
                year,
                month
            )
            tmin = obtener_archivo_tmin(
                year,
                month
            )
            tmax = obtener_archivo_tmax(
                year,
                month
            )

            # Verificacion de la existencia del archivo de precipitacion
            if not prec.exists():
                raise FileNotFoundError(
                    f"Falta precipitación:\n{prec}"
                )

            # Verificacion de la existencia del archivo de temperatura minima
            if not tmin.exists():
                raise FileNotFoundError(
                    f"Falta Tmin:\n{tmin}"
                )

            # Verificacion de la existencia del archivo de temperatura maxima
            if not tmax.exists():
                raise FileNotFoundError(
                    f"Falta Tmax:\n{tmax}"
                )

            # Almacenamiento de las rutas de los archivos validados
            archivos_prec.append(prec)
            archivos_tmin.append(tmin)
            archivos_tmax.append(tmax)

    # Impresion del total de archivos encontrados para cada variable climatica
    print(
        f"Precipitación encontrada: "
        f"{len(archivos_prec)} / 48"
    )
    print(
        f"Tmin encontrada:          "
        f"{len(archivos_tmin)} / 48"
    )
    print(
        f"Tmax encontrada:          "
        f"{len(archivos_tmax)} / 48"
    )

    # Devolucion de las listas de archivos para realizar las validaciones posteriores
    return (
        archivos_prec,
        archivos_tmin,
        archivos_tmax
    )


def validar_raster(ruta, nombre):
    """
    Valida las propiedades espaciales clave de un raster (CRS, dimensiones y resolucion).
    """
    # Apertura del GeoTIFF para consultar sus metadatos espaciales
    with rasterio.open(ruta) as src:
        # Obtencion del sistema de coordenadas, dimensiones y resolucion del raster
        crs = src.crs
        width = src.width
        height = src.height
        res_x = abs(src.transform.a)
        res_y = abs(src.transform.e)

        # Comprobacion de que el raster tenga definido un sistema de referencia de coordenadas
        if crs is None:
            raise ValueError(
                f"{nombre}: el raster no tiene CRS."
            )

        # Validacion del sistema de referencia esperado, correspondiente a WGS84
        if crs.to_string() != EXPECTED_CRS:
            raise ValueError(
                f"{nombre}: CRS incorrecto. "
                f"Esperado {EXPECTED_CRS}, "
                f"encontrado {crs}"
            )

        # Verificacion de las dimensiones esperadas del raster
        if (
            width != EXPECTED_WIDTH
            or height != EXPECTED_HEIGHT
        ):
            raise ValueError(
                f"{nombre}: dimensiones incorrectas. "
                f"Esperado "
                f"{EXPECTED_WIDTH}x{EXPECTED_HEIGHT}, "
                f"encontrado "
                f"{width}x{height}"
            )

        # Validacion de la resolucion horizontal con una tolerancia numerica
        if not np.isclose(
            res_x,
            EXPECTED_RESOLUTION,
            atol=0.0001
        ):
            raise ValueError(
                f"{nombre}: resolución X incorrecta: "
                f"{res_x}"
            )

        # Validacion de la resolucion vertical con una tolerancia numerica
        if not np.isclose(
            res_y,
            EXPECTED_RESOLUTION,
            atol=0.0001
        ):
            raise ValueError(
                f"{nombre}: resolución Y incorrecta: "
                f"{res_y}"
            )


def validar_rasters(
    archivos_prec,
    archivos_tmin,
    archivos_tmax
):
    """
    Ejecuta la validacion de metadatos para todos los rasters climaticos de precipitacion y temperatura.
    """
    print(
        "\nVALIDANDO METADATOS DE LOS RASTERS"
    )

    # Validacion de las propiedades espaciales de todos los archivos de precipitacion
    for ruta in archivos_prec:
        validar_raster(
            ruta,
            ruta.name
        )

    # Validacion espacial y del valor NoData para los archivos de temperatura minima
    for ruta in archivos_tmin:
        validar_raster(
            ruta,
            ruta.name
        )

        # Comprobacion del valor utilizado para representar datos faltantes en el raster
        with rasterio.open(ruta) as src:
            if src.nodata != TEMPERATURE_NODATA:
                raise ValueError(
                    f"{ruta.name}: NoData esperado = "
                    f"{TEMPERATURE_NODATA}, "
                    f"encontrado = {src.nodata}"
                )

    # Validacion espacial y del valor NoData para los archivos de temperatura maxima
    for ruta in archivos_tmax:
        validar_raster(
            ruta,
            ruta.name
        )

        # Comprobacion del valor utilizado para representar datos faltantes en el raster
        with rasterio.open(ruta) as src:
            if src.nodata != TEMPERATURE_NODATA:
                raise ValueError(
                    f"{ruta.name}: NoData esperado = "
                    f"{TEMPERATURE_NODATA}, "
                    f"encontrado = {src.nodata}"
                )

    # Impresion de las caracteristicas espaciales que deben cumplir los archivos
    print("CRS: EPSG:4326")
    print("Dimensiones: 65 x 72")
    print("Resolución: 0.05° x 0.05°")
    print("NoData temperatura: -9999")
    print(
        "Metadatos de los GeoTIFF "
        "validados correctamente."
    )


def cargar_parcelas():
    """
    Carga el archivo parcel_master.csv y valida la existencia de columnas 
    y centroides correctos.
    """
    print("\nCARGANDO PARCEL MASTER")

    # Comprobacion de la existencia del archivo maestro de parcelas
    if not PARCEL_MASTER.exists():
        raise FileNotFoundError(
            f"No existe:\n{PARCEL_MASTER}"
        )

    # Lectura del archivo maestro conservando los identificadores de parcela como texto
    df = pd.read_csv(
        PARCEL_MASTER,
        dtype={"parcel_id": str}
    )

    # Definicion de las columnas necesarias para identificar las parcelas y localizar sus centroides
    columnas_requeridas = {
        "parcel_id",
        "centroid_lat",
        "centroid_lon"
    }

    # Identificacion de las columnas obligatorias que no existen en el archivo
    faltantes = (
        columnas_requeridas
        - set(df.columns)
    )

    # Interrupcion del proceso si faltan columnas requeridas
    if faltantes:
        raise ValueError(
            "Faltan columnas requeridas en "
            f"parcel_master.csv: {faltantes}"
        )

    # Limpieza de espacios en blanco en los identificadores de las parcelas
    df["parcel_id"] = (
        df["parcel_id"]
        .astype(str)
        .str.strip()
    )

    # Conversion de las coordenadas de los centroides a valores numericos
    df["centroid_lat"] = pd.to_numeric(
        df["centroid_lat"],
        errors="coerce"
    )
    df["centroid_lon"] = pd.to_numeric(
        df["centroid_lon"],
        errors="coerce"
    )

    # Identificacion de parcelas que tienen coordenadas faltantes o no numericas
    faltantes_coord = df[
        df["centroid_lat"].isna()
        | df["centroid_lon"].isna()
    ]

    # Generacion de un error si alguna parcela no tiene coordenadas validas
    if len(faltantes_coord) > 0:
        raise ValueError(
            "Existen parcelas sin coordenadas de centroide:\n"
            + faltantes_coord[
                ["parcel_id"]
            ].to_string(index=False)
        )

    # Identificacion de los identificadores de parcela que aparecen mas de una vez
    duplicados = df[
        df["parcel_id"].duplicated(
            keep=False
        )
    ]

    # Generacion de un error si existen identificadores duplicados
    if len(duplicados) > 0:
        raise ValueError(
            "Existen parcel_id duplicados:\n"
            + duplicados[
                ["parcel_id"]
            ].to_string(index=False)
        )

    # Impresion del numero de parcelas cargadas y de las columnas utilizadas
    print(
        f"Parcelas cargadas: {len(df)}"
    )
    print(
        "Columnas utilizadas: "
        "parcel_id, centroid_lat, centroid_lon"
    )

    # Devolucion del DataFrame con las parcelas validadas
    return df


def validar_centroides(df_parcelas, raster_referencia):
    """
    Verifica que las coordenadas de los centroides de las parcelas 
    se encuentren dentro de la extension espacial del raster climatico.
    """
    print(
        "\nVALIDANDO COBERTURA ESPACIAL"
    )

    # Apertura de un raster de referencia para obtener los limites de su cobertura geografica
    with rasterio.open(raster_referencia) as src:
        bounds = src.bounds

        # Identificacion de los centroides que se encuentran fuera de los limites del raster
        puntos_fuera = df_parcelas[
            ~(
                df_parcelas["centroid_lon"].between(
                    bounds.left,
                    bounds.right
                )
                &
                df_parcelas["centroid_lat"].between(
                    bounds.bottom,
                    bounds.top
                )
            )
        ]

    # Impresion de la cantidad de centroides dentro y fuera de la cobertura espacial
    print(
        f"Centroides dentro del raster: "
        f"{len(df_parcelas) - len(puntos_fuera)}"
    )
    print(
        f"Centroides fuera del raster: "
        f"{len(puntos_fuera)}"
    )

    # Mostrar las coordenadas de las parcelas que se encuentran fuera de la cobertura
    if len(puntos_fuera) > 0:
        print(
            puntos_fuera[
                [
                    "parcel_id",
                    "centroid_lat",
                    "centroid_lon"
                ]
            ].to_string(index=False)
        )

        # Interrupcion del proceso cuando hay parcelas sin cobertura climatica
        raise ValueError(
            "Hay centroides fuera de la cobertura "
            "del raster climático."
        )

    print(
        "Todos los centroides están dentro "
        "de la cobertura climática."
    )


def extraer_valor_pixel(
    src,
    longitud,
    latitud,
    nodata=None
):
    """
    Extrae el valor del pixel del raster correspondiente a las coordenadas 
    del centroide de la parcela, manejando valores nulos o NoData.
    """
    # Extraccion del valor del pixel correspondiente a las coordenadas del centroide
    muestra = next(
        src.sample(
            [(longitud, latitud)]
        )
    )

    # Conversion del valor extraido a un numero decimal
    valor = float(muestra[0])

    # Comprobacion de si el valor coincide con el NoData especifico del raster
    if nodata is not None:
        if np.isclose(
            valor,
            nodata
        ):
            return np.nan

    # Tratamiento del valor NoData utilizado para representar datos faltantes de temperatura
    if np.isclose(
        valor,
        TEMPERATURE_NODATA
    ):
        return np.nan

    # Comprobacion de que el valor extraido sea un numero finito
    if not np.isfinite(valor):
        return np.nan

    # Devolucion del valor valido del pixel
    return valor


def procesar_clima():
    """
    Funcion principal para procesar las series de tiempo climaticas (precipitacion y temperaturas)
    asociadas a los centroides de las parcelas, generando los archivos de salida correspondientes.
    """
    # Impresion del encabezado de la tarea que se va a ejecutar
    print("=" * 70)
    print(
        "P1.5 — PREPARAR CLIMA POR PARCELA"
    )
    print("=" * 70)

    # Creacion del directorio de salida si todavia no existe
    LIMPIO_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    # Validacion de la estructura y el contenido de los inventarios climaticos
    validar_inventarios()

    # Comprobacion de la existencia de todos los archivos GeoTIFF del periodo
    (
        archivos_prec,
        archivos_tmin,
        archivos_tmax
    ) = validar_archivos_raster()

    # Validacion del sistema de coordenadas, dimensiones, resolucion y valores NoData
    validar_rasters(
        archivos_prec,
        archivos_tmin,
        archivos_tmax
    )

    # Carga y validacion de los identificadores y centroides de las parcelas
    df_parcelas = cargar_parcelas()

    # Comprobacion de que todos los centroides esten dentro de la cobertura del raster
    validar_centroides(
        df_parcelas,
        archivos_prec[0]
    )

    print(
        "\nEXTRAYENDO CLIMA POR CENTROIDE"
    )

    # Calculo del numero total de extracciones esperadas (parcelas por 48 meses)
    total_combinaciones = (
        len(df_parcelas) * 48
    )

    print(
        f"Combinaciones a procesar: "
        f"{total_combinaciones}"
    )

    # Inicializacion de la lista que almacenara los resultados climaticos
    resultados = []
    procesadas = 0

    # Recorrido de cada anio del periodo de estudio
    for year in YEARS:

        # Recorrido de cada mes del anio actual
        for month in MONTHS:

            # Construccion de la fecha correspondiente al primer dia del mes procesado
            fecha = pd.Timestamp(
                year=year,
                month=month,
                day=1
            )

            # Obtencion de las rutas de los archivos climaticos del mes actual
            ruta_prec = (
                obtener_archivo_precipitacion(
                    year,
                    month
                )
            )
            ruta_tmin = (
                obtener_archivo_tmin(
                    year,
                    month
                )
            )
            ruta_tmax = (
                obtener_archivo_tmax(
                    year,
                    month
                )
            )

            print(
                f"Procesando {year}-{month:02d}..."
            )

            # Apertura simultanea de los tres rasters correspondientes al mismo mes
            with rasterio.open(
                ruta_prec
            ) as src_prec, \
                rasterio.open(
                    ruta_tmin
                ) as src_tmin, \
                rasterio.open(
                    ruta_tmax
                ) as src_tmax:

                # Recorrido de todas las parcelas para extraer sus valores climaticos
                for _, parcela in (
                    df_parcelas.iterrows()
                ):
                    # Obtencion del identificador y las coordenadas del centroide de la parcela
                    parcel_id = (
                        parcela["parcel_id"]
                    )
                    latitud = (
                        parcela["centroid_lat"]
                    )
                    longitud = (
                        parcela["centroid_lon"]
                    )

                    # Extraccion de la precipitacion mensual correspondiente a la parcela
                    precip = extraer_valor_pixel(
                        src_prec,
                        longitud,
                        latitud,
                        src_prec.nodata
                    )

                    # Extraccion de la temperatura minima mensual de la parcela
                    tmin = extraer_valor_pixel(
                        src_tmin,
                        longitud,
                        latitud,
                        TEMPERATURE_NODATA
                    )

                    # Extraccion de la temperatura maxima mensual de la parcela
                    tmax = extraer_valor_pixel(
                        src_tmax,
                        longitud,
                        latitud,
                        TEMPERATURE_NODATA
                    )

                    # Almacenamiento del identificador, fecha y valores climaticos obtenidos
                    resultados.append(
                        {
                            "parcel_id": parcel_id,
                            "fecha_captura":
                                fecha.strftime(
                                    "%Y-%m-%d"
                                ),
                            "precip_mm": precip,
                            "tmin_c": tmin,
                            "tmax_c": tmax
                        }
                    )

                    # Actualizacion del contador de combinaciones procesadas
                    procesadas += 1

            # Impresion del avance acumulado del procesamiento
            print(
                f"  Completado: "
                f"{procesadas}/{total_combinaciones}"
            )

    print(
        "\nGENERANDO CLIMATE_TIMESERIES.CSV"
    )

    # Conversion de la lista de resultados en un DataFrame para organizar las series climaticas
    df_clima = pd.DataFrame(
        resultados
    )

    # Conversion de la columna de fechas al formato de fecha y hora de Pandas
    df_clima["fecha_captura"] = (
        pd.to_datetime(
            df_clima["fecha_captura"]
        )
    )

    # Ordenamiento de los registros por identificador de parcela y fecha
    df_clima = (
        df_clima
        .sort_values(
            [
                "parcel_id",
                "fecha_captura"
            ]
        )
        .reset_index(drop=True)
    )

    # Identificacion de registros repetidos para una misma parcela y fecha
    duplicados = df_clima[
        df_clima.duplicated(
            [
                "parcel_id",
                "fecha_captura"
            ],
            keep=False
        )
    ]

    # Interrupcion del proceso si existen combinaciones duplicadas de parcela y fecha
    if len(duplicados) > 0:
        raise ValueError(
            "Existen combinaciones duplicadas "
            "parcel_id + fecha_captura."
        )

    # Exportacion de la serie temporal climatica a un archivo CSV sin incluir el indice
    df_clima.to_csv(
        OUTPUT_TIMESERIES,
        index=False,
        date_format="%Y-%m-%d"
    )

    # Impresion de la ubicacion y el numero de registros del archivo generado
    print(
        f"Generado: {OUTPUT_TIMESERIES}"
    )
    print(
        f"Filas generadas: {len(df_clima)}"
    )

    print(
        "\nGENERANDO CLIMATE_AGGREGATES.CSV"
    )

    # Agrupacion de los registros por parcela para calcular estadisticas climaticas del periodo
    df_agg = (
        df_clima
        .groupby(
            "parcel_id",
            as_index=False
        )
        .agg(
            # Suma de la precipitacion mensual registrada durante el periodo
            precip_total_mm=(
                "precip_mm",
                "sum"
            ),
            # Calculo de la precipitacion mensual promedio del periodo
            precip_mean_mm=(
                "precip_mm",
                "mean"
            ),
            # Calculo de la temperatura minima promedio del periodo
            tmin_mean_c=(
                "tmin_c",
                "mean"
            ),
            # Calculo de la temperatura maxima promedio del periodo
            tmax_mean_c=(
                "tmax_c",
                "mean"
            )
        )
    )

    # Exportacion de los agregados climaticos por parcela a formato CSV
    df_agg.to_csv(
        OUTPUT_AGGREGATES,
        index=False
    )

    # Impresion de la ubicacion del archivo de agregados generado
    print(
        f"Generado: {OUTPUT_AGGREGATES}"
    )

    # Impresion del resumen general de la tarea P1.5
    print(
        "RESUMEN P1.5"
    )

    # Reporte del numero de parcelas unicas procesadas
    print(
        f"Parcelas procesadas: "
        f"{df_clima['parcel_id'].nunique()}"
    )

    # Reporte del numero de meses unicos incluidos en las series temporales
    print(
        f"Meses procesados: "
        f"{df_clima['fecha_captura'].nunique()}"
    )

    # Reporte del total de registros climaticos generados
    print(
        f"Registros climáticos: "
        f"{len(df_clima)}"
    )

    # Comparacion del resultado obtenido con el numero de registros esperado
    print(
        "Registros esperados: "
        f"{len(df_parcelas) * 48}"
    )

    # Reporte de la cantidad de valores faltantes para cada variable climatica
    print(
        "\nValores faltantes:"
    )
    print(
        f"  precip_mm: "
        f"{df_clima['precip_mm'].isna().sum()}"
    )
    print(
        f"  tmin_c: "
        f"{df_clima['tmin_c'].isna().sum()}"
    )
    print(
        f"  tmax_c: "
        f"{df_clima['tmax_c'].isna().sum()}"
    )

    # Reporte de los valores minimos y maximos obtenidos para cada variable climatica
    print(
        "\nRangos obtenidos:"
    )
    print(
        f"  Precipitación: "
        f"{df_clima['precip_mm'].min():.2f} a "
        f"{df_clima['precip_mm'].max():.2f} mm"
    )
    print(
        f"  Tmin: "
        f"{df_clima['tmin_c'].min():.2f} a "
        f"{df_clima['tmin_c'].max():.2f} °C"
    )
    print(
        f"  Tmax: "
        f"{df_clima['tmax_c'].min():.2f} a "
        f"{df_clima['tmax_c'].max():.2f} °C"
    )

    # Impresion de las rutas de los archivos de salida creados durante el procesamiento
    print(
        "\nArchivos generados:"
    )
    print(
        f"  {OUTPUT_TIMESERIES}"
    )
    print(
        f"  {OUTPUT_AGGREGATES}"
    )

    print(
        "\nP1.5 FINALIZADO."
    )


if __name__ == "__main__":

    procesar_clima()
