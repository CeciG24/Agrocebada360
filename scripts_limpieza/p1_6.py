"""
Tarea: P1.6 — Preparar topografía y geometría
Proyecto: Cebada360
"""

from pathlib import Path

import numpy as np
import pandas as pd
import geopandas as gpd
import rasterio
from rasterio.mask import mask


# Definicion de las rutas base para los archivos originales y los datos procesados
BASE_DIR = Path("DATASET_RETO_AGRO_2026")

LIMPIO_DIR = Path("DATASET_RETO_AGRO_2026_LIMPIO")

# Ruta al archivo maestro que contiene los identificadores y atributos de las parcelas
PARCEL_MASTER = LIMPIO_DIR / "parcel_master.csv"

# Ruta al Shapefile que contiene las geometrías de las parcelas
SHAPEFILE = (
    BASE_DIR
    / "Parcelas_Reto_AGC_CONJUNTO_70_30"
    / "Parcelas_Reto_AGC_CONJUNTO.shp"
)

# Ruta al raster de elevacion del modelo topografico INEGI CEM4 con resolucion de 120 metros
ELEVACION_RASTER = (
    BASE_DIR
    / "Reto_AgroCebada_Topografia_INEGI_CEM4"
    / "Reto_AgroCebada_Topografia_INEGI_CEM4"
    / "Elevacion_INEGI_CEM4_120m.tif"
)

# Ruta al raster de pendiente del terreno expresada en grados
PENDIENTE_RASTER = (
    BASE_DIR
    / "Reto_AgroCebada_Topografia_INEGI_CEM4"
    / "Reto_AgroCebada_Topografia_INEGI_CEM4"
    / "Pendiente_INEGI_CEM4_120m_grados.tif"
)

# Definicion de la ruta donde se guardara el archivo maestro de topografia
OUTPUT = LIMPIO_DIR / "topography_master.csv"

# Definicion de las columnas esperadas en el archivo final de topografia
EXPECTED_COLUMNS = [
    "parcel_id",
    "area_ha",
    "elevation_mean",
    "slope_mean",
    "municipio",
    "estado",
    "centroid_lat",
    "centroid_lon",
]


def validar_archivos():
    """
    Verifica la existencia de los archivos de entrada necesarios
    para procesar la topografia de las parcelas.
    """
    print("\n--- VALIDANDO ARCHIVOS DE ENTRADA ---")

    # Organizacion de las rutas de entrada en un diccionario para facilitar su validacion
    archivos = {
        "parcel_master.csv": PARCEL_MASTER,
        "Shapefile": SHAPEFILE,
        "Elevación": ELEVACION_RASTER,
        "Pendiente": PENDIENTE_RASTER,
    }

    # Recorrido de los archivos para comprobar que existan en las rutas especificadas
    for nombre, ruta in archivos.items():
        if not ruta.exists():
            raise FileNotFoundError(
                f"No se encontró {nombre}:\n{ruta}"
            )

        print(f"{nombre}: OK")

    print("Todos los archivos de entrada existen.")


def cargar_parcel_master():
    """
    Carga el archivo maestro de parcelas y valida las columnas requeridas,
    los identificadores y los atributos necesarios para el procesamiento.
    """
    print("\n--- CARGANDO PARCEL MASTER ---")

    # Lectura del archivo CSV que contiene los atributos principales de las parcelas
    df = pd.read_csv(PARCEL_MASTER)

    # Definicion de las columnas obligatorias para el procesamiento topografico
    columnas_requeridas = [
        "parcel_id",
        "area_ha",
        "municipio",
        "estado",
        "centroid_lat",
        "centroid_lon",
    ]

    # Identificacion de las columnas requeridas que no existen en el archivo maestro
    faltantes = [
        col for col in columnas_requeridas
        if col not in df.columns
    ]

    # Interrupcion del proceso si faltan columnas necesarias
    if faltantes:
        raise ValueError(
            f"Faltan columnas en parcel_master.csv: {faltantes}"
        )

    # Verificacion de que cada identificador de parcela sea unico
    if df["parcel_id"].duplicated().any():

        # Obtencion de los identificadores que aparecen repetidos
        duplicados = df.loc[
            df["parcel_id"].duplicated(),
            "parcel_id"
        ].tolist()

        raise ValueError(
            f"Hay parcel_id duplicados: {duplicados}"
        )

    # Validacion de que todas las parcelas tengan registrada su superficie en hectareas
    if df["area_ha"].isna().any():
        raise ValueError(
            "Hay parcelas sin area_ha."
        )

    # Validacion de que todas las parcelas tengan registrado su municipio
    if df["municipio"].isna().any():
        raise ValueError(
            "Hay parcelas sin municipio."
        )

    # Validacion de que todas las parcelas tengan registrado su estado
    if df["estado"].isna().any():
        raise ValueError(
            "Hay parcelas sin estado."
        )

    # Impresion del numero de parcelas cargadas y de las columnas utilizadas
    print(f"Parcelas cargadas: {len(df)}")

    print(
        "Columnas utilizadas: "
        "parcel_id, area_ha, municipio, estado, "
        "centroid_lat, centroid_lon"
    )

    # Devolucion del DataFrame validado para continuar con el procesamiento
    return df


