#!/usr/bin/env bash
# Descarga y extrae el bundle de datos en el disco de Render (/data).
# Ejecutar desde el shell de Render (dashboard → servicio → pestaña Shell):
#
#   bash scripts/setup_render_disk.sh <URL-DE-DESCARGA>
#
# El disco debe estar montado en /data (configurado en render.yaml).

set -euo pipefail

URL="${1:-}"
DISK="/data"
TMP="/tmp/cebada-deploy.tar.gz"

if [[ -z "$URL" ]]; then
  echo "Uso: bash scripts/setup_render_disk.sh <URL-DE-DESCARGA>"
  exit 1
fi

# ── Verificar que el disco esté montado ───────────────────────────────────────
if [[ ! -d "$DISK" ]]; then
  echo "Error: no se encontró $DISK. Verifica que el disco esté configurado en render.yaml."
  exit 1
fi

# ── Descargar ─────────────────────────────────────────────────────────────────
echo "Descargando bundle desde $URL ..."
curl -L --progress-bar -o "$TMP" "$URL"
echo "Descarga completa: $(du -sh "$TMP" | cut -f1)"

# ── Limpiar instalación anterior (si existe) ──────────────────────────────────
if [[ -d "$DISK/data" || -d "$DISK/delivery" ]]; then
  echo "Eliminando datos anteriores en $DISK ..."
  rm -rf "$DISK/data" "$DISK/delivery"
fi

# ── Extraer ───────────────────────────────────────────────────────────────────
echo "Extrayendo en $DISK ..."
tar -xzf "$TMP" -C "$DISK" --strip-components=1
rm -f "$TMP"

# ── Verificar estructura mínima ───────────────────────────────────────────────
REQUIRED=(
  "$DISK/data/features/features_master.csv"
  "$DISK/data/targets/rendimiento.csv"
  "$DISK/data/parcel_master.csv"
  "$DISK/delivery/integration_manifest.json"
  "$DISK/delivery/catalog.json"
  "$DISK/delivery/model"
)

echo "Verificando estructura ..."
ALL_OK=true
for f in "${REQUIRED[@]}"; do
  if [[ -e "$f" ]]; then
    echo "  ✓ $f"
  else
    echo "  ✗ FALTA: $f"
    ALL_OK=false
  fi
done

if [[ "$ALL_OK" != "true" ]]; then
  echo "Error: faltan archivos en el disco. Revisa el bundle."
  exit 1
fi

echo ""
echo "✓ Disco configurado correctamente."
echo "  Reinicia el servicio en Render para que la API cargue los datos."
echo "  Verifica en: https://<tu-servicio>.onrender.com/health"
