"""
Tarea: P1.13 — Auditoría temporal y prevención de Data Leakage
Proyecto: Cebada360
"""

import pandas as pd
import numpy as np
from pathlib import Path


# Directorio que contiene los archivos procesados del proyecto
BASE_DIR = Path("DATASET_RETO_AGRO_2026_LIMPIO")

# Archivos maestros que se utilizarán como referencia
MASTER_PATH = BASE_DIR / "features_master.csv"
PARCEL_PATH = BASE_DIR / "parcel_master.csv"

# Directorios donde se encuentran los datasets de predicción temprana
PRED_DIR = BASE_DIR / "prediccion_temprana"
FEATURES_DIR = PRED_DIR / "features"

# Archivo que contiene los valores reales de rendimiento
TARGET_PATH = BASE_DIR / "targets" / "rendimiento.csv"

# Definir el inicio y el final del ciclo agrícola permitido
CYCLE_START = pd.Timestamp("2025-04-01")
DATA_CUTOFF = pd.Timestamp("2025-10-31")

# Meses límite que se utilizarán para auditar los cortes temporales
CORTES = {
    "junio": 6,
    "julio": 7,
    "agosto": 8,
    "septiembre": 9,
    "octubre": 10,
}

# Combinaciones de parcela y característica en las que se esperan
# valores faltantes documentados, según las reglas de esta auditoría.
NAN_ESPERADOS = {
    ("AGC_043", "planet_ndvi_decay_rate"),
    ("AGC_175", "planet_ndvi_decay_rate"),
}

# Nombres habituales de columnas que pueden contener fechas
COLUMNAS_FECHA = [
    "fecha_captura",
    "fecha",
    "date",
    "datetime",
    "fecha_mes",
    "periodo",
]

# Nombres alternativos para las columnas de año y mes
COLUMNAS_ANIO = ["anio", "año", "year"]
COLUMNAS_MES = ["mes", "month"]


def exigir(condicion, mensaje):
    """
    Detiene la auditoría si una condición no se cumple.

    Parámetros:
        condicion: expresión booleana que se debe verificar.
        mensaje: descripción del error que se mostrará.
    """

    # Generar un error cuando la validación resulte falsa
    if not condicion:
        raise ValueError(mensaje)


def leer_csv(path):
    """
    Lee un archivo CSV y valida que no tenga nombres de columnas
    duplicados.

    Los identificadores de parcela se conservan como texto para
    evitar diferencias de formato entre archivos.
    """

    # Comprobar que el archivo exista antes de intentar leerlo
    exigir(path.exists(), f"No existe el archivo: {path}")

    # Leer el archivo conservando los identificadores como cadenas
    df = pd.read_csv(
        path,
        dtype={"parcel_id": str, "ID_POLIGONO": str}
    )

    # Comprobar que cada nombre de columna aparezca una sola vez
    exigir(
        len(df.columns) == len(set(df.columns)),
        f"Hay columnas duplicadas en {path.name}."
    )

    return df


def encontrar_columna(df, candidatas):
    """
    Busca una columna a partir de una lista de nombres posibles.

    La comparación ignora las mayúsculas y los espacios al principio
    o al final del nombre de la columna.

    Retorna:
        El nombre original de la columna encontrada o None.
    """

    # Crear un diccionario con los nombres normalizados y sus nombres
    # originales para conservar la referencia a la columna correcta.
    normalizadas = {
        str(col).strip().lower(): col
        for col in df.columns
    }

    # Revisar los nombres candidatos hasta encontrar una coincidencia
    for candidata in candidatas:
        if candidata.lower() in normalizadas:
            return normalizadas[candidata.lower()]

    # Indicar que no se encontró ninguna columna compatible
    return None