def cargar_shapefile():
    """
    Carga el Shapefile de parcelas y valida su sistema de coordenadas,
    identificadores y geometrías.
    """
    print("\n--- CARGANDO SHAPEFILE ---")

    # Lectura de la capa geografica mediante GeoPandas
    gdf = gpd.read_file(SHAPEFILE)

    # Impresion del numero de parcelas y del sistema de coordenadas original
    print(f"Parcelas en Shapefile: {len(gdf)}")
    print(f"CRS del Shapefile: {gdf.crs}")

    # Comprobacion de que el Shapefile tenga definido un sistema de referencia de coordenadas
    if gdf.crs is None:
        raise ValueError(
            "El Shapefile no tiene CRS definido."
        )

    # Busqueda automatica de la columna que contiene el identificador de cada poligono
    posibles_columnas = [
        col for col in gdf.columns
        if col.upper() == "ID_POLIGON"
    ]

    # Generacion de un error si no se encuentra la columna del identificador
    if not posibles_columnas:
        raise ValueError(
            "No se encontró la columna ID_POLIGON "
            "en el Shapefile."
        )

    # Seleccion del nombre de la columna identificadora encontrada
    id_columna = posibles_columnas[0]

    print(f"Identificador del Shapefile: {id_columna}")

    # Renombramiento de la columna para utilizar el mismo identificador que el archivo maestro
    gdf = gdf.rename(
        columns={id_columna: "parcel_id"}
    )

    # Conversion de los identificadores a texto para facilitar la comparacion entre archivos
    gdf["parcel_id"] = gdf["parcel_id"].astype(str)

    # Conteo de las geometrías nulas que no contienen una geometría definida
    geometria_nula = gdf.geometry.isna().sum()

    # Interrupcion del proceso si existen geometrías nulas
    if geometria_nula > 0:
        raise ValueError(
            f"Hay {geometria_nula} geometrías nulas."
        )

    # Conteo de las geometrías vacías que no representan un polígono válido
    geometria_vacia = gdf.geometry.is_empty.sum()

    # Interrupcion del proceso si existen geometrías vacías
    if geometria_vacia > 0:
        raise ValueError(
            f"Hay {geometria_vacia} geometrías vacías."
        )

    # Verificacion de que no existan identificadores de parcela repetidos
    if gdf["parcel_id"].duplicated().any():

        # Obtencion de los identificadores duplicados del Shapefile
        duplicados = gdf.loc[
            gdf["parcel_id"].duplicated(),
            "parcel_id"
        ].tolist()

        raise ValueError(
            f"Hay parcel_id duplicados en el Shapefile: "
            f"{duplicados}"
        )

    # Confirmacion de que las geometrías superaron las validaciones
    print("Geometrías válidas.")
    print(f"CRS: {gdf.crs}")

    # Devolucion de la capa geografica validada
    return gdf


