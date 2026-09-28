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
// TODO: validar con BKB los textos de `uso` (redactados a partir del tipo de equipo, sin especificaciones).
export const gruposArriendo: GrupoArriendo[] = [
  {
    titulo: 'Instrumentos de medición',
    equipos: [
      { id: 'fluke-1674-fc', nombre: 'Comprobador de instalaciones RIC 19', modelo: 'Fluke 1674 FC', uso: 'Verifica instalaciones eléctricas antes de su puesta en servicio, según el pliego RIC N°19.' },
      { id: 'fluke-1775', nombre: 'Analizador trifásico de calidad eléctrica clase A', modelo: 'Fluke 1775', uso: 'Registra la calidad de la energía en redes trifásicas: armónicos, variaciones de tensión, factor de potencia y consumo.' },
      { id: 'fluke-1630-2-fc', nombre: 'Pinza de resistencia de tierra', modelo: 'Fluke 1630-2 FC', uso: 'Mide la resistencia de puesta a tierra sin desconectar el electrodo ni clavar picas auxiliares.' },
      { id: 'fluke-1625-2', nombre: 'Comprobador de puesta a tierra avanzado', modelo: 'Fluke 1625-2', uso: 'Mide la resistencia de mallas y electrodos de puesta a tierra, y la resistividad del terreno.' },
      { id: 'fluke-773', nombre: 'Pinza amperimétrica de procesos', modelo: 'Fluke 773', uso: 'Mide y simula señales de 4-20 mA en lazos de control e instrumentación sin abrir el circuito.' },
      { id: 'fluke-1507', nombre: 'Medidor de resistencia de aislamiento', modelo: 'Fluke 1507', uso: 'Mide la resistencia de aislamiento de cables, motores, transformadores y tableros.' },
      { id: 'fluke-ti400', nombre: 'Cámara termográfica', modelo: 'Fluke Ti400', uso: 'Detecta puntos calientes en tableros, conexiones y motores sin contacto y sin detener la operación.' },
      { id: 'fluke-376', nombre: 'Pinza amperimétrica', modelo: 'Fluke 376', uso: 'Mide corriente sin abrir el circuito, además de tensión y continuidad, en circuitos de fuerza y control.' },
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