def extraer_fechas(df, archivo):
    """
    Extrae las fechas de una fuente de datos.

    Primero busca una columna que contenga fechas completas.
    Si no existe, intenta construirlas a partir de las columnas
    de año y mes. La función genera un error si no puede obtener
    fechas válidas de forma verificable.
    """

    # Buscar una columna temporal utilizando los nombres conocidos
    columna_fecha = encontrar_columna(df, COLUMNAS_FECHA)

    if columna_fecha is None:

        # Buscar columnas con nombres alternativos que incluyan
        # palabras relacionadas con fechas o marcas de tiempo.
        candidatas = [
            col for col in df.columns
            if (
                "fecha" in str(col).lower()
                or "date" in str(col).lower()
                or "datetime" in str(col).lower()
            )
        ]

        # Utilizar la primera coincidencia si existe alguna
        if candidatas:
            columna_fecha = candidatas[0]

    # Si se encontró una columna temporal, convertirla a datetime
    if columna_fecha is not None:
        fechas = pd.to_datetime(
            df[columna_fecha],
            errors="coerce"
        )

        # Exigir que todas las fechas puedan convertirse correctamente
        exigir(
            fechas.notna().all(),
            f"{archivo}: hay fechas vacías o inválidas "
            f"en la columna {columna_fecha}."
        )

        return fechas

    # Si no existe una columna de fecha, buscar columnas de año y mes
    columna_anio = encontrar_columna(df, COLUMNAS_ANIO)
    columna_mes = encontrar_columna(df, COLUMNAS_MES)

    if columna_anio is not None and columna_mes is not None:

        # Convertir año y mes a números para poder construir fechas
        anio = pd.to_numeric(df[columna_anio], errors="coerce")
        mes = pd.to_numeric(df[columna_mes], errors="coerce")

        # Comprobar que todos los años y meses sean numéricos
        exigir(
            anio.notna().all() and mes.notna().all(),
            f"{archivo}: año o mes inválido."
        )

        # Validar que los meses estén entre enero y diciembre
        exigir(
            mes.between(1, 12).all(),
            f"{archivo}: hay meses fuera del rango 1-12."
        )

        # Construir una fecha utilizando el primer día de cada mes
        fechas = pd.to_datetime(
            {
                "year": anio.astype(int),
                "month": mes.astype(int),
                "day": 1,
            },
            errors="coerce"
        )

        # Comprobar que las fechas construidas sean válidas
        exigir(
            fechas.notna().all(),
            f"{archivo}: no se pudieron construir las fechas."
        )

        return fechas

    # Detener la auditoría si no existe una forma verificable
    # de recuperar las fechas del archivo.
    raise ValueError(
        f"{archivo}: no se encontró una columna de fecha "
        "ni una combinación de año y mes. "
        f"Columnas disponibles: {list(df.columns)}"
    )


def validar_fechas_fuente(path, inicio, fin_exclusivo):
    """
    Comprueba que una fuente temporal contenga únicamente
    observaciones dentro del periodo permitido.

    Parámetros:
        path: ruta del archivo que se auditará.
        inicio: fecha inicial incluida en el intervalo.
        fin_exclusivo: primera fecha que queda fuera del intervalo.

    También muestra un resumen del periodo detectado.
    """

    # Cargar el archivo y extraer sus fechas
    df = leer_csv(path)
    fechas = extraer_fechas(df, path.name)

    # Identificar registros anteriores al inicio del ciclo
    fuera_inicio = fechas < inicio

    # Identificar registros que alcanzan o superan el límite exclusivo
    fuera_fin = fechas >= fin_exclusivo

    # Identificar registros que no pertenecen al año 2025
    anio_incorrecto = fechas.dt.year != 2025

    # Combinar las condiciones que indican una posible fuga temporal
    problemas = fuera_inicio | fuera_fin | anio_incorrecto

    # Mostrar el resumen temporal del archivo
    print(f"\nFuente temporal: {path.name}")
    print(f"  Registros: {len(df)}")
    print(f"  Fecha mínima: {fechas.min().date()}")
    print(f"  Fecha máxima: {fechas.max().date()}")
    print(f"  Fuera del periodo permitido: {int(problemas.sum())}")

    # Detener el proceso si existen observaciones fuera del periodo
    exigir(
        not problemas.any(),
        f"Fuga temporal en {path.name}: hay registros "
        f"fuera del periodo {inicio.date()} a "
        f"{(fin_exclusivo - pd.Timedelta(days=1)).date()}."
    )

    print("[OK] Fechas de la fuente dentro del límite.")

    return df


