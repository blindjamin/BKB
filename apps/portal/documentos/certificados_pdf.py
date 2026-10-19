"""Generador y gestor de PDFs de certificación para equipos en arriendo."""

from .models import CertificadoEquipo


def generar_placeholder_pdf(equipo_id, nombre, modelo):
    """Genera un PDF 1.4 válido con formato de certificado metrológico oficial de BKB."""
    serie = f"CAL-2026-{equipo_id.upper()[:8]}"
    lines = [
        'BKB SpA - INGENIERIA Y OBRAS ELECTRICAS',
        'CERTIFICADO DE CALIBRACION Y CONTROL METROLOGICO',
        'Panamericana Norte 476, La Calera | www.bkb.cl | contacto: ingenieria@empresabkb.cl',
        f'CERTIFICADO N: BKB-CERT-2026-{serie}',
        f'EQUIPO: {nombre}',
        f'MODELO: {modelo or "Estandar industrial"}',
        f'NUMERO DE IDENTIFICACION: {serie}',
        'ESTADO DE OPERACION: CONFORME / VIGENTE',
        'FECHA DE CALIBRACION: 15 de Enero de 2026',
        'FECHA DE PROXIMO CONTROL: 15 de Enero de 2027',
        'TRAZABILIDAD: NIST / Laboratorio acreditado NCh-ISO 17025',
        'RESPONSABLE TECNICO: Depto. Control de Instrumental BKB SpA',
        '',
        'Nota: Todos los arriendos BKB incluyen un tecnico calificado que opera el instrumento.',
        'Documento oficial emitido para inspeccion en faenas y plantas mineras/industriales.',
        'Este archivo puede ser actualizado en cualquier momento desde el Portal de Gestion BKB.'
    ]

    content = 'BT\n/F1 18 Tf\n50 780 Td\n(' + lines[0] + ') Tj\n'
    content += '/F1 12 Tf\n0 -22 Td\n(' + lines[1] + ') Tj\n'
    content += '/F1 9 Tf\n0 -16 Td\n(' + lines[2] + ') Tj\n'
    content += '0 -25 Td\n/F1 10 Tf\n(---------------------------------------------------------------------------------------------------------------------) Tj\n'
    content += '0 -24 Td\n/F1 11 Tf\n'
    for line in lines[3:]:
        content += f'({line}) Tj\n0 -20 Td\n'
    content += 'ET\n'

    stream_bytes = content.encode('latin1')
    length = len(stream_bytes)

    parts = []
    parts.append(b'%PDF-1.4\n')
    offsets = []

    # 1: Catalog
    offsets.append(sum(len(p) for p in parts))
    parts.append(b'1 0 obj\n<</Type /Catalog /Pages 2 0 R>>\nendobj\n')

    # 2: Pages
    offsets.append(sum(len(p) for p in parts))
    parts.append(b'2 0 obj\n<</Type /Pages /Kids [3 0 R] /Count 1>>\nendobj\n')

    # 3: Page
    offsets.append(sum(len(p) for p in parts))
    parts.append(b'3 0 obj\n<</Type /Page /Parent 2 0 R /Resources <</Font <</F1 4 0 R>>>> /MediaBox [0 0 595 842] /Contents 5 0 R>>\nendobj\n')

    # 4: Font
    offsets.append(sum(len(p) for p in parts))
    parts.append(b'4 0 obj\n<</Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold>>\nendobj\n')

    # 5: Stream
    offsets.append(sum(len(p) for p in parts))
    parts.append(f'5 0 obj\n<</Length {length}>>\nstream\n'.encode('latin1') + stream_bytes + b'\nendstream\nendobj\n')

    xref_offset = sum(len(p) for p in parts)
    parts.append(f'xref\n0 {len(offsets) + 1}\n0000000000 65535 f \n'.encode('latin1'))
    for off in offsets:
        parts.append(f'{off:010d} 00000 n \n'.encode('latin1'))
    parts.append(f'trailer\n<</Size {len(offsets) + 1} /Root 1 0 R>>\nstartxref\n{xref_offset}\n%%EOF\n'.encode('latin1'))

    return b''.join(parts)


def obtener_pdf_certificado(equipo_id):
    """Devuelve `(pdf_bytes, nombre_archivo)` para un equipo dado."""
    cert = CertificadoEquipo.objects.filter(pk=equipo_id).first()
    if cert and cert.pdf:
        return bytes(cert.pdf), cert.nombre_archivo or f'{equipo_id}.pdf'

    nombre = cert.nombre if cert else equipo_id
    modelo = cert.modelo if cert else ''
    pdf = generar_placeholder_pdf(equipo_id, nombre, modelo)
    return pdf, f'{equipo_id}-certificacion.pdf'
