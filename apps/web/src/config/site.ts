export const SITE = {
  name: 'BKB Obras Eléctricas & Servicios',
  phoneDisplay: '+56 9 8249 1403',
  phoneHref: 'tel:+56982491403',
  email: 'contacto@bkb.cl',
  office: 'Quilpué, Región de Valparaíso',
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