def validar_fechas_master(df):
    """
    Verifica que las fechas de las características fenológicas
    pertenezcan al ciclo agrícola de 2025.

    Se revisan las columnas cuyo nombre contiene peak_date.
    """

    print("\nFechas fenológicas del master")

    # Identificar las columnas que contienen fechas de pico fenológico
    columnas_fecha = [
        col for col in df.columns
        if "peak_date" in str(col).lower()
    ]

    # Exigir que exista al menos una columna de fechas de pico
    exigir(
        len(columnas_fecha) > 0,
        "No se encontraron columnas peak_date en features_master."
    )

    # Validar cada columna de fechas de pico por separado
    for columna in columnas_fecha:

        # Convertir los valores a fechas y detectar los valores inválidos
        fechas = pd.to_datetime(df[columna], errors="coerce")
        presentes = fechas.notna()

        # Mostrar la cantidad de fechas válidas y vacías
        print(f"\n{columna}:")
        print(f"  Fechas válidas: {int(presentes.sum())}")
        print(f"  Fechas vacías: {int((~presentes).sum())}")

        # Exigir que todas las parcelas tengan una fecha válida
        exigir(
            presentes.all(),
            f"{columna} contiene fechas vacías o inválidas."
        )

        # Identificar fechas anteriores o posteriores al ciclo permitido
        fuera_ciclo = (
            (fechas < CYCLE_START)
            | (fechas > DATA_CUTOFF)
        )

        # Detener la auditoría si alguna fecha está fuera del ciclo
        exigir(
            not fuera_ciclo.any(),
            f"{columna} contiene fechas fuera del ciclo "
            "2025-04-01 a 2025-10-31."
        )

        # Mostrar el intervalo temporal encontrado
        print(
            f"  Periodo: {fechas.min().date()} → "
            f"{fechas.max().date()}"
        )
        print("[OK] Fechas dentro del ciclo.")

    return True


def validar_nan_master(df):
    """
    Comprueba que los valores faltantes del archivo maestro
    coincidan exactamente con los casos documentados en NAN_ESPERADOS.
    """

    # Crear un conjunto para registrar cada combinación de parcela
    # y columna donde se encuentre un valor faltante.
    faltantes = set()

    # Obtener las posiciones de todas las celdas que contienen NaN
    for fila, columna in zip(*np.where(df.isna().to_numpy())):

        # Registrar el identificador de parcela y el nombre de columna
        faltantes.add(
            (str(df.iloc[fila]["parcel_id"]), df.columns[columna])
        )

    # Identificar los valores faltantes que no están documentados
    inesperados = faltantes - NAN_ESPERADOS

    print("\nValores faltantes del master")
    print(f"NaN encontrados: {len(faltantes)}")

    # Mostrar los casos detectados para facilitar su revisión
    if faltantes:
        print(f"NaN documentados presentes: {sorted(faltantes)}")

    # Rechazar la auditoría si existe algún NaN inesperado
    exigir(
        not inesperados,
        f"Hay NaN no documentados: {sorted(inesperados)}"
    )

    print("[OK] No existen NaN fuera de los casos documentados.")


def validar_sin_infinitos(df, nombre):
    """
    Comprueba que las columnas numéricas no contengan valores
    positivos o negativos infinitos.
    """

    # Seleccionar únicamente las columnas numéricas del DataFrame
    numericos = df.select_dtypes(include=[np.number])

    # Contar los valores infinitos de las columnas seleccionadas
    infinitos = int(np.isinf(numericos.to_numpy()).sum())

    print(f"{nombre}: infinitos = {infinitos}")

    # Detener la auditoría si se encuentra algún valor infinito
    exigir(
        infinitos == 0,
        f"{nombre} contiene valores infinitos."
    )


def validar_ids(df, ids_referencia, nombre):
    """
    Comprueba que el dataset tenga identificadores válidos,
    únicos y coincidentes con el conjunto de referencia.
    """

    # Verificar que exista la columna de identificación de parcelas
    exigir(
        "parcel_id" in df.columns,
        f"{nombre} no tiene la columna parcel_id."
    )

    # Convertir los identificadores a texto para compararlos
    ids = df["parcel_id"].astype(str)

    # Comprobar que no existan identificadores vacíos o nulos.
    # Esta validación conserva la lógica original del script.
    exigir(
        ids.notna().all(),
        f"{nombre} contiene parcel_id vacío."
    )

    # Exigir que cada identificador aparezca una sola vez
    exigir(
        ids.is_unique,
        f"{nombre} contiene IDs duplicados."
    )

    # Comparar los IDs del archivo con los del maestro de parcelas
    exigir(
        set(ids) == ids_referencia,
        f"Los IDs de {nombre} no coinciden con parcel_master."
    )


