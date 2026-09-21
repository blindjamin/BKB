export const SITE = {
  name: 'BKB Obras Eléctricas & Servicios',
  phoneDisplay: '+56 9 8249 1403',
  phoneHref: 'tel:+56982491403',
  email: 'contacto@bkb.cl',
  office: 'La Calera, Región de Valparaíso',
  officeAddress: 'El Parque 110, La Calera, Región de Valparaíso',
  coverage: 'Valparaíso y Región Metropolitana',
} as const;

const PORTAL = import.meta.env.PUBLIC_PORTAL_URL || 'https://portal.bkb.cl';

export const PORTAL_URLS = {
  home: PORTAL,
  cliente: `${PORTAL}/accounts/login/?perfil=cliente`,
  colaborador: `${PORTAL}/accounts/login/?perfil=colaborador`,
} as const;

export const QUOTE_ENDPOINT = import.meta.env.PUBLIC_QUOTE_ENDPOINT || '';
