/**
 * Helper para generar rutas compatibles tanto en local (base: '/')
 * como en GitHub Pages (base: '/BKB/').
 */
export const baseUrl = (import.meta.env.BASE_URL || '/').replace(/\/$/, '');

export function getPath(path: string): string {
  const cleanPath = path.startsWith('/') ? path : `/${path}`;
  if (cleanPath === '/') {
    return baseUrl ? `${baseUrl}/` : '/';
  }
  return `${baseUrl}${cleanPath}`;
}