def validar_corte(nombre_corte, mes_limite, ids_referencia):
    """
    Audita el dataset de características de un corte temporal.

    Comprueba los identificadores, el número de filas, los valores
    faltantes, los infinitos, las columnas potencialmente relacionadas
    con el objetivo y las fechas de las fuentes satelitales y climáticas.
    """

    print(f"\nAuditoría del corte: {nombre_corte.upper()}")

    # Construir la ruta del archivo de características del corte actual
    path_features = (
        FEATURES_DIR /
        f"features_master_corte_{nombre_corte}.csv"
    )

    # Cargar el archivo y validar sus columnas
    df = leer_csv(path_features)

    # Comprobar que los IDs sean únicos y coincidan con la referencia
    validar_ids(df, ids_referencia, path_features.name)

    # Verificar que exista una fila por cada parcela de referencia
    exigir(
        len(df) == len(ids_referencia),
        f"{path_features.name}: número de filas incorrecto."
    )

    # Comprobar que el dataset del corte no tenga valores faltantes
    exigir(
        not df.isna().any().any(),
        f"{path_features.name} contiene NaN."
    )

    # Verificar que las columnas numéricas no contengan infinitos
    validar_sin_infinitos(df, path_features.name)

    # Buscar nombres de columnas que puedan indicar información
    # del futuro o variables que revelen el rendimiento objetivo.
    columnas_sospechosas = [
        col for col in df.columns
        if any(
            termino in str(col).lower()
            for termino in (
                "future",
                "target",
                "yield_real",
                "rendimiento_real",
                "rendimiento_t_ha",
            )
        )
    ]

    # Rechazar el dataset si se encuentran columnas sospechosas
    exigir(
        not columnas_sospechosas,
        f"{path_features.name} contiene columnas "
        f"potencialmente relacionadas con el target: "
        f"{columnas_sospechosas}"
    )

    # Calcular el primer día del mes siguiente al corte.
    # Este valor funciona como límite temporal exclusivo.
    fin_exclusivo = pd.Timestamp(
        year=2025,
        month=mes_limite,
        day=1
    ) + pd.offsets.MonthBegin(1)

    # Construir las rutas de los archivos satelital y climático
    # generados previamente para el corte actual.
    path_satellite = PRED_DIR / f"sentinel2_corte_{nombre_corte}.csv"
    path_climate = PRED_DIR / f"climate_corte_{nombre_corte}.csv"

    # Verificar que las fechas satelitales estén dentro del intervalo
    # permitido para el corte.
    validar_fechas_fuente(
        path_satellite,
        CYCLE_START,
        fin_exclusivo
    )

    # Verificar que las fechas climáticas estén dentro del intervalo
    # temporal general establecido para el corte.
    validar_fechas_fuente(
        path_climate,
        CYCLE_START,
        fin_exclusivo
    )

    print(
        f"[OK] Corte {nombre_corte}: "
        f"sin NaN, infinitos ni columnas de target."
    )

    return df


