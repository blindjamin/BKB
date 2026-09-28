// Teléfonos confirmados por BKB. El primero es el principal (aviso de emergencia, WhatsApp, datos para Google).
const PHONES = [
  { display: '+56 9 8975 3095', href: 'tel:+56989753095' },
  { display: '+56 9 6191 1593', href: 'tel:+56961911593' },
] as const;

export const SITE = {
  name: 'BKB Obras Eléctricas & Servicios',
  phones: PHONES,
  phoneDisplay: PHONES[0].display,
  phoneHref: PHONES[0].href,
  email: 'contacto@bkb.cl',
  office: 'La Calera, Región de Valparaíso',
  officeAddress: 'El Parque 110, La Calera, Región de Valparaíso',
  coverage: 'Valparaíso y Región Metropolitana',
} as const;

const PORTAL = import.meta.env.PUBLIC_PORTAL_URL || 'https://portal.empresabkb.cl';
const LOGIN = `${PORTAL}/login/`;

// Clientes y colaboradores entran por el mismo login; el portal decide qué ve cada uno.
export const PORTAL_URLS = {
  home: LOGIN,
  cliente: LOGIN,
  colaborador: LOGIN,
} as const;

export const QUOTE_ENDPOINT = import.meta.env.PUBLIC_QUOTE_ENDPOINT || '';
