// ============================================================
// Datos mock para Cebada360
// Todas las parcelas tienen la misma estructura para evitar
// errores de "Cannot read properties of undefined".
// ============================================================

// ---------- Base común ----------
const parcelaBase = {
  municipio: 'Tlaxco',
  estado: 'Tlaxcala',
  superficie_ha: 3.0,
  produccion_potencial_t: 14.0,
  rango_probable: [4.0, 5.0],
  confianza: 'media',
  confianza_pct: 75,
  riesgo: 'medio',
  ood_flag: false,
  corte_temporal: 'octubre 2025',
  shap: [],
  narrativa: 'Sin narrativa disponible para esta parcela.',
};

// ---------- Helper: SHAP escalado ----------
const shapEjemplo = (rv = 1.0) => [
  { categoria: 'vigor',          etiqueta: 'Vigor de la planta', valor:  0.55 * rv },
  { categoria: 'clima',          etiqueta: 'Lluvia acumulada',   valor:  0.27 * rv },
  { categoria: 'humedad',        etiqueta: 'Humedad del suelo',  valor:  0.14 * rv },
  { categoria: 'estres_hidrico', etiqueta: 'Estrés hídrico',     valor: -0.06 * rv },
  { categoria: 'topografia',     etiqueta: 'Pendiente',          valor:  0.03 * rv },
];

// ---------- Helper: cortes temporales ----------
export function generarCortes(final) {
  return [
    { corte: 'junio',        rendimiento_t_ha: +(final * 0.81).toFixed(2), rmse_estimado: 0.72 },
    { corte: 'julio-agosto', rendimiento_t_ha: +(final * 0.91).toFixed(2), rmse_estimado: 0.55 },
    { corte: 'septiembre',   rendimiento_t_ha: +(final * 0.97).toFixed(2), rmse_estimado: 0.46 },
    { corte: 'octubre',      rendimiento_t_ha: +final.toFixed(2),          rmse_estimado: 0.42 },
  ];
}

// ============================================================
// Parcelas
// ============================================================
export const parcelasMock = [
  {
    ...parcelaBase,
    id: 'AGC_042',
    codigo: '042',
    superficie_ha: 3.1,
    rendimiento_t_ha: 4.85,
    produccion_potencial_t: 15.0,
    rango_probable: [4.51, 5.19],
    confianza: 'alta',
    confianza_pct: 88,
    riesgo: 'bajo',
    shap: shapEjemplo(1.0),
    narrativa:
      'Buena humedad y un vigor sostenido durante todo el ciclo. Se parece mucho a parcelas vecinas con alto rendimiento.',
  },
  {
    ...parcelaBase,
    id: 'AGC_017',
    codigo: '017',
    municipio: 'Tlaxco',
    superficie_ha: 2.4,
    rendimiento_t_ha: 3.92,
    produccion_potencial_t: 9.4,
    rango_probable: [3.55, 4.28],
    confianza: 'media',
    confianza_pct: 72,
    riesgo: 'medio',
    shap: shapEjemplo(0.8),
    narrativa:
      'Vigor moderado con buena respuesta a la lluvia acumulada. El estrés hídrico en junio limitó el potencial.',
  },
  {
    ...parcelaBase,
    id: 'AGC_088',
    codigo: '088',
    municipio: 'Tlaxco',
    superficie_ha: 4.2,
    rendimiento_t_ha: 5.10,
    produccion_potencial_t: 21.4,
    rango_probable: [4.75, 5.45],
    confianza: 'alta',
    confianza_pct: 91,
    riesgo: 'bajo',
    shap: shapEjemplo(1.15),
    narrativa:
      'Parcela con vigor excepcional y sin señales de estrés hídrico durante el ciclo. Es la más productiva del grupo vecino.',
  },
  {
    ...parcelaBase,
    id: 'AGC_103',
    codigo: '103',
    municipio: 'Tlaxco',
    superficie_ha: 3.8,
    rendimiento_t_ha: 4.45,
    produccion_potencial_t: 16.9,
    rango_probable: [4.10, 4.80],
    confianza: 'media',
    confianza_pct: 78,
    riesgo: 'medio',
    shap: shapEjemplo(0.9),
    narrativa:
      'Buen desempeño general con una ligera caída de vigor al final del ciclo. Sensible a la variabilidad térmica.',
  },
  {
    ...parcelaBase,
    id: 'AGC_131',
    codigo: '131',
    municipio: 'Tlaxco',
    superficie_ha: 2.9,
    rendimiento_t_ha: 4.72,
    produccion_potencial_t: 13.7,
    rango_probable: [4.38, 5.06],
    confianza: 'alta',
    confianza_pct: 85,
    riesgo: 'bajo',
    shap: shapEjemplo(1.0),
    narrativa:
      'Rendimiento alto sostenido por humedad favorable durante el llenado de grano.',
  },
  {
    ...parcelaBase,
    id: 'AGC_156',
    codigo: '156',
    municipio: 'Tlaxco',
    superficie_ha: 3.5,
    rendimiento_t_ha: 4.10,
    produccion_potencial_t: 14.35,
    rango_probable: [3.60, 4.60],
    confianza: 'baja',
    confianza_pct: 62,
    riesgo: 'alto',
    ood_flag: true,
    shap: shapEjemplo(0.7),
    narrativa:
      'Predicción con incertidumbre alta: el patrón temporal se parece poco a las parcelas de entrenamiento. Conviene revisarla con cautela.',
  },
  {
    ...parcelaBase,
    id: 'AGC_179',
    codigo: '179',
    municipio: 'Tlaxco',
    superficie_ha: 3.2,
    rendimiento_t_ha: 3.65,
    produccion_potencial_t: 11.7,
    rango_probable: [3.20, 4.10],
    confianza: 'media',
    confianza_pct: 70,
    riesgo: 'alto',
    shap: shapEjemplo(0.6),
    narrativa:
      'Señales de estrés hídrico en etapa crítica reducen la estimación final. La pendiente también penaliza la retención de agua.',
  },
];

