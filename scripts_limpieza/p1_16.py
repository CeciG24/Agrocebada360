"""
Tarea: P1.16 — Preparación del target de rendimiento
Proyecto: Cebada360
"""

from pathlib import Path
import os
import pandas as pd


# Definir la raíz del proyecto y las rutas de los archivos de entrada y salida.
ROOT = Path(os.environ.get("CEBADA_PREP_WORKDIR", Path(__file__).resolve().parent.parent)).resolve()

RAW_DIR = ROOT / "DATASET_RETO_AGRO_2026"
CLEAN_DIR = ROOT / "DATASET_RETO_AGRO_2026_LIMPIO"

# Archivo original que contiene los identificadores y el rendimiento.
RAW_FILE = RAW_DIR / "ID_area_rendimiento_70_30_Reto_AgroCebada.csv"

# Archivo maestro que identifica las parcelas y su partición.
PARCEL_MASTER = CLEAN_DIR / "parcel_master.csv"

# Directorio y archivo donde se guardará el target preparado.
TARGET_DIR = CLEAN_DIR / "targets"
TARGET_FILE = TARGET_DIR / "rendimiento.csv"


print("P1.16 — Preparación del target de rendimiento")

print("\n[1] Leyendo archivos...")

# Cargar el rendimiento original y el maestro de parcelas.
df_target = pd.read_csv(RAW_FILE)
df_parcel = pd.read_csv(PARCEL_MASTER)

# Mostrar las dimensiones para comprobar que los archivos se cargaron.
print(f"[OK] Dataset original: {df_target.shape}")
print(f"[OK] parcel_master: {df_parcel.shape}")

# Se conservan el identificador de parcela y el rendimiento por hectárea.
required_target_cols = [
    "ID_POLIGONO",
    "RENDIMIENTO_T_HA"
]

# Comprobar que las columnas requeridas existan en el archivo original.
missing = [
    col for col in required_target_cols
    if col not in df_target.columns
]

if missing:
    raise ValueError(
        f"Faltan columnas en el dataset original: {missing}"
    )

# Crear una copia que contenga solamente las columnas del objetivo.
target = df_target[required_target_cols].copy()

# Renombrar las columnas para mantener el esquema del proyecto.
target = target.rename(
    columns={
        "ID_POLIGONO": "parcel_id",
        "RENDIMIENTO_T_HA": "rendimiento_t_ha"
    }
)

print("\n[2] Validando target...")

# No se permiten parcelas sin identificador.
if target["parcel_id"].isna().any():
    raise ValueError("Existen parcel_id nulos.")

# Cada parcela debe aparecer una sola vez en el archivo de rendimiento.
if target["parcel_id"].duplicated().any():
    duplicados = target[
        target["parcel_id"].duplicated(keep=False)
    ]
    print(duplicados)
    raise ValueError("Existen parcel_id duplicados.")

# Verificar que la columna de rendimiento tenga un tipo numérico.
if not pd.api.types.is_numeric_dtype(target["rendimiento_t_ha"]):
    raise ValueError(
        "RENDIMIENTO_T_HA no es una columna numérica."
    )

print("[OK] IDs únicos.")
print("[OK] parcel_id sin nulos.")
print("[OK] Rendimiento numérico.")

print("\n[3] Comparando IDs con parcel_master...")

# Convertir los identificadores en conjuntos para comparar su pertenencia.
ids_target = set(target["parcel_id"])
ids_master = set(df_parcel["parcel_id"])

# Identificar parcelas presentes en un archivo, pero ausentes en el otro.
faltan_en_master = ids_target - ids_master
faltan_en_target = ids_master - ids_target

# Detener el proceso si el target contiene parcelas que no están en el master.
if faltan_en_master:
    raise ValueError(
        f"Parcelas del target que no existen en parcel_master: "
        f"{sorted(faltan_en_master)}"
    )

# Detener el proceso si el master contiene parcelas sin registro en el target.
if faltan_en_target:
    raise ValueError(
        f"Parcelas de parcel_master que no existen en target: "
        f"{sorted(faltan_en_target)}"
    )

print("[OK] Los 197 IDs coinciden exactamente.")

print("\n[4] Verificando conjuntos...")

# Relacionar cada parcela con su rendimiento y su partición correspondiente.
# La validación one_to_one exige una relación de uno a uno entre los IDs.
merged = df_parcel[
    ["parcel_id", "dataset_split"]
].merge(
    target,
    on="parcel_id",
    how="left",
    validate="one_to_one"
)

# Separar los registros de entrenamiento y los de predicción.
entrenamiento = merged[
    merged["dataset_split"] == "ENTRENAMIENTO"
]

prediccion = merged[
    merged["dataset_split"] == "PREDICCION"
]

# Mostrar cuántas parcelas pertenecen a cada conjunto.
print(
    f"ENTRENAMIENTO: {len(entrenamiento)} parcelas"
)

print(
    f"PREDICCION:    {len(prediccion)} parcelas"
)

# Todas las parcelas de entrenamiento deben tener rendimiento conocido.
if entrenamiento["rendimiento_t_ha"].isna().any():
    raise ValueError(
        "Existen parcelas ENTRENAMIENTO sin rendimiento."
    )

# Las parcelas de predicción deben conservar el rendimiento desconocido.
if prediccion["rendimiento_t_ha"].notna().any():
    raise ValueError(
        "Existen parcelas PREDICCION con rendimiento conocido."
    )

print(
    "[OK] Las 138 parcelas de entrenamiento tienen rendimiento."
)

print(
    "[OK] Las 59 parcelas de predicción tienen rendimiento desconocido."
)

# parents permite crear también los directorios superiores necesarios.
# exist_ok evita un error cuando la carpeta ya está creada.
TARGET_DIR.mkdir(
    parents=True,
    exist_ok=True
)

# index=False evita añadir una columna con el índice de pandas.
target.to_csv(
    TARGET_FILE,
    index=False
)

print("\n[5] Archivo generado:")
print(f"    {TARGET_FILE}")

print("\nResultado P1.16")

# Informar el total de parcelas y la cantidad de rendimientos disponibles.
print(f"Total parcelas:       {len(target)}")
print(
    f"Rendimiento conocido: "
    f"{target['rendimiento_t_ha'].notna().sum()}"
)
print(
    f"Rendimiento faltante: "
    f"{target['rendimiento_t_ha'].isna().sum()}"
)

# Mostrar el rango mínimo y máximo de los rendimientos conocidos.
print(
    f"Rango rendimiento conocido: "
    f"{target['rendimiento_t_ha'].min():.2f} - "
    f"{target['rendimiento_t_ha'].max():.2f} t/ha"
)

print("\n[OK] Target preparado correctamente.")
