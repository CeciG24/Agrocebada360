"""
Tarea: P1.11 — Crear datasets de predicción temprana
Proyecto: Cebada360
"""

import pandas as pd
from pathlib import Path


# Directorio que contiene los archivos procesados de entrada
BASE_DIR = Path("DATASET_RETO_AGRO_2026_LIMPIO")

# Archivos con las observaciones satelitales y climáticas
SATELITE_PATH = BASE_DIR / "basico_temporal_normalizado.csv"
CLIMA_PATH = BASE_DIR / "climate_timeseries.csv"

# Directorio donde se guardarán los datasets de cada corte temporal
OUTPUT_DIR = BASE_DIR / "prediccion_temprana"

# Crear el directorio de salida si todavía no existe
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


# Definir los meses límite para generar los cortes de predicción.
# Cada corte utiliza información desde abril de 2025 hasta el mes
# indicado, considerando las reglas temporales de cada fuente.
CORTES = {
    "junio": 6,
    "julio": 7,
    "agosto": 8,
    "septiembre": 9,
    "octubre": 10,
}


def main():
    """
    Carga los datos satelitales y climáticos, valida sus fechas
    y genera archivos independientes para cada corte temporal.

    Los datasets resultantes se guardan en el directorio
    prediccion_temprana.
    """

    # Leer los archivos CSV que contienen las observaciones
    # satelitales y los registros climáticos.
    print("\nCargando datasets...")

    df_satelite = pd.read_csv(SATELITE_PATH)
    df_clima = pd.read_csv(CLIMA_PATH)

    # Mostrar la cantidad de registros disponibles en cada fuente
    print(f"Satélite: {len(df_satelite):,} registros")
    print(f"Clima:    {len(df_clima):,} registros")

    # Convertir fecha_captura al formato datetime para poder
    # filtrar los registros por año, mes e intervalo temporal.
    # Los valores que no puedan convertirse se transforman en NaT.
    df_satelite["fecha_captura"] = pd.to_datetime(
        df_satelite["fecha_captura"],
        errors="coerce"
    )

    df_clima["fecha_captura"] = pd.to_datetime(
        df_clima["fecha_captura"],
        errors="coerce"
    )

    # Detener la ejecución si existen fechas inválidas en alguno
    # de los archivos, ya que podrían afectar los filtros temporales.
    if df_satelite["fecha_captura"].isna().any():
        raise ValueError(
            "Existen fechas inválidas en los datos satelitales."
        )

    if df_clima["fecha_captura"].isna().any():
        raise ValueError(
            "Existen fechas inválidas en los datos climáticos."
        )

    # Mostrar las fechas mínima y máxima de cada fuente para
    # conocer el periodo temporal que cubren los datos.
    print("\nPeriodo satelital:")
    print(
        f"  {df_satelite['fecha_captura'].min().date()} "
        f"→ "
        f"{df_satelite['fecha_captura'].max().date()}"
    )

    print("Periodo climático:")
    print(
        f"  {df_clima['fecha_captura'].min().date()} "
        f"→ "
        f"{df_clima['fecha_captura'].max().date()}"
    )

    # Contar los registros satelitales disponibles por año.
    # Esto permite revisar cómo se distribuyen las observaciones
    # antes de generar los cortes de predicción.
    print("\nDistribución satelital por año:")

    print(
        df_satelite["fecha_captura"]
        .dt.year
        .value_counts()
        .sort_index()
        .to_string()
    )

    # Realizar el mismo conteo para los registros climáticos.
    print("\nDistribución climática por año:")

    print(
        df_clima["fecha_captura"]
        .dt.year
        .value_counts()
        .sort_index()
        .to_string()
    )

    # Procesar cada mes límite definido en CORTES para producir
    # un par de archivos: uno satelital y otro climático.
    print("\nGenerando cortes temporales")

    for nombre_corte, mes_limite in CORTES.items():

        print(
            f"\nProcesando corte abril-{nombre_corte}..."
        )

        # Definir el inicio del ciclo agrícola analizado.
        inicio_ciclo = pd.Timestamp("2025-04-01")

        # Calcular el límite exclusivo del corte satelital.
        # Se toma el primer día del mes siguiente para incluir
        # todas las observaciones del mes límite.
        fin_exclusivo = (
            pd.Timestamp(year=2025, month=mes_limite, day=1)
            + pd.offsets.MonthBegin(1)
        )

        # Los registros climáticos tienen fechas al inicio del mes
        # al que corresponden. Por ello, se excluye el mes límite
        # para no utilizar su agregado mensual antes de que termine.
        fin_clima_exclusivo = pd.Timestamp(
            year=2025,
            month=mes_limite,
            day=1
        )

        # Seleccionar las observaciones satelitales comprendidas
        # entre abril y el final del mes límite, exclusivamente
        # para el año 2025.
        mascara_fechas_sat = (
            df_satelite["fecha_captura"].ge(inicio_ciclo)
            & df_satelite["fecha_captura"].lt(fin_exclusivo)
            & df_satelite["fecha_captura"].dt.year.eq(2025)
        )

        # Seleccionar los registros climáticos desde abril hasta
        # antes del inicio del mes límite. De esta manera, no se
        # incorpora el agregado del mes que todavía está en curso.
        mascara_fechas_clima = (
            df_clima["fecha_captura"].ge(inicio_ciclo)
            & df_clima["fecha_captura"].lt(fin_clima_exclusivo)
            & df_clima["fecha_captura"].dt.year.eq(2025)
        )

        # Aplicar el filtro temporal y conservar únicamente
        # las observaciones del sensor Sentinel-2.
        sat_corte = df_satelite.loc[
            mascara_fechas_sat
            & df_satelite["sensor"].eq("Sentinel-2")
        ].copy()

        # Obtener los registros climáticos correspondientes
        # al intervalo permitido para el corte actual.
        clima_corte = df_clima.loc[
            mascara_fechas_clima
        ].copy()

        # Comprobar que los registros seleccionados no contengan
        # fechas anteriores al inicio del ciclo, posteriores al
        # límite permitido o pertenecientes a otro año.
        # Esta validación busca prevenir fugas temporales.
        for nombre, df_corte in [
            ("satelital", sat_corte),
            ("climático", clima_corte),
        ]:
            if not df_corte.empty:
                fechas = df_corte["fecha_captura"]

                if (
                    fechas.lt(inicio_ciclo).any()
                    or fechas.ge(fin_exclusivo).any()
                    or fechas.dt.year.ne(2025).any()
                ):
                    raise ValueError(
                        f"Fuga temporal detectada en el corte "
                        f"{nombre_corte}: datos {nombre} fuera "
                        f"del intervalo permitido."
                    )

        # Construir la ruta de salida del archivo correspondiente
        # a Sentinel-2 para el mes límite actual.
        sat_path = (
            OUTPUT_DIR
            / f"sentinel2_corte_{nombre_corte}.csv"
        )

        # Exportar los registros satelitales sin incluir
        # el índice interno del DataFrame.
        sat_corte.to_csv(
            sat_path,
            index=False
        )

        # Construir la ruta de salida del archivo climático
        # correspondiente al mismo corte temporal.
        clima_path = (
            OUTPUT_DIR
            / f"climate_corte_{nombre_corte}.csv"
        )

        # Exportar los registros climáticos seleccionados.
        clima_corte.to_csv(
            clima_path,
            index=False
        )

        # Contar las parcelas distintas presentes en cada archivo.
        # El dataset satelital utiliza ID_POLIGONO y el climático
        # utiliza parcel_id como identificadores de parcela.
        parcelas_sat = (
            sat_corte["ID_POLIGONO"]
            .nunique()
        )

        parcelas_clima = (
            clima_corte["parcel_id"]
            .nunique()
        )

        # Mostrar el número de registros y parcelas de cada fuente
        # para facilitar la revisión de los archivos generados.
        print(f"  Satélite: {len(sat_corte):,} registros")
        print(f"  Parcelas satélite: {parcelas_sat}")

        print(f"  Clima: {len(clima_corte):,} registros")
        print(f"  Parcelas clima: {parcelas_clima}")

        # Mostrar las rutas de los archivos guardados
        print(f"  {sat_path}")
        print(f"  {clima_path}")

    # Informar que terminó el proceso y mostrar los cortes
    # temporales que se generaron.
    print("\nP1.11 completada")
    print("\nCortes generados:")

    for nombre_corte in CORTES:
        print(
            f"  abril-{nombre_corte}"
        )

if __name__ == "__main__":
    main()