def main():
    """
    Ejecuta todas las comprobaciones de la auditoría P1.13.

    Valida los archivos maestros, las particiones de datos, los valores
    faltantes, las fechas fenológicas, la separación del rendimiento
    objetivo y la consistencia de los datasets de predicción temprana.
    """

    print("P1.13 — Auditoría temporal y prevención de Data Leakage")
    print(f"Ciclo: {CYCLE_START.date()} a {DATA_CUTOFF.date()}")

    # Leer el archivo de características completo y el maestro de parcelas
    df_master = leer_csv(MASTER_PATH)
    df_parcel = leer_csv(PARCEL_PATH)

    # Mostrar las dimensiones de ambos archivos
    print(f"\nMaster: {df_master.shape}")
    print(f"Parcelas: {df_parcel.shape}")

    # Exigir que el maestro de características contenga 197 parcelas
    exigir(
        len(df_master) == 197,
        "features_master debe contener 197 parcelas."
    )

    # Verificar que ambos archivos tengan el identificador requerido
    exigir(
        "parcel_id" in df_master.columns
        and "parcel_id" in df_parcel.columns,
        "Falta parcel_id en el master o parcel_master."
    )

    # Construir los conjuntos de IDs para comparar ambos archivos
    ids_master = set(df_master["parcel_id"].astype(str))
    ids_parcel = set(df_parcel["parcel_id"].astype(str))

    # Comprobar que los dos archivos contengan las mismas parcelas
    exigir(
        ids_master == ids_parcel,
        "Los IDs de features_master y parcel_master no coinciden."
    )

    # Verificar que no existan identificadores repetidos en el master
    exigir(
        df_master["parcel_id"].astype(str).is_unique,
        "features_master contiene IDs duplicados."
    )

    # Comprobar que todos los nombres de columna sean únicos
    exigir(
        df_master.columns.is_unique,
        "features_master contiene columnas duplicadas."
    )

    print("[OK] IDs y estructura del master.")

    # Comprobar que el master incluya la columna que identifica
    # si cada parcela pertenece a entrenamiento o predicción.
    exigir(
        "dataset_split" in df_master.columns,
        "Falta dataset_split en features_master."
    )

    # Obtener las categorías de partición presentes en el archivo
    splits = set(df_master["dataset_split"].dropna().unique())

    # Exigir que solo existan las dos particiones esperadas
    exigir(
        splits == {"ENTRENAMIENTO", "PREDICCION"},
        f"Particiones inesperadas: {splits}"
    )

    # Mostrar cuántas parcelas pertenecen a cada partición
    print("\nDistribución de particiones:")
    print(df_master["dataset_split"].value_counts().to_string())

    print("[OK] Particiones de entrenamiento y predicción.")

    # Comprobar que los únicos NaN del master sean los documentados
    validar_nan_master(df_master)

    # Comprobar que el master no contenga valores infinitos
    validar_sin_infinitos(df_master, "features_master")

    # Verificar que las fechas de pico estén dentro del ciclo agrícola
    validar_fechas_master(df_master)

    # Revisar los nombres de las columnas para detectar variables
    # que puedan revelar el valor real que el modelo debe predecir.
    columnas_target = [
        col for col in df_master.columns
        if any(
            termino in str(col).lower()
            for termino in (
                "rendimiento_t_ha",
                "rendimiento_real",
                "yield_real",
                "target",
            )
        )
    ]

    # El master de características no debe contener estas columnas
    exigir(
        not columnas_target,
        f"El master contiene columnas de target: {columnas_target}"
    )

    print("\n[OK] No se encontraron columnas de rendimiento objetivo.")

    # Si existe el archivo de objetivos, comprobar que contenga
    # los mismos identificadores de parcela que el maestro.
    # La ausencia del archivo se reporta como advertencia.
    if TARGET_PATH.exists():
        df_target = leer_csv(TARGET_PATH)

        # Verificar que el archivo de rendimiento tenga parcel_id
        exigir(
            "parcel_id" in df_target.columns,
            "El archivo de targets no contiene parcel_id."
        )

        # Comprobar que los identificadores coincidan con el maestro
        exigir(
            set(df_target["parcel_id"].astype(str)) == ids_parcel,
            "Los IDs de rendimiento.csv no coinciden con parcel_master."
        )

        print("[OK] targets/rendimiento.csv mantiene los IDs de parcelas.")
    else:
        print(
            "[AVISO] No existe targets/rendimiento.csv; "
            "no se pudo comprobar su separación."
        )

    # Guardar el esquema del primer corte para compararlo con
    # los siguientes y comprobar que todos tengan las mismas columnas
    # en el mismo orden.
    columnas_referencia = None

    for nombre, mes in CORTES.items():

        # Validar el dataset correspondiente al mes actual
        df_corte = validar_corte(nombre, mes, ids_parcel)

        # Utilizar las columnas del primer corte como referencia
        if columnas_referencia is None:
            columnas_referencia = list(df_corte.columns)
        else:

            # Detener la auditoría si cambia el esquema entre cortes
            exigir(
                list(df_corte.columns) == columnas_referencia,
                f"El esquema del corte {nombre} no coincide "
                "con los demás cortes."
            )

    # Mostrar que todas las comprobaciones terminaron correctamente
    print("\nP1.13 completada — Auditoría superada")
    print("Se validaron IDs, valores, fechas fenológicas,")
    print("fechas de los cortes y separación del rendimiento.")

if __name__ == "__main__":
    main()