def validar_coincidencia(df_master, gdf):
    """
    Compara los identificadores del archivo maestro y del Shapefile
    para comprobar que ambos contengan las mismas parcelas.
    """
    print("\n--- VALIDANDO COINCIDENCIA DE PARCELAS ---")

    # Conversion de los identificadores de ambos archivos a conjuntos para compararlos
    ids_master = set(df_master["parcel_id"].astype(str))
    ids_shape = set(gdf["parcel_id"].astype(str))

    # Identificacion de las parcelas que faltan en el Shapefile y de las que aparecen de mas
    faltan_en_shape = ids_master - ids_shape
    sobran_en_shape = ids_shape - ids_master

    # Impresion de la cantidad de identificadores unicos de cada archivo
    print(f"Parcelas en parcel_master: {len(ids_master)}")
    print(f"Parcelas en Shapefile: {len(ids_shape)}")

    # Reporte de las parcelas registradas en el maestro que no aparecen en el Shapefile
    if faltan_en_shape:
        print(
            "Parcelas del master que no están en el Shapefile:"
        )
        print(sorted(faltan_en_shape))

    # Reporte de las parcelas del Shapefile que no aparecen en el archivo maestro
    if sobran_en_shape:
        print(
            "Parcelas del Shapefile que no están en el master:"
        )
        print(sorted(sobran_en_shape))

    # Interrupcion del proceso si los identificadores de ambos archivos no coinciden
    if faltan_en_shape or sobran_en_shape:
        raise ValueError(
            "Las parcelas del parcel_master y del "
            "Shapefile no coinciden."
        )

    # Confirmacion del numero de parcelas que coinciden entre ambos archivos
    print(
        f"Parcelas coincidentes: {len(ids_master)}"
    )


def validar_raster(ruta, nombre):
    """
    Comprueba los metadatos espaciales de un raster, incluyendo
    el CRS, las dimensiones, la resolucion y el numero de bandas.
    """
    print(f"\nValidando raster: {nombre}")

    # Apertura del raster para consultar sus propiedades y metadatos
    with rasterio.open(ruta) as src:

        # Impresion de las caracteristicas principales del raster
        print(f"  CRS: {src.crs}")
        print(f"  Dimensiones: {src.width} x {src.height}")
        print(
            f"  Resolución: "
            f"{src.res[0]} x {src.res[1]}"
        )
        print(f"  NoData: {src.nodata}")
        print(f"  Bandas: {src.count}")

        # Verificacion de que el raster tenga definido su sistema de coordenadas
        if src.crs is None:
            raise ValueError(
                f"{nombre} no tiene CRS."
            )

        # Comprobacion de que exista al menos una banda de datos
        if src.count < 1:
            raise ValueError(
                f"{nombre} no contiene bandas."
            )

        # Validacion de que las resoluciones horizontal y vertical sean valores finitos
        if not np.isfinite(src.res[0]) or not np.isfinite(src.res[1]):
            raise ValueError(
                f"Resolución inválida en {nombre}."
            )

    print(f"{nombre}: metadatos válidos.")


def extraer_media_por_poligono(geometria, raster_path):
    """
    Extrae los valores del raster que intersectan un poligono y calcula
    su media, descartando los valores faltantes y los datos no validos.
    """
    # Apertura del raster que contiene los datos topograficos que se van a extraer
    with rasterio.open(raster_path) as src:

        # La geometria recibida debe estar previamente transformada al CRS del raster

        try:
            # Recorte del raster utilizando la geometria del poligono como mascara
            # all_touched=True incluye los pixeles que son tocados por el poligono
            data, _ = mask(
                src,
                [geometria],
                crop=True,
                filled=False,
                all_touched=True,
            )
        except ValueError:
            # Devolucion de un valor faltante cuando no es posible realizar el recorte
            return np.nan

        # Obtencion de los valores de la primera banda del raster recortado
        valores = data[0]

        # Extraccion de los valores no enmascarados cuando el resultado es una matriz enmascarada
        if np.ma.isMaskedArray(valores):
            valores = valores.compressed()

        # Conversion de los datos extraidos a un arreglo numerico de tipo decimal
        valores = np.asarray(valores, dtype=float)

        # Comprobacion de que existan pixeles disponibles dentro del poligono
        if valores.size == 0:
            return np.nan

        # Eliminacion de los valores que no son numeros finitos
        valores = valores[np.isfinite(valores)]

        # Devolucion de un valor faltante si no quedan datos numericos validos
        if valores.size == 0:
            return np.nan

        # Eliminacion de los pixeles que contienen el valor NoData definido en el raster
        if src.nodata is not None:
            valores = valores[
                ~np.isclose(
                    valores,
                    src.nodata
                )
            ]

        # Comprobacion de que queden valores validos despues de excluir NoData
        if valores.size == 0:
            return np.nan

        # Calculo y devolucion de la media de los valores validos del poligono
        return float(np.mean(valores))


