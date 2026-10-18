"""
Tarea: P1.15 — Validación final y reproducibilidad
Proyecto: Cebada360
"""

from pathlib import Path
import os
import subprocess
import sys
import pandas as pd
import numpy as np


# Rutas principales del proyecto y de los scripts de preparación.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = PROJECT_ROOT / "scripts_limpieza"
WORK_DIR = Path(os.environ.get("CEBADA_PREP_WORKDIR", PROJECT_ROOT)).resolve()
CLEAN_DIR = WORK_DIR / "DATASET_RETO_AGRO_2026_LIMPIO"

# Scripts que se ejecutan para reconstruir y auditar los datos.
BUILD_SCRIPT = SCRIPTS_DIR / "build_features.py"
TARGET_SCRIPT = SCRIPTS_DIR / "p1_16.py"
AUDIT_SCRIPT = SCRIPTS_DIR / "p1_13.py"

# Cantidades esperadas para comprobar la estructura de los archivos.
EXPECTED_PARCELS = 197
EXPECTED_MASTER_COLUMNS = 215
EXPECTED_CUT_COLUMNS = 33

# Casos de valores NaN permitidos y previamente documentados.
NAN_ESPERADOS = {
    ("AGC_043", "planet_ndvi_decay_rate"),
    ("AGC_175", "planet_ndvi_decay_rate"),
}

# Meses para los que se generan los conjuntos de predicción temprana.
CORTES = [
    "junio",
    "julio",
    "agosto",
    "septiembre",
    "octubre",
]

# Archivos que deben existir después de reconstruir el pipeline.
ARCHIVOS_REQUERIDOS = [
    CLEAN_DIR / "parcel_master.csv",
    CLEAN_DIR / "topography_master.csv",
    CLEAN_DIR / "climate_timeseries.csv",

    CLEAN_DIR / "sensores" / "sentinel2_timeseries.csv",
    CLEAN_DIR / "sensores" / "landsat_timeseries.csv",
    CLEAN_DIR / "sensores" / "planet_timeseries.csv",

    CLEAN_DIR / "satellite_features.csv",
    CLEAN_DIR / "fenologia_features.csv",
    CLEAN_DIR / "climate_features.csv",
    CLEAN_DIR / "features_master.csv",

    CLEAN_DIR / "targets" / "rendimiento.csv",

    *[
        CLEAN_DIR / "prediccion_temprana" / f"sentinel2_corte_{c}.csv"
        for c in CORTES
    ],
    *[
        CLEAN_DIR / "prediccion_temprana" / f"climate_corte_{c}.csv"
        for c in CORTES
    ],
    *[
        CLEAN_DIR / "prediccion_temprana" / "features"
        / f"features_master_corte_{c}.csv"
        for c in CORTES
    ],
]


def ejecutar_script(ruta, descripcion):
    """
    Ejecuta un script de Python desde la raíz del proyecto.

    Comprueba que el archivo exista y verifica el código de salida
    del proceso para determinar si terminó correctamente.
    """
    print(f"\n{descripcion}")

    # Verificar que el script solicitado exista.
    if not ruta.exists():
        print(f"[ERROR] No existe el script: {ruta}")
        return False

    # Ejecutar el script usando el mismo intérprete de Python.
    resultado = subprocess.run(
        [sys.executable, str(ruta)],
        cwd=WORK_DIR
    )

    # Un código distinto de cero indica que ocurrió un error.
    if resultado.returncode != 0:
        print(f"[ERROR] Falló {ruta.name}, código {resultado.returncode}.")
        return False

    print(f"[OK] {ruta.name} terminó correctamente.")
    return True


