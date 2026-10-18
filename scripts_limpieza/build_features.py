"""
Tarea: P1.14 — Reconstrucción y validación de features
Proyecto: Cebada360
"""

from pathlib import Path
import subprocess
import sys
import pandas as pd


# Definir las rutas principales del proyecto.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = PROJECT_ROOT / "scripts_limpieza"
CLEAN_DIR = PROJECT_ROOT / "DATASET_RETO_AGRO_2026_LIMPIO"

# Establecer el periodo del ciclo agrícola utilizado para las variables.
DATA_CUTOFF = "2025-10-31"
CYCLE_START = "2025-04-01"

# Definir la ubicación del archivo maestro que se validará.
FEATURES_MASTER = CLEAN_DIR / "features_master.csv"

# Registrar los valores NaN permitidos y previamente justificados.
NAN_ESPERADOS = {
    ("AGC_043", "planet_ndvi_decay_rate"),
    ("AGC_175", "planet_ndvi_decay_rate"),
}

# Definir los scripts que deben ejecutarse para reconstruir las variables.
PIPELINE = [
    "p1_1.py",
    "p1_3.py",
    "p1_4.py",
    "p1_5.py",
    "p1_6.py",
    "p1_7.py",
    "p1_8.py",
    "p1_9.py",
    "p1_10.py",
    "p1_11.py",
    "p1_12.py",
]


def ejecutar_pipeline():
    """
    Ejecuta secuencialmente los scripts de preparación de datos.

    Comprueba que cada script exista y que termine correctamente.
    Si alguno falla, detiene la reconstrucción para evitar continuar
    con archivos que podrían estar incompletos o desactualizados.
    """
    print("AGROCEBADA — Reconstrucción de features")
    print(f"Ciclo satelital: {CYCLE_START} a {DATA_CUTOFF}")

    # Recorrer la lista de scripts respetando el orden establecido.
    for numero, nombre in enumerate(PIPELINE, start=1):
        script = SCRIPTS_DIR / nombre

        # Verificar que el archivo del script exista antes de ejecutarlo.
        if not script.is_file():
            raise FileNotFoundError(
                f"No existe el script requerido: {script}"
            )

        print(f"\n[{numero}/{len(PIPELINE)}] Ejecutando {nombre}")

        # Ejecutar el script con el mismo intérprete de Python
        # y desde la raíz del proyecto.
        resultado = subprocess.run(
            [sys.executable, str(script)],
            cwd=PROJECT_ROOT,
            check=False,
        )

        # Detener el proceso si el script devuelve un código de error.
        if resultado.returncode != 0:
            raise RuntimeError(
                f"{nombre} falló con código {resultado.returncode}. "
                "Se detuvo la reconstrucción."
            )

        print(f"[OK] {nombre}")


def validar_features_master():
    """
    Valida la estructura y la integridad de features_master.csv.

    Comprueba que existan las 197 parcelas esperadas, que los IDs
    sean únicos y no nulos, que no haya columnas duplicadas ni valores
    infinitos y que los NaN correspondan a los casos documentados.
    """
    print("\nValidación de features_master.csv")

    # Comprobar que el archivo maestro haya sido generado.
    if not FEATURES_MASTER.is_file():
        raise FileNotFoundError(
            f"No se generó {FEATURES_MASTER}"
        )

    # Leer los identificadores como texto para conservar su formato.
    df = pd.read_csv(
        FEATURES_MASTER,
        dtype={"parcel_id": "string"},
    )

    # Mostrar las dimensiones del archivo para facilitar su revisión.
    print(f"Filas: {len(df)}")
    print(f"Columnas: {len(df.columns)}")

    # Verificar que el archivo contenga las 197 parcelas esperadas.
    if len(df) != 197:
        raise ValueError(f"Se esperaban 197 filas; hay {len(df)}.")

    # Comprobar que exista la columna identificadora de las parcelas.
    if "parcel_id" not in df.columns:
        raise ValueError("Falta la columna parcel_id.")

    # Los identificadores deben estar completos.
    if df["parcel_id"].isna().any():
        raise ValueError("Hay parcel_id nulos.")

    # Cada identificador debe aparecer una sola vez.
    if df["parcel_id"].duplicated().any():
        raise ValueError("Hay parcel_id duplicados.")

    # Confirmar que existan 197 identificadores distintos.
    if df["parcel_id"].nunique() != 197:
        raise ValueError("No hay 197 parcelas únicas.")

    # Detectar nombres de columnas repetidos.
    duplicadas = df.columns[df.columns.duplicated()].tolist()

    if duplicadas:
        raise ValueError(f"Hay columnas duplicadas: {duplicadas}")

    # Seleccionar las columnas numéricas para detectar infinitos.
    numericas = df.select_dtypes(include="number")

    infinitos = int(
        numericas.isin([float("inf"), float("-inf")]).sum().sum()
    )

    if infinitos:
        raise ValueError(f"Hay {infinitos} valores infinitos.")

    # Revisar los valores faltantes y registrar cada caso
    # mediante el identificador de parcela y el nombre de la columna.
    faltantes = set()

    for columna in df.columns:
        filas_nan = df.loc[df[columna].isna(), "parcel_id"]

        for parcel_id in filas_nan:
            faltantes.add((str(parcel_id), columna))

    # Separar los NaN no documentados de los casos que ya no aparecen.
    inesperados = faltantes - NAN_ESPERADOS
    ausentes_de_justificacion = NAN_ESPERADOS - faltantes

    # Rechazar el archivo si se encuentran valores faltantes inesperados.
    if inesperados:
        raise ValueError(
            f"Hay NaN no justificados: {sorted(inesperados)}"
        )

    # Informar si algún NaN documentado dejó de aparecer en el archivo.
    if ausentes_de_justificacion:
        print(
            "[AVISO] Algunos faltantes documentados ya no aparecen: "
            f"{sorted(ausentes_de_justificacion)}"
        )

    # Mostrar el resultado de la comprobación de valores faltantes.
    if faltantes:
        print(f"[INFO] NaN justificados: {sorted(faltantes)}")
    else:
        print("[OK] Sin valores NaN.")

    # Informar que las comprobaciones de integridad finalizaron.
    print("[OK] 197 parcelas únicas.")
    print("[OK] Sin infinitos.")
    print("[OK] Sin columnas duplicadas.")
    print("[OK] Validación del archivo final completada.")


def main():
    # Reconstruir los archivos y las variables del proyecto.
    ejecutar_pipeline()

    # Validar la estructura y los valores de features_master.csv.
    validar_features_master()

    # Mostrar el resultado general del proceso.
    print("\nP1.14 — RECONSTRUCCIÓN COMPLETADA")
    print(f"Fecha límite configurada: {DATA_CUTOFF}")
    print("Revisa también la auditoría temporal de P1.13.")


if __name__ == "__main__":
    try:
        main()

    except Exception as error:
        print(f"\n[ERROR] {error}")
        sys.exit(1)