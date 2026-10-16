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
// Parcelas destacadas (escritas a mano: son las que cuenta el guion de la demo)
//   042 → riesgo bajo · 017/103 → medio · 156 → alto con alerta fuera de distribución
// ============================================================
const parcelasDestacadas = [
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
// Parcelas generadas hasta completar las 197 del reto
// Determinista: mismo resultado en cada recarga (semilla fija), así la demo es repetible.
// Los datos son de EJEMPLO; no representan parcelas reales.
// ============================================================
const TOTAL_PARCELAS = 197;

// Cuántas parcelas hay por municipio, rendimiento medio y probabilidad de riesgo [bajo, medio, alto]
const PERFIL_MUNICIPIO = {
  Tlaxco:              { n: 58, media: 4.32, riesgo: [0.62, 0.28, 0.10] },
  Huamantla:           { n: 52, media: 4.65, riesgo: [0.74, 0.20, 0.06] },
  Atlangatepec:        { n: 32, media: 3.88, riesgo: [0.42, 0.38, 0.20] },
  Nanacamilpa:         { n: 28, media: 4.10, riesgo: [0.55, 0.33, 0.12] },
  Terrenate:           { n: 24, media: 3.72, riesgo: [0.38, 0.40, 0.22] },
  'San José Teacalco': { n: 3,  media: 4.20, riesgo: [0.60, 0.30, 0.10] }, // muestra chica: prueba el filtro n ≥ 5
};

const FACTORES_MUNICIPIO = {
  Tlaxco: ['Estrés hídrico en junio', 'Pendiente pronunciada', 'Baja retención de suelo'],
  Huamantla: ['Granizo tardío', 'Variabilidad térmica'],
  Atlangatepec: ['Déficit hídrico recurrente', 'Suelo erosionado', 'Baja fertilidad'],
  Nanacamilpa: ['Nubosidad persistente', 'Pendiente moderada'],
  Terrenate: ['Estrés hídrico severo en julio', 'Parcela con historial de bajo vigor'],
  'San José Teacalco': ['Muestra insuficiente'],
};

const NARRATIVAS = {
  bajo: [
    'Vigor sostenido durante el ciclo y humedad favorable. Se parece a parcelas vecinas con buen rendimiento.',
    'Buen desarrollo en el llenado de grano; la lluvia acumulada acompañó la estimación.',
    'Rendimiento alto respaldado por un vigor constante y sin señales relevantes de estrés hídrico.',
    'Ciclo estable de principio a fin. La estimación coincide con la de parcelas cercanas de condiciones parecidas.',
  ],
  medio: [
    'Vigor moderado con buena respuesta a la lluvia. Una ligera caída hacia el final del ciclo reduce la estimación.',
    'Desempeño razonable, aunque la variabilidad térmica de la temporada añade incertidumbre.',
    'El estrés hídrico en una etapa intermedia limitó parte del potencial; el resto del ciclo fue estable.',
    'Rendimiento cercano al promedio municipal, con un rango probable algo más amplio de lo habitual.',
  ],
  alto: [
    'Incertidumbre alta: hay señales de estrés hídrico en una etapa crítica y pocas parcelas comparables. Conviene revisarla con cautela.',
    'La pendiente y la baja retención de humedad penalizan la estimación; el rango probable es amplio.',
    'Vigor irregular durante el ciclo. La cifra es orientativa y debe leerse junto con su rango probable.',
  ],
  ood: [
    'El patrón temporal se parece poco al de las parcelas de entrenamiento, así que la estimación es menos confiable. Revísala con cautela.',
    'Parcela poco representada en los datos de entrenamiento: la predicción puede desviarse más de lo habitual.',
  ],
};

function mulberry32(semilla) {
  let a = semilla;
  return () => {
    a = (a + 0x6d2b79f5) | 0;
    let t = Math.imul(a ^ (a >>> 15), 1 | a);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

const limitar = (v, a, b) => Math.min(b, Math.max(a, v));

function generarParcelas() {
  const rnd = mulberry32(361);
  const gauss = () => { // ≈ N(0,1): suma de 6 uniformes
    let acc = 0;
    for (let k = 0; k < 6; k++) acc += rnd();
    return (acc - 3) / Math.SQRT1_2;
  };
  const entre = (a, b) => a + Math.floor(rnd() * (b - a + 1));
  const elegir = (lista) => lista[Math.floor(rnd() * lista.length)];

  // Cola de municipios (descontando las destacadas) barajada con Fisher–Yates
  const restantes = Object.fromEntries(Object.entries(PERFIL_MUNICIPIO).map(([m, d]) => [m, d.n]));
  parcelasDestacadas.forEach((p) => { restantes[p.municipio] -= 1; });
  const cola = Object.entries(restantes).flatMap(([m, n]) => Array(n).fill(m));
  for (let k = cola.length - 1; k > 0; k--) {
    const r = Math.floor(rnd() * (k + 1));
    [cola[k], cola[r]] = [cola[r], cola[k]];
  }

  const ocupados = new Set(parcelasDestacadas.map((p) => p.id));
  const generadas = [];

  for (let n = 1; n <= TOTAL_PARCELAS; n++) {
    const codigo = String(n).padStart(3, '0');
    const id = `AGC_${codigo}`;
    if (ocupados.has(id)) continue;

    const municipio = cola.pop();
    const perfil = PERFIL_MUNICIPIO[municipio];

    // Riesgo según la distribución del municipio; la confianza sigue al riesgo
    const u = rnd();
    const [pBajo, pMedio] = perfil.riesgo;
    const riesgo = u < pBajo ? 'bajo' : u < pBajo + pMedio ? 'medio' : 'alto';
    const confianza_pct =
      riesgo === 'bajo' ? entre(82, 94) : riesgo === 'medio' ? entre(70, 81) : entre(55, 69);
    const confianza = confianza_pct >= 82 ? 'alta' : confianza_pct >= 70 ? 'media' : 'baja';
    const ood_flag = riesgo === 'alto' && rnd() < 0.6;

    // Parcelas de riesgo alto tienden a rendir un poco menos
    const ajuste = riesgo === 'bajo' ? 0.12 : riesgo === 'alto' ? -0.28 : 0;
    const rendimiento_t_ha = +limitar(perfil.media + gauss() * 0.42 + ajuste, 2.9, 5.7).toFixed(2);
    const superficie_ha = +(1.4 + rnd() ** 1.6 * 7).toFixed(1);
    const semiancho = 0.15 + (100 - confianza_pct) * 0.0105;

    // SHAP: magnitudes escaladas con el rendimiento; el estrés hídrico pesa más con riesgo alto
    const rv = limitar(0.55 + (rendimiento_t_ha - 4.3) * 0.45, 0.45, 1.2);
    const jit = () => 0.85 + rnd() * 0.3;
    const estres = riesgo === 'alto' ? -(0.14 + rnd() * 0.1) : riesgo === 'medio' ? -(0.07 + rnd() * 0.06) : -(0.02 + rnd() * 0.04);
    const shap = [
      { categoria: 'vigor',          etiqueta: 'Vigor de la planta', valor: +(0.55 * rv * jit()).toFixed(2) },
      { categoria: 'clima',          etiqueta: 'Lluvia acumulada',   valor: +(0.27 * rv * jit()).toFixed(2) },
      { categoria: 'humedad',        etiqueta: 'Humedad del suelo',  valor: +(0.14 * rv * jit()).toFixed(2) },
      { categoria: 'estres_hidrico', etiqueta: 'Estrés hídrico',     valor: +estres.toFixed(2) },
      { categoria: 'topografia',     etiqueta: 'Pendiente',          valor: +((rnd() - 0.35) * 0.1).toFixed(2) },
    ].sort((x, y) => Math.abs(y.valor) - Math.abs(x.valor));

    generadas.push({
      ...parcelaBase,
      id,
      codigo,
      municipio,
      superficie_ha,
      rendimiento_t_ha,
      produccion_potencial_t: +(superficie_ha * rendimiento_t_ha).toFixed(1),
      rango_probable: [+(rendimiento_t_ha - semiancho).toFixed(2), +(rendimiento_t_ha + semiancho).toFixed(2)],
      confianza,
      confianza_pct,
      riesgo,
      ood_flag,
      shap,
      narrativa: elegir(ood_flag ? NARRATIVAS.ood : NARRATIVAS[riesgo]),
    });
  }
  return generadas;
}

// Las destacadas van primero: el dashboard abre seleccionando la primera (AGC_042)
export const parcelasMock = [...parcelasDestacadas, ...generarParcelas()];

// ============================================================
// Agregados CALCULADOS desde las parcelas (nunca escritos a mano,
// para que Regional, dashboard y ficha siempre cuadren entre sí)
// ============================================================
const redondear = (v, d) => +v.toFixed(d);

function distribucionRiesgo(lista) {
  const n = lista.length || 1;
  const cuenta = (nivel) => lista.filter((p) => p.riesgo === nivel).length / n;
  return { bajo: redondear(cuenta('bajo'), 3), medio: redondear(cuenta('medio'), 3), alto: redondear(cuenta('alto'), 3) };
}

// ============================================================
// Contexto municipal
// ============================================================
export const municipiosMock = Object.fromEntries(
  Object.keys(PERFIL_MUNICIPIO).map((municipio) => {
    const lista = parcelasMock.filter((p) => p.municipio === municipio);
    return [
      municipio,
      {
        municipio,
        estado: 'Tlaxcala',
        n_parcelas: lista.length,
        rendimiento_promedio_t_ha: redondear(lista.reduce((s, p) => s + p.rendimiento_t_ha, 0) / lista.length, 2),
        superficie_total_ha: redondear(lista.reduce((s, p) => s + p.superficie_ha, 0), 1),
        produccion_total_t: redondear(lista.reduce((s, p) => s + p.produccion_potencial_t, 0), 1),
        distribucion_riesgo: distribucionRiesgo(lista),
        factores_limitantes: FACTORES_MUNICIPIO[municipio],
      },
    ];
  }),
);

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
  n_parcelas: parcelasMock.length,
  n_train: 138,        // con rendimiento observado (dato del reto)
  n_prediccion: 59,    // a predecir (dato del reto)
  superficie_total_ha: redondear(parcelasMock.reduce((t, p) => t + p.superficie_ha, 0), 1),
  produccion_potencial_total_t: redondear(parcelasMock.reduce((t, p) => t + p.produccion_potencial_t, 0), 1),
  distribucion_riesgo: distribucionRiesgo(parcelasMock),
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