def validar_archivos():
    """
    Comprueba que todos los entregables requeridos existan
    y que ninguno esté vacío.

    Devuelve True si todos los archivos pasan las comprobaciones.
    """
    print("\nVerificación de entregables")

    faltantes = []

    # Revisar cada archivo requerido por el pipeline.
    for archivo in ARCHIVOS_REQUERIDOS:
        if not archivo.is_file():
            print(f"[FALTA] {archivo.relative_to(WORK_DIR)}")
            faltantes.append(archivo)

        elif archivo.stat().st_size == 0:
            print(f"[ERROR] Archivo vacío: {archivo.name}")
            faltantes.append(archivo)

        else:
            print(
                f"[OK] {archivo.relative_to(WORK_DIR)} "
                f"({archivo.stat().st_size / 1024:.2f} KB)"
            )

    # Informar si se encontraron archivos ausentes o vacíos.
    if faltantes:
        print(f"\n[ERROR] Entregables ausentes o vacíos: {len(faltantes)}")
        return False

    print("\n[OK] Todos los entregables existen y no están vacíos.")
    return True


def leer_csv(ruta):
    """
    Lee un archivo CSV conservando como texto los identificadores.

    Evita que pandas interprete los IDs como valores numéricos
    y altere su representación.
    """
    return pd.read_csv(
        ruta,
        dtype={"parcel_id": str, "ID_POLIGONO": str}
    )


def validar_estructura(
    df,
    nombre,
    filas=EXPECTED_PARCELS,
    columnas=None
):
    """
    Valida la estructura general de un DataFrame.

    Comprueba el número de filas y columnas cuando se especifican,
    la unicidad de los nombres de columnas, los identificadores
    de parcela y la ausencia de valores infinitos.
    """
    ok = True

    print(f"\n{nombre}")
    print(f"Dimensiones: {df.shape}")

    # Comprobar el número esperado de registros.
    if filas is not None and len(df) != filas:
        print(f"[ERROR] Se esperaban {filas} filas.")
        ok = False

    # Comprobar el número esperado de variables.
    if columnas is not None and len(df.columns) != columnas:
        print(f"[ERROR] Se esperaban {columnas} columnas.")
        ok = False

    # Evitar nombres de columnas repetidos.
    if not df.columns.is_unique:
        print("[ERROR] Hay nombres de columnas duplicados.")
        ok = False
    else:
        print("[OK] Columnas únicas.")

    # Verificar que exista el identificador principal.
    if "parcel_id" not in df.columns:
        print("[ERROR] Falta parcel_id.")
        return False

    ids = df["parcel_id"].astype("string")

    # Los identificadores deben estar completos y ser únicos.
    if ids.isna().any() or ids.duplicated().any():
        print("[ERROR] Hay IDs vacíos o duplicados.")
        ok = False
    else:
        print("[OK] IDs únicos y no nulos.")

    # Buscar valores positivos o negativos infinitos en columnas numéricas.
    numericos = df.select_dtypes(include=[np.number])
    infinitos = int(np.isinf(numericos.to_numpy()).sum())

    if infinitos:
        print(f"[ERROR] Se encontraron {infinitos} infinitos.")
        ok = False
    else:
        print("[OK] Sin valores infinitos.")

    return ok