// ============================================================
// Contexto municipal
// ============================================================
export const municipiosMock = {
  Tlaxco: {
    municipio: 'Tlaxco',
    estado: 'Tlaxcala',
    n_parcelas: 42,
    rendimiento_promedio_t_ha: 4.32,
    superficie_total_ha: 128.4,
    produccion_total_t: 554.7,
    distribucion_riesgo: { bajo: 0.62, medio: 0.28, alto: 0.10 },
    factores_limitantes: [
      'Estrés hídrico en junio',
      'Pendiente pronunciada',
      'Baja retención de suelo',
    ],
  },
  Huamantla: {
    municipio: 'Huamantla',
    estado: 'Tlaxcala',
    n_parcelas: 38,
    rendimiento_promedio_t_ha: 4.65,
    superficie_total_ha: 142.1,
    produccion_total_t: 660.8,
    distribucion_riesgo: { bajo: 0.74, medio: 0.20, alto: 0.06 },
    factores_limitantes: ['Granizo tardío', 'Variabilidad térmica'],
  },
  Atlangatepec: {
    municipio: 'Atlangatepec',
    estado: 'Tlaxcala',
    n_parcelas: 24,
    rendimiento_promedio_t_ha: 3.88,
    superficie_total_ha: 89.6,
    produccion_total_t: 347.6,
    distribucion_riesgo: { bajo: 0.42, medio: 0.38, alto: 0.20 },
    factores_limitantes: [
      'Déficit hídrico recurrente',
      'Suelo erosionado',
      'Baja fertilidad',
    ],
  },
  Nanacamilpa: {
    municipio: 'Nanacamilpa',
    estado: 'Tlaxcala',
    n_parcelas: 18,
    rendimiento_promedio_t_ha: 4.10,
    superficie_total_ha: 61.3,
    produccion_total_t: 251.3,
    distribucion_riesgo: { bajo: 0.55, medio: 0.33, alto: 0.12 },
    factores_limitantes: ['Nubosidad persistente', 'Pendiente moderada'],
  },
  Terrenate: {
    municipio: 'Terrenate',
    estado: 'Tlaxcala',
    n_parcelas: 15,
    rendimiento_promedio_t_ha: 3.72,
    superficie_total_ha: 48.9,
    produccion_total_t: 181.9,
    distribucion_riesgo: { bajo: 0.38, medio: 0.40, alto: 0.22 },
    factores_limitantes: [
      'Estrés hídrico severo en julio',
      'Parcela con historial de bajo vigor',
    ],
  },
  // Municipios con muestra chica (para probar el filtro n >= 5)
  SanJoséTeacalco: {
    municipio: 'San José Teacalco',
    estado: 'Tlaxcala',
    n_parcelas: 3,
    rendimiento_promedio_t_ha: 4.20,
    superficie_total_ha: 9.4,
    produccion_total_t: 39.5,
    distribucion_riesgo: { bajo: 0.60, medio: 0.30, alto: 0.10 },
    factores_limitantes: ['Muestra insuficiente'],
  },
};

// ============================================================
// Cortes temporales precalculados (opcional)
// Si una parcela no está aquí, el repo los genera con generarCortes()
// ============================================================
export const cortesMock = {
  AGC_042: [
    { corte: 'junio',        rendimiento_t_ha: 3.95, rmse_estimado: 0.72 },
    { corte: 'julio-agosto', rendimiento_t_ha: 4.42, rmse_estimado: 0.55 },
    { corte: 'septiembre',   rendimiento_t_ha: 4.71, rmse_estimado: 0.46 },
    { corte: 'octubre',      rendimiento_t_ha: 4.85, rmse_estimado: 0.42 },
  ],
};

// ============================================================
// Resumen global para el dashboard
// ============================================================
export const resumenGlobalMock = {
  n_parcelas: 197,
  n_train: 138,
  n_prediccion: 59,
  superficie_total_ha: 842.6,
  produccion_potencial_total_t: 3452.1,
  distribucion_riesgo: { bajo: 0.62, medio: 0.28, alto: 0.10 },
  corte_temporal: 'hasta 2025-09-15',
};

// ============================================================
// Métricas del modelo (para /modelo cuando toque)
// ============================================================
export const metricasModeloMock = {
  modelo_oficial: 'Gradient Boosting + features fenológicos',
  rmse: 0.42,
  mae: 0.31,
  r2: 0.71,
  cv_aleatoria: { rmse: 0.42, mae: 0.31, r2: 0.71, std: 0.05 },
  cv_espacial:  { rmse: 0.58, mae: 0.44, r2: 0.53, std: 0.09 },
  cortes_temporales: [
    { corte: 'junio',        rmse: 0.72, mae: 0.55, r2: 0.38, n_features: 18 },
    { corte: 'julio-agosto', rmse: 0.55, mae: 0.42, r2: 0.54, n_features: 26 },
    { corte: 'septiembre',   rmse: 0.46, mae: 0.35, r2: 0.65, n_features: 31 },
    { corte: 'octubre',      rmse: 0.42, mae: 0.31, r2: 0.71, n_features: 34 },
  ],
  ablacion: [
    { familia: 'Vegetación',  rmse: 0.61, delta_rmse: 0.19 },
    { familia: 'Clima',       rmse: 0.55, delta_rmse: 0.13 },
    { familia: 'Topografía',  rmse: 0.72, delta_rmse: 0.30 },
    { familia: 'Fusión',      rmse: 0.42, delta_rmse: 0.00 },
  ],
};