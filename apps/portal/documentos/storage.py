"""Conexión con el Space: firma URLs y confirma objetos, siempre bajo SPACES_PREFIX.

El contenido de los archivos nunca pasa por Django: viaja navegador <-> Space.
A propósito no hay funciones para listar ni borrar (docs/03, sección 8).
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


def url_descarga(clave, nombre_original):
    """URL de 60 s que descarga el objeto como adjunto con su nombre original."""
    _validar(clave)
    disposicion = f"attachment; filename*=UTF-8''{quote(nombre_original, safe='')}"
    return _cliente().generate_presigned_url(
        'get_object',
        Params={'Bucket': settings.SPACES_BUCKET, 'Key': clave, 'ResponseContentDisposition': disposicion},
        ExpiresIn=EXPIRA_SEGUNDOS,
    )


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
