"""
Tarea: P1.2 — Validar IDs y crear maestro de parcelas
Proyecto: Cebada360
"""

import pandas as pd
import geopandas as gpd
from pathlib import Path
import json


def preparar_parcel_master(ruta_shp):
    """
    Funcion para procesar el Shapefile de parcelas, validar conteos,
    asegurar sistemas de coordenadas, calcular centroides geograficos 
    y generar el archivo maestro de parcelas.
    """

    print("Cargando parcelas...")

    # Carga de la capa geografica en formato Shapefile utilizando GeoPandas
    gdf = gpd.read_file(ruta_shp)

    print(f"Parcelas encontradas: {len(gdf)}")
    print(f"CRS original: {gdf.crs}")
    if gdf.crs is None:
        raise ValueError("El shapefile no declara su CRS de origen.")
    source_crs = gdf.crs.to_string()
    ids = gdf["ID_POLIGON"]
    if ids.isna().any() or ids.astype(str).str.strip().eq("").any() or ids.duplicated().any():
        raise ValueError("El shapefile requiere IDs únicos y no vacíos.")
    if not ids.map(lambda value: isinstance(value, str)).all():
        raise ValueError("Los IDs deben llegar como string; no se convierten desde números.")
    if (gdf.geometry.isna().any() or gdf.geometry.is_empty.any()
            or not gdf.geometry.is_valid.all()
            or not gdf.geom_type.isin(["Polygon", "MultiPolygon"]).all()):
        raise ValueError("Geometrías nulas, vacías, inválidas o de tipo no poligonal.")

    # Validacion del numero esperado de registros (197 parcelas)
    if len(gdf) != 197:
        print(
            f"ADVERTENCIA: se esperaban 197 parcelas, "
            f"pero se encontraron {len(gdf)}."
        )

    # Verificacion y transformacion del sistema de referencia de coordenadas a WGS84 (EPSG:4326)
    if gdf.crs != "EPSG:4326":
        gdf = gdf.to_crs("EPSG:4326")

    # Calculo preciso de centroides proyectando temporalmente a un CRS UTM optimizado para la zona
    gdf_utm = gdf.to_crs(gdf.estimate_utm_crs())
    centroides_utm = gdf_utm.geometry.centroid

    # Conversion de los centroides calculados de vuelta al sistema geografico WGS84
    centroides_wgs84 = gpd.GeoSeries(
        centroides_utm,
        crs=gdf_utm.crs
    ).to_crs("EPSG:4326")

    # Asignacion de las coordenadas de latitud y longitud al GeoDataFrame principal
    gdf["centroid_lat"] = centroides_wgs84.y
    gdf["centroid_lon"] = centroides_wgs84.x

    # Seleccion de las columnas de interes para conformar el DataFrame maestro
    parcel_master = gdf[
        [
            "ID_POLIGON",
            "CONJUNTO",
            "Municipio",
            "Estado",
            "área_ha",
            "centroid_lat",
            "centroid_lon",
        ]
    ].copy()

    # Renombramiento de columnas para estandarizar la nomenclatura del dataset
    parcel_master = parcel_master.rename(
        columns={
            "ID_POLIGON": "parcel_id",
            "CONJUNTO": "dataset_split",
            "Municipio": "municipio",
            "Estado": "estado",
            "área_ha": "area_ha",
        }
    )

    # Definicion de la ruta y exportacion del DataFrame maestro a formato CSV
    ruta_salida = "DATASET_RETO_AGRO_2026_LIMPIO/parcel_master.csv"
    Path(ruta_salida).parent.mkdir(parents=True, exist_ok=True)
    # GeoJSON de interoperabilidad: únicamente ID y geometría, sin atributos privados.
    from shapely import force_2d
    geometry = gdf[["ID_POLIGON", "geometry"]].rename(columns={"ID_POLIGON": "parcel_id"}).copy()
    geometry.geometry = geometry.geometry.map(force_2d)
    Path(ruta_salida).with_name("parcels.geojson").write_text(geometry.to_json(), encoding="utf-8")
    Path(ruta_salida).with_name("geometry_metadata.json").write_text(json.dumps({
        "source_crs": source_crs, "api_crs": "EPSG:4326", "n_parcels": len(gdf),
        "validation": "nonempty valid Polygon/MultiPolygon; unique string IDs",
        "coordinate_order": "longitude, latitude", "dimensions": 2,
        "source": str(ruta_shp),
    }, indent=2), encoding="utf-8")

    parcel_master.to_csv(
        ruta_salida,
        index=False,
        encoding="utf-8-sig"
    )

    # Despliegue de resumenes informativos y estadisticas basicas del resultado obtenido
    print(f"\nparcel_master.csv generado correctamente.")
    print(f"Ubicacion: {ruta_salida}")
    print(f"Total de parcelas: {len(parcel_master)}")

    print("\nColumnas finales:")
    print(parcel_master.columns.tolist())

    print("\nDistribucion del conjunto:")
    print(parcel_master["dataset_split"].value_counts())

    print("\nMunicipios:")
    print(parcel_master["municipio"].value_counts())

    return parcel_master


if __name__ == "__main__":

    # Definicion de la ruta al archivo Shapefile de entrada
    ruta_shp = (
        "DATASET_RETO_AGRO_2026/"
        "Parcelas_Reto_AGC_CONJUNTO_70_30/"
        "Parcelas_Reto_AGC_CONJUNTO.shp"
    )

    # Ejecucion de la funcion principal
    preparar_parcel_master(ruta_shp)