def validar_master():
    """
    Valida el archivo features_master.csv.

    Comprueba sus dimensiones, identificadores, valores faltantes,
    distribución de las particiones y posibles variables relacionadas
    con el rendimiento objetivo.
    """
    ruta = CLEAN_DIR / "features_master.csv"
    df = leer_csv(ruta)

    # Validar las dimensiones y la estructura general del archivo maestro.
    ok = validar_estructura(
        df,
        "features_master.csv",
        filas=EXPECTED_PARCELS,
        columnas=EXPECTED_MASTER_COLUMNS
    )

    # Recopilar los NaN identificando la parcela y la columna afectada.
    nan_encontrados = set()

    for indice, columna in zip(*np.where(df.isna().to_numpy())):
        parcel_id = str(df.iloc[indice]["parcel_id"])
        nan_encontrados.add((parcel_id, df.columns[columna]))

    # Comparar los NaN encontrados con los casos documentados.
    nan_inesperados = nan_encontrados - NAN_ESPERADOS

    print(f"NaN encontrados: {len(nan_encontrados)}")

    if nan_encontrados:
        print(f"NaN documentados presentes: {sorted(nan_encontrados)}")

    if nan_inesperados:
        print(f"[ERROR] NaN no documentados: {sorted(nan_inesperados)}")
        ok = False
    else:
        print("[OK] No hay NaN fuera de los casos documentados.")

    # Comprobar que exista la columna que identifica cada partición.
    if "dataset_split" not in df.columns:
        print("[ERROR] Falta dataset_split.")
        ok = False

    else:
        # Verificar la cantidad de parcelas de entrenamiento y predicción.
        distribucion = df["dataset_split"].value_counts().to_dict()
        print(f"Distribución de particiones: {distribucion}")

        if distribucion != {"ENTRENAMIENTO": 138, "PREDICCION": 59}:
            print("[ERROR] La distribución de particiones no coincide.")
            ok = False
        else:
            print("[OK] Particiones correctas.")

    # Buscar columnas que puedan contener información del rendimiento real.
    sospechosas = [
        col for col in df.columns
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

    # El rendimiento objetivo debe mantenerse separado de las variables predictoras.
    if sospechosas:
        print(f"[ERROR] Posibles columnas objetivo en features: {sospechosas}")
        ok = False
    else:
        print("[OK] El rendimiento objetivo no está en las features.")

    return ok, df


def validar_cortes(ids_referencia):
    """
    Valida los archivos de variables para cada corte temporal.

    Comprueba sus dimensiones, IDs, valores faltantes, posibles columnas
    relacionadas con el objetivo y consistencia del esquema entre cortes.
    """
    print("\nValidación de cortes tempranos")

    todo_ok = True
    columnas_referencia = None

    # Recorrer los cortes mensuales configurados.
    for corte in CORTES:
        ruta = (
            CLEAN_DIR / "prediccion_temprana" / "features"
            / f"features_master_corte_{corte}.csv"
        )
        df = leer_csv(ruta)

        # Validar las dimensiones y la estructura del corte actual.
        ok = validar_estructura(
            df,
            f"Corte {corte}",
            filas=EXPECTED_PARCELS,
            columnas=EXPECTED_CUT_COLUMNS
        )

        # Comprobar que cada corte contenga las mismas parcelas que el master.
        ids = set(df["parcel_id"].astype(str))

        if ids != ids_referencia:
            print(f"[ERROR] IDs diferentes en el corte {corte}.")
            ok = False
        else:
            print("[OK] IDs coinciden con el master.")

        # Los archivos de predicción temprana no deben contener NaN.
        nan_total = int(df.isna().sum().sum())

        if nan_total:
            print(f"[ERROR] {nan_total} NaN en el corte {corte}.")
            ok = False
        else:
            print("[OK] Sin NaN.")

        # Detectar nombres que puedan indicar información futura o del objetivo.
        sospechosas = [
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

        if sospechosas:
            print(f"[ERROR] Columnas de target: {sospechosas}")
            ok = False

        # Todos los cortes deben mantener el mismo esquema de columnas.
        if columnas_referencia is None:
            columnas_referencia = list(df.columns)

        elif list(df.columns) != columnas_referencia:
            print(f"[ERROR] El esquema difiere en el corte {corte}.")
            ok = False

        # Registrar el resultado de las validaciones del corte.
        if ok:
            print(f"[OK] Corte {corte} validado.")
        else:
            todo_ok = False

    return todo_ok


def validar_targets(ids_referencia):
    """
    Valida el archivo separado de rendimiento objetivo.

    Comprueba que los IDs coincidan con las parcelas del master,
    que exista la variable de rendimiento y que los valores conocidos
    correspondan únicamente a las parcelas de entrenamiento.
    """
    ruta = CLEAN_DIR / "targets" / "rendimiento.csv"
    df = leer_csv(ruta)

    print("\nValidación de targets/rendimiento.csv")

    # Comprobar que el archivo tenga el identificador de parcela.
    if "parcel_id" not in df.columns:
        print("[ERROR] Falta parcel_id en targets.")
        return False

    # Comprobar que exista la columna con el rendimiento real.
    if "rendimiento_t_ha" not in df.columns:
        print("[ERROR] Falta rendimiento_t_ha en targets.")
        return False

    ids = df["parcel_id"].astype(str)

    # Verificar que los IDs sean únicos y coincidan con el conjunto de parcelas.
    if ids.duplicated().any() or set(ids) != ids_referencia:
        print("[ERROR] IDs de targets duplicados o distintos.")
        return False

    # Convertir el rendimiento a formato numérico para revisar sus valores.
    rendimiento = pd.to_numeric(df["rendimiento_t_ha"], errors="coerce")

    # Recuperar la partición asignada a cada parcela.
    splits = leer_csv(CLEAN_DIR / "parcel_master.csv")
    splits["parcel_id"] = splits["parcel_id"].astype(str)

    # Relacionar el rendimiento con la partición correspondiente.
    comprobar = pd.DataFrame({
        "parcel_id": ids,
        "rendimiento": rendimiento,
    }).merge(
        splits[["parcel_id", "dataset_split"]],
        on="parcel_id",
        how="left",
        validate="one_to_one"
    )

    entrenamiento = comprobar["dataset_split"] == "ENTRENAMIENTO"
    prediccion = comprobar["dataset_split"] == "PREDICCION"

    # Las parcelas de entrenamiento deben tener rendimiento disponible.
    if comprobar.loc[entrenamiento, "rendimiento"].isna().any():
        print("[ERROR] Hay rendimientos faltantes en entrenamiento.")
        return False

    # Las parcelas de predicción no deben tener rendimiento conocido.
    if comprobar.loc[prediccion, "rendimiento"].notna().any():
        print("[ERROR] Las parcelas de predicción tienen rendimiento conocido.")
        return False

    print("[OK] IDs correctos.")
    print("[OK] Rendimiento disponible solo para entrenamiento.")
    return True


def validar_reproducibilidad_final():
    """
    Coordina la reconstrucción y las validaciones finales de P1.15.

    Ejecuta el pipeline de variables, actualiza el archivo del objetivo,
    verifica los entregables y valida el master, los cortes tempranos,
    la separación del rendimiento y la auditoría temporal.
    """
    print("P1.15 — Validación final y reproducibilidad")
    print("Proyecto: AgroCebada / Cebada360")

    # Paso 1: reconstruir las variables y los cortes temporales.
    if not ejecutar_script(
        BUILD_SCRIPT,
        "Paso 1 — Reconstrucción del pipeline"
    ):
        print("\nP1.15 NO SUPERADA.")
        return 1

    # Paso 2: crear o actualizar el archivo separado del rendimiento.
    if not ejecutar_script(
        TARGET_SCRIPT,
        "Paso 2 — Separación del target (P1.16)"
    ):
        print("\nP1.15 NO SUPERADA.")
        return 1

    # Paso 3: comprobar que los entregables existan y no estén vacíos.
    if not validar_archivos():
        print("\nP1.15 NO SUPERADA.")
        return 1

    # Paso 4: validar el conjunto maestro de variables.
    master_ok, df_master = validar_master()

    # Obtener los IDs del master como referencia para las demás comprobaciones.
    ids_referencia = set(df_master["parcel_id"].astype(str))

    # Paso 5: validar los archivos de predicción temprana.
    cortes_ok = validar_cortes(ids_referencia)

    # Paso 6: validar la separación del rendimiento objetivo.
    targets_ok = validar_targets(ids_referencia)

    # Paso 7: ejecutar la auditoría temporal definida en P1.13.
    auditoria_ok = ejecutar_script(
        AUDIT_SCRIPT,
        "Paso final — Auditoría temporal P1.13"
    )

    # Consolidar los resultados de las comprobaciones finales.
    resultados = {
        "Entregables": True,
        "features_master": master_ok,
        "Cortes tempranos": cortes_ok,
        "Separación del rendimiento": targets_ok,
        "Auditoría temporal P1.13": auditoria_ok,
    }

    print("\nResultado final P1.15")

    for nombre, ok in resultados.items():
        print(f"[{'OK' if ok else 'ERROR'}] {nombre}")

    # La tarea se considera superada únicamente si todas las validaciones pasan.
    if all(resultados.values()):
        print("\nP1.15 COMPLETADA — VALIDACIÓN SUPERADA")
        print("La reconstrucción y las comprobaciones finalizaron correctamente.")
        return 0

    print("\nP1.15 NO SUPERADA — Revisa los errores anteriores.")
    return 1

if __name__ == "__main__":
    raise SystemExit(validar_reproducibilidad_final())
