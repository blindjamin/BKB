"""Conexión con el Space: firma URLs y confirma objetos, siempre bajo SPACES_PREFIX.

El contenido de los archivos nunca pasa por Django: viaja navegador <-> Space.
Excepciones: `leer` trae el objeto para adjuntarlo a un correo, solo al enviar una modificación (M2), y
`abrir` lo lee para armar el ZIP del proyecto completo (solo jefes).
A propósito no hay función para borrar. Los archivos antiguos solo se listan y copian, al importarlos (comando importar_antiguos).
"""

from urllib.parse import quote

import boto3
from botocore.client import Config
from botocore.exceptions import ClientError
from django.conf import settings

EXPIRA_SEGUNDOS = 60


def _cliente():
    return boto3.client(
        's3',
        region_name=settings.SPACES_REGION,
        endpoint_url=settings.SPACES_ENDPOINT,
        aws_access_key_id=settings.SPACES_KEY,
        aws_secret_access_key=settings.SPACES_SECRET,
        config=Config(signature_version='s3v4', s3={'addressing_style': 'virtual'}),
    )


def _validar(clave):
    if not clave.startswith(settings.SPACES_PREFIX):
        raise ValueError(f'Clave fuera del prefijo {settings.SPACES_PREFIX!r}: {clave!r}')
    return clave


def clave_para(proyecto, archivo):
    """`{prefijo}{proyecto_uuid}/{archivo_uuid}`: solo UUID y prefijo, nunca texto del usuario."""
    return _validar(f'{settings.SPACES_PREFIX}{proyecto.pk}/{archivo.pk}')


def url_descarga(clave, nombre_original, ver_tipo=None):
    """URL de 60 s que descarga el objeto como adjunto con su nombre original.
    Con `ver_tipo` (vista previa, docs/13 D10) se muestra en el navegador con ese tipo, sin descargar."""
    _validar(clave)
    modo = 'inline' if ver_tipo else 'attachment'
    params = {'Bucket': settings.SPACES_BUCKET, 'Key': clave,
              'ResponseContentDisposition': f"{modo}; filename*=UTF-8''{quote(nombre_original, safe='')}"}
    if ver_tipo:  # los importados pueden venir como octet-stream: el PDF se descargaría en vez de mostrarse
        params['ResponseContentType'] = ver_tipo
    return _cliente().generate_presigned_url('get_object', Params=params, ExpiresIn=EXPIRA_SEGUNDOS)


MINIATURA_SEGUNDOS = 15 * 60  # la cuadrícula carga las fotos al bajar (lazy): 60 s no alcanzan


def url_miniatura(clave):
    """URL para mostrar la foto en un <img> (docs/13 P5). No es una descarga: no pasa por DescargaLog."""
    _validar(clave)
    return _cliente().generate_presigned_url(
        'get_object', Params={'Bucket': settings.SPACES_BUCKET, 'Key': clave}, ExpiresIn=MINIATURA_SEGUNDOS)


def post_subida(clave, tipo):
    """POST prefirmado de 60 s: el Space rechaza otro tipo, o menos de 1 byte o más de MAX_UPLOAD_MB.

    Devuelve `{'url': ..., 'fields': {...}}` para armar el formulario en el navegador.
    """
    _validar(clave)
    return _cliente().generate_presigned_post(
        settings.SPACES_BUCKET,
        clave,
        Fields={'Content-Type': tipo},
        Conditions=[
            {'Content-Type': tipo},
            ['content-length-range', 1, settings.MAX_UPLOAD_MB * 1024 * 1024],
        ],
        ExpiresIn=EXPIRA_SEGUNDOS,
    )


def tamano_en_space(clave):
    """Tamaño en bytes del objeto, o None si no existe (subida no hecha)."""
    _validar(clave)
    try:
        return _cliente().head_object(Bucket=settings.SPACES_BUCKET, Key=clave)['ContentLength']
    except ClientError as error:
        if error.response['Error']['Code'] in ('404', 'NoSuchKey', 'NotFound'):
            return None
        raise


def leer(clave):
    """M2: contenido del objeto para adjuntarlo al correo (solo al enviar, tope de 20 MB)."""
    _validar(clave)
    return _cliente().get_object(Bucket=settings.SPACES_BUCKET, Key=clave)['Body'].read()


def abrir(clave):
    """ZIP del proyecto: el objeto como flujo de lectura, para copiarlo al ZIP sin cargarlo entero en memoria."""
    _validar(clave)
    return _cliente().get_object(Bucket=settings.SPACES_BUCKET, Key=clave)['Body']


def listar_antiguos(raiz):
    """Importación: `(clave, tamaño)` de cada archivo bajo una carpeta antigua. Solo lectura, nunca bajo SPACES_PREFIX."""
    if not raiz.endswith('/') or raiz.startswith(settings.SPACES_PREFIX):
        raise ValueError(f'Carpeta antigua no válida: {raiz!r}')
    for pagina in _cliente().get_paginator('list_objects_v2').paginate(Bucket=settings.SPACES_BUCKET, Prefix=raiz):
        for objeto in pagina.get('Contents', []):
            if not objeto['Key'].endswith('/'):  # marcadores de carpeta
                yield objeto['Key'], objeto['Size']


def copiar(origen, destino):
    """Importación: copia dentro del Space (no pasa por Django); el original queda intacto."""
    _validar(destino)
    _cliente().copy_object(Bucket=settings.SPACES_BUCKET, Key=destino,
                           CopySource={'Bucket': settings.SPACES_BUCKET, 'Key': origen})