def procesar_topografia(df_master, gdf):
    """
    Procesa los datos de elevacion y pendiente para cada parcela,
    utilizando sus geometrías para extraer los valores medios de los rasters.
    """
    print("\n--- PROCESANDO TOPOGRAFÍA ---")

    # Apertura del raster de elevacion para consultar su sistema de coordenadas
    with rasterio.open(ELEVACION_RASTER) as src_elev:
        elev_crs = src_elev.crs

    # Apertura del raster de pendiente para consultar su sistema de coordenadas
    with rasterio.open(PENDIENTE_RASTER) as src_slope:
        slope_crs = src_slope.crs

    # Comprobacion de que el raster de elevacion tenga un CRS definido
    if elev_crs is None:
        raise ValueError(
            "El raster de elevación no tiene CRS."
        )

    # Comprobacion de que el raster de pendiente tenga un CRS definido
    if slope_crs is None:
        raise ValueError(
            "El raster de pendiente no tiene CRS."
        )

    # Verificacion de que ambos rasters utilicen el mismo sistema de coordenadas
    if elev_crs != slope_crs:
        raise ValueError(
            "Los rasters de elevación y pendiente "
            "tienen CRS diferentes."
        )

    # Asignacion del sistema de coordenadas compartido por los dos rasters
    raster_crs = elev_crs

    print(f"CRS de los rasters: {raster_crs}")

    # Transformacion de las geometrías al sistema de coordenadas de los rasters cuando sea necesario
    if gdf.crs != raster_crs:
        print(
            f"Reproyectando geometrías: "
            f"{gdf.crs} -> {raster_crs}"
        )

        # Reproyeccion de las geometrías para que coincidan espacialmente con los rasters
        gdf_raster = gdf.to_crs(raster_crs)
    else:
        print(
            "El Shapefile ya está en el mismo CRS "
            "que los rasters."
        )

        # Copia de la capa geografica cuando no es necesario transformar sus coordenadas
        gdf_raster = gdf.copy()

    # Creacion de un indice por identificador para localizar la geometria de cada parcela
    geometries = gdf_raster.set_index("parcel_id")["geometry"]

    # Inicializacion de la lista donde se almacenaran los resultados topograficos
    resultados = []

    # Obtencion del numero total de parcelas que deben procesarse
    total = len(df_master)

    # Recorrido de cada parcela registrada en el archivo maestro
    for i, row in df_master.iterrows():

        # Obtencion del identificador de la parcela actual como texto
        parcel_id = str(row["parcel_id"])

        # Busqueda de la geometria asociada al identificador de la parcela
        geometria = geometries.loc[parcel_id]

        # Extraccion de la elevacion media de los pixeles que intersectan la parcela
        elevation_mean = extraer_media_por_poligono(
            geometria,
            ELEVACION_RASTER
        )

        # Extraccion de la pendiente media de los pixeles que intersectan la parcela
        slope_mean = extraer_media_por_poligono(
            geometria,
            PENDIENTE_RASTER
        )

        # Almacenamiento de los atributos originales y los valores topograficos calculados
        resultados.append({
            "parcel_id": parcel_id,
            "area_ha": row["area_ha"],
            "elevation_mean": elevation_mean,
            "slope_mean": slope_mean,
            "municipio": row["municipio"],
            "estado": row["estado"],
            "centroid_lat": row["centroid_lat"],
            "centroid_lon": row["centroid_lon"],
        })

        # Actualizacion del indicador de avance del procesamiento de las parcelas
        print(
            f"  Completado: {i + 1}/{total}",
            end="\r"
        )

    print()

    # Conversion de los resultados recopilados en un DataFrame
    return pd.DataFrame(resultados)


