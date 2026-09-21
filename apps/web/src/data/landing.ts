import esval from '../assets/clients/brand-esval.png';
import sopraval from '../assets/clients/brand-sopraval.jpg';
import castano from '../assets/clients/brand-castano.jpg';
import generadora from '../assets/clients/brand-generadora.jpg';
import ksb from '../assets/clients/brand-ksb.jpg';
import venezia from '../assets/clients/brand-venezia.png';
import algas from '../assets/clients/brand-algas.jpg';
import tecfluid from '../assets/clients/brand-tecfluid.jpg';
import propal from '../assets/clients/brand-propal.png';
import ecorriles from '../assets/clients/brand-ecorriles.png';
import maf from '../assets/clients/brand-maf.png';
import soldesp from '../assets/clients/brand-soldesp.png';
import energias from '../assets/clients/brand-energias.png';
import ingefrio from '../assets/clients/brand-ingefrio.png';
import ingenproyect from '../assets/clients/brand-ingenproyect.png';
import shs from '../assets/clients/brand-shs.jpg';

import faena1 from '../assets/landing/faena-1.jpg';
import faena2 from '../assets/landing/faena-2.jpg';
import faena3 from '../assets/landing/faena-3.jpg';

export interface StatItem {
  target: number;
  suffix: string;
  display: string;
  label: string;
}

export const stats: StatItem[] = [
  { target: 25, suffix: '+', display: '25+', label: 'Años de trayectoria continua' },
  { target: 150, suffix: '+', display: '150+', label: 'Proyectos de alta y baja tensión' },
  { target: 40, suffix: '+', display: '40+', label: 'Clientes corporativos activos' },
  { target: 100, suffix: '%', display: '100%', label: 'Certificaciones SEC aprobadas' }
];

export interface MercadoItem {
  title: string;
  desc: string;
  clients: string;
}

export const mercados: MercadoItem[] = [
  { title: 'Agroindustria & Alimentos', desc: 'Cámaras de frío, líneas de molienda y envasado con continuidad operativa garantizada.', clients: 'Sopraval · Castaño · Venezia' },
  { title: 'Recursos Hídricos & Sanitaria', desc: 'Plantas de tratamiento, impulsión de caudal y variadores de frecuencia.', clients: 'ESVAL · KSB · Tecfluid' },
  { title: 'Energía & Generación', desc: 'Sincronismo de generadores, celdas de MT y trámites de potencia.', clients: 'Generadora Metropolitana' }
];

export interface ServicioItem {
  title: string;
  desc: string;
  bullets: string[];
}

export const servicios: ServicioItem[] = [
  { title: 'Ingeniería Eléctrica', desc: 'Montaje de TDF/TDA, mallas a tierra y bandejas portacables pesadas.', bullets: ['Declaración SEC TE1', 'Diseño BT/MT'] },
  { title: 'Automatización & PLC', desc: 'Programación Siemens S7 / Allen-Bradley, pantallas HMI y SCADA.', bullets: ['Variadores de frecuencia', 'Integración SCADA'] },
  { title: 'Obras Civiles Industriales', desc: 'Salas eléctricas modulares climatizadas y zanjas para ductos subterráneos.', bullets: ['Radieres técnicos', 'Ductos subterráneos'] },
  { title: 'Mantención & Guardia 24/7', desc: 'Termografía infrarroja de tableros y calibración de protecciones.', bullets: ['Atención de contingencias', 'Termografía IR'] }
];

export interface PortfolioItem {
  img: ImageMetadata;
  title: string;
  spec: string;
}

export const portafolio: PortfolioItem[] = [
  { img: faena1, title: 'Ampliación Planta Cecinas Sopraval', spec: '450 kVA · Quilpué' },
  { img: faena2, title: 'Estación de Bombeo e Impulsión ESVAL', spec: '800 kVA · Valparaíso' },
  { img: faena3, title: 'Línea de Envasado Alimentos Castaño', spec: 'Control Siemens S7-1500 · Santiago' }
];

export interface BrandItem {
  img: ImageMetadata;
  alt: string;
}

export const brands: BrandItem[] = [
  { img: esval, alt: 'ESVAL' },
  { img: sopraval, alt: 'Sopraval' },
  { img: castano, alt: 'Castaño' },
  { img: generadora, alt: 'Generadora Metropolitana' },
  { img: ksb, alt: 'KSB' },
  { img: venezia, alt: 'Cecinas Venezia' },
  { img: algas, alt: 'Algas Marinas' },
  { img: tecfluid, alt: 'Tecfluid' },
  { img: propal, alt: 'Propal' },
  { img: ecorriles, alt: 'Ecorriles' },
  { img: maf, alt: 'MAF' },
  { img: soldesp, alt: 'Soldes P' },
  { img: energias, alt: 'Energías Industriales' },
  { img: ingefrio, alt: 'IngeFrío' },
  { img: ingenproyect, alt: 'IngenProyect' },
  { img: shs, alt: 'SHS' }
];

export const quoteOptions: string[] = ['Montaje TDF', 'Automatización', 'Trámite TE1', 'Mantención'];

export interface TestimonialItem {
  quote: string;
  name: string;
  role: string;
}

// TODO: PLACEHOLDER FICTICIO — reemplazar por reseñas reales (Google/clientes) antes de publicar a producción.
export const testimonials: TestimonialItem[] = [
  { quote: 'El equipo de BKB respondió a una falla crítica de tablero fuera de horario y evitó varias horas de parada de línea. Profesionalismo total de principio a fin.', name: 'J. Contreras', role: 'Jefe de Mantención · Sector Agroindustrial' },
  { quote: 'Cumplieron los plazos comprometidos en el montaje de la subestación y toda la documentación SEC quedó en regla desde el primer día.', name: 'M. Herrera', role: 'Gerente de Proyectos · Sector Sanitario' },
  { quote: 'Llevamos años trabajando con BKB en mantenciones preventivas. Comunicación clara, orden en terreno y un equipo técnico muy capacitado.', name: 'R. Salinas', role: 'Superintendente Eléctrico · Sector Energía' },
];
