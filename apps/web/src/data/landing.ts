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
import faenaHero from '../assets/landing/faena-hero.jpg';

export interface StatItem {
  target: number;
  suffix: string;
  display: string;
  label: string;
}

export const stats: StatItem[] = [
  { target: 30, suffix: '+', display: '30+', label: 'Años de trayectoria continua' },
  { target: 150, suffix: '+', display: '150+', label: 'Proyectos de alta y baja tensión' },
  { target: 40, suffix: '+', display: '40+', label: 'Clientes corporativos activos' }
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
  image: ImageMetadata;
  title: string;
  desc: string;
}

// Textos de los 4 primeros servicios: verificados (empresabkb.cl). Arriendo: dato entregado por el cliente.
// TODO: fotos provisorias (faena), reemplazar por fotos de cada servicio
export const servicios: ServicioItem[] = [
  { image: faena1, title: 'Ingeniería Eléctrica', desc: 'Desarrollo de ingenierías conceptual, básica y de detalle. Diseño y ejecución de proyectos eléctricos completos: canalización, alimentación, tableros y sistemas de control.' },
  { image: faena2, title: 'Automatización PLC', desc: 'Programación y desarrollo de sistemas PLC con pruebas FAT/SAT e integración SCADA.' },
  { image: faena3, title: 'Fabricación Propia', desc: 'Fabricación de Sistemas Kit: Bombeo, Filtrado, Lubricación y otros componentes especializados.' },
  { image: faenaHero, title: 'Montaje y Soporte', desc: 'Montaje en terreno y puesta en marcha con soporte técnico post-entrega garantizado.' },
  { image: faena2, title: 'Arriendo de Equipos', desc: 'Arriendo de instrumentación eléctrica: analizadores de red y medidores de tierra, de fuga y de aislación.' }
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