def validar_resultado(df):
    """
    Valida la cantidad de parcelas, la unicidad de los identificadores,
    las columnas requeridas y los valores obtenidos en el procesamiento.
    """
    print("\n--- VALIDANDO RESULTADO ---")

    # Comprobacion de que el resultado contenga las 197 parcelas esperadas
    if len(df) != 197:
        raise ValueError(
            f"Se esperaban 197 parcelas, "
            f"pero se generaron {len(df)}."
        )

    # Verificacion de que no existan identificadores de parcela duplicados
    if df["parcel_id"].duplicated().any():
        raise ValueError(
            "Hay parcel_id duplicados en el resultado."
        )

    # Identificacion de las columnas esperadas que no aparecen en el resultado
    faltantes_columnas = [
        col for col in EXPECTED_COLUMNS
        if col not in df.columns
    ]

    # Interrupcion del proceso si faltan columnas obligatorias
    if faltantes_columnas:
        raise ValueError(
            f"Faltan columnas: {faltantes_columnas}"
        )

    # Impresion del total de parcelas generadas
    print(
        f"Parcelas generadas: {len(df)}"
    )

    # Reporte de los valores faltantes en los atributos principales y topograficos
    print("\nValores faltantes:")

    # Recorrido de las columnas para contar sus valores nulos
    for columna in [
        "area_ha",
        "elevation_mean",
        "slope_mean",
        "municipio",
        "estado",
        "centroid_lat",
        "centroid_lon",
    ]:
        print(
            f"  {columna}: "
            f"{df[columna].isna().sum()}"
        )

    # Advertencia cuando existen parcelas sin datos de elevacion
    if df["elevation_mean"].isna().any():
        print(
            "\nADVERTENCIA: hay parcelas sin "
            "elevación."
        )

    # Advertencia cuando existen parcelas sin datos de pendiente
    if df["slope_mean"].isna().any():
        print(
            "ADVERTENCIA: hay parcelas sin "
            "pendiente."
        )

    # Impresion de los valores minimos y maximos de superficie, elevacion y pendiente
    print("\nRangos obtenidos:")

    # Reporte del rango de superficies de las parcelas en hectareas
    print(
        f"  Área: "
        f"{df['area_ha'].min():.2f} - "
        f"{df['area_ha'].max():.2f} ha"
    )

    # Reporte del rango de elevaciones medias en metros
    print(
        f"  Elevación: "
        f"{df['elevation_mean'].min():.2f} - "
        f"{df['elevation_mean'].max():.2f} m"
    )

    # Reporte del rango de pendientes medias en grados
    print(
        f"  Pendiente: "
        f"{df['slope_mean'].min():.2f} - "
        f"{df['slope_mean'].max():.2f} grados"
    )


def procesar_p1_6():
    """
    Ejecuta el flujo principal de la tarea P1.6, validando los archivos,
    procesando los rasters y generando el maestro de topografia.
    """

    # Impresion del encabezado de la tarea P1.6
    print("=" * 70)
    print("P1.6 — PREPARAR TOPOGRAFÍA Y GEOMETRÍA")
    print("=" * 70)

    # Validacion de la existencia de los archivos de entrada
    validar_archivos()

    # Validacion de los metadatos del raster de elevacion
    validar_raster(
        ELEVACION_RASTER,
        "Elevación INEGI CEM4"
    )

    # Validacion de los metadatos del raster de pendiente
    validar_raster(
        PENDIENTE_RASTER,
        "Pendiente INEGI CEM4"
    )

    # Carga del archivo maestro con los atributos de las parcelas
    df_master = cargar_parcel_master()

    # Carga del Shapefile con las geometrías de las parcelas
    gdf = cargar_shapefile()

    # Comprobacion de que los identificadores coincidan entre el maestro y el Shapefile
    validar_coincidencia(
        df_master,
        gdf
    )

    # Extraccion de los valores medios de elevacion y pendiente para cada parcela
    df_resultado = procesar_topografia(
        df_master,
        gdf
    )

    print("\n--- GENERANDO TOPOGRAPHY_MASTER.CSV ---")

    # Seleccion y ordenamiento de las columnas que conformaran el archivo final
    df_resultado = df_resultado[EXPECTED_COLUMNS]

    # Exportacion del maestro topografico a CSV sin incluir el indice del DataFrame
    df_resultado.to_csv(
        OUTPUT,
        index=False
    )

    print(f"Generado: {OUTPUT}")

    # Validacion de la estructura, cantidad de registros y valores del resultado generado
    validar_resultado(df_resultado)

    # Impresion del resumen final de la tarea P1.6
    print("\n" + "=" * 70)
    print("RESUMEN P1.6")
    print("=" * 70)

    # Reporte del numero total de parcelas procesadas
    print(
        f"Parcelas procesadas: "
        f"{len(df_resultado)}"
    )

    # Reporte del numero de columnas del archivo maestro de topografia
    print(
        f"Columnas generadas: "
        f"{len(df_resultado.columns)}"
    )

    print("\nArchivo generado:")
    print(f"  {OUTPUT}")

    print("\nP1.6 FINALIZADO.")


if __name__ == "__main__":

    procesar_p1_6()