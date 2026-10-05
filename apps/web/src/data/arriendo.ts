export interface EquipoArriendo {
  id: string;
  nombre: string;
  modelo?: string;
  uso: string;
}

export interface GrupoArriendo {
  titulo: string;
  equipos: EquipoArriendo[];
}

// Equipos: tabla entregada por BKB el 28-09-2026. No se arriendan equipos de calibración ni de alineación láser.
// Textos de `uso` de los Fluke: según las fichas del fabricante (05-10-2026). Generadores: sin modelo, texto genérico.
export const gruposArriendo: GrupoArriendo[] = [
  {
    titulo: 'Instrumentos de medición',
    equipos: [
      { id: 'fluke-1674-fc', nombre: 'Comprobador de instalaciones RIC 19', modelo: 'Fluke 1674 FC', uso: 'Prueba completa de instalaciones antes de su puesta en servicio: aislamiento hasta 1000 V, continuidad, impedancia de lazo y línea, diferenciales (RCD) y protectores de sobretensión, con secuencia automática y aprobado/rechazado.' },
      { id: 'fluke-1775', nombre: 'Analizador trifásico de calidad eléctrica clase A', modelo: 'Fluke 1775', uso: 'Registra más de 500 parámetros de la red trifásica: tensión, corriente, potencia, armónicos, huecos, sobretensiones, desequilibrios y transitorios de hasta 8 kV, con informes para detectar el origen de fallas.' },
      { id: 'fluke-1630-2-fc', nombre: 'Pinza de resistencia de tierra', modelo: 'Fluke 1630-2 FC', uso: 'Mide la resistencia de lazo de tierra (0,025 a 1500 Ω) y las corrientes de fuga a tierra con solo abrazar el conductor, sin desconectar el electrodo ni clavar picas auxiliares.' },
      { id: 'fluke-1625-2', nombre: 'Comprobador de puesta a tierra avanzado', modelo: 'Fluke 1625-2', uso: 'Mide mallas y electrodos de tierra con picas (caída de potencial de 3 y 4 polos), de forma selectiva o sin picas con dos pinzas, y la resistividad del terreno para diseñar nuevas mallas.' },
      { id: 'fluke-773', nombre: 'Pinza amperimétrica de procesos', modelo: 'Fluke 773', uso: 'Mide señales de 4-20 mA sin abrir el lazo, simula y alimenta lazos (24 V) y mide o genera tensión continua: ideal para revisar transmisores, válvulas y entradas/salidas de PLC.' },
      { id: 'fluke-1507', nombre: 'Medidor de resistencia de aislamiento', modelo: 'Fluke 1507', uso: 'Mide aislamiento de cables, motores, transformadores y tableros con tensiones de prueba de 50 a 1000 V (hasta 10 GΩ), y calcula el índice de polarización y la relación de absorción dieléctrica.' },
      { id: 'fluke-ti400', nombre: 'Cámara termográfica', modelo: 'Fluke Ti400', uso: 'Cámara de 320x240 con enfoque automático por láser que detecta puntos calientes en tableros, conexiones y motores hasta 1200 °C, sin contacto y sin detener la operación.' },
      { id: 'fluke-376', nombre: 'Pinza amperimétrica', modelo: 'Fluke 376', uso: 'Mide hasta 1000 A en AC y DC (2500 A AC con sonda flexible iFlex) y 1000 V, con filtro para variadores de frecuencia y captura de la corriente de arranque de motores.' },
    ],
  },
  {
    titulo: 'Generadores',
    equipos: [
      { id: 'generador-200kva', nombre: 'Generador 200 kVA', uso: 'Respaldo de energía para plantas, obras o faenas durante cortes programados o mantenciones.' },
      { id: 'generador-30kva', nombre: 'Generador 30 kVA', uso: 'Energía provisoria para obras, instalaciones de menor consumo o trabajos puntuales en terreno.' },
    ],
  },
];
