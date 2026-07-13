import io
import logging
import uuid
from pathlib import Path

import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)

UPLOAD_SUBDIR = 'palms'


def _is_valid_upload(image):
    if image is None:
        return False
    filename = getattr(image, 'filename', None)
    return bool(filename and str(filename).strip())


def _read_upload_content(image):
    if hasattr(image, 'file'):
        stream = image.file
        try:
            stream.seek(0)
        except (OSError, ValueError):
            pass
        data = stream.read()
    elif hasattr(image, 'read'):
        data = image.read()
    else:
        data = bytes(image)
    return io.BytesIO(data)


class StorageService:
    def __init__(self, settings):
        self.settings = settings
        self.s3_bucket = (settings.get('s3_bucket') or '').strip()
        self.aws_access_key_id = (settings.get('aws_access_key_id') or '').strip()
        self.aws_secret_access_key = (settings.get('aws_secret_access_key') or '').strip()
        self.aws_region = settings.get('aws_region', 'us-east-1')
        self.upload_root = Path(settings.get('upload_dir', '/app/uploads'))
        self.s3_client = None

        if self._s3_configured():
            self.s3_client = boto3.client(
                's3',
                aws_access_key_id=self.aws_access_key_id,
                aws_secret_access_key=self.aws_secret_access_key,
                region_name=self.aws_region,
                endpoint_url=f'https://s3.{self.aws_region}.amazonaws.com',
            )

    def _s3_configured(self):
        return bool(self.s3_bucket and self.aws_access_key_id and self.aws_secret_access_key)

    def storage_mode(self):
        return 's3' if self._s3_configured() else 'local'

    def _extract_s3_key(self, image_url):
        if not image_url:
            return None
        if image_url.startswith('s3://'):
            parts = image_url[5:].split('/', 1)
            return parts[1] if len(parts) == 2 else None
        if '.amazonaws.com/' in image_url:
            path = image_url.split('.amazonaws.com/', 1)[-1]
            return path.split('?')[0]
        if image_url.startswith('/api/images/'):
            return image_url.removeprefix('/api/images/')
        return None

    def _presign_view_url(self, key, expires_in=3600):
        return self.s3_client.generate_presigned_url(
            'get_object',
            Params={
                'Bucket': self.s3_bucket,
                'Key': key,
                'ResponseContentDisposition': 'inline',
            },
            ExpiresIn=expires_in,
        )

    def get_view_url(self, stored_url):
        if not stored_url:
            return None
        if stored_url.startswith('/api/uploads/'):
            return stored_url
        key = self._extract_s3_key(stored_url)
        if key and self._s3_configured():
            try:
                return self._presign_view_url(key)
            except ClientError as exc:
                logger.error('Failed to presign S3 image %s: %s', key, exc)
        return stored_url

    def get_s3_object(self, key):
        if not self._s3_configured():
            raise ValueError('S3 is not configured')
        return self.s3_client.get_object(Bucket=self.s3_bucket, Key=key)

    def upload_image(self, image):
        if not _is_valid_upload(image):
            return None

        filename_attr = str(image.filename).strip()
        ext = filename_attr.rsplit('.', 1)[-1].lower() if '.' in filename_attr else 'jpg'
        filename = f'{UPLOAD_SUBDIR}/{uuid.uuid4()}.{ext}'
        content_type = getattr(image, 'type', None) or 'image/jpeg'
        file_obj = _read_upload_content(image)

        if self._s3_configured():
            return self._upload_to_s3(file_obj, filename, content_type)
        return self._upload_to_local(file_obj, filename)

    def delete_image(self, image_url):
        if not image_url:
            return

        if image_url.startswith('/api/uploads/'):
            relative = image_url.removeprefix('/api/uploads/')
            path = self.upload_root / relative
            if path.exists():
                path.unlink(missing_ok=True)
            return

        if '.amazonaws.com/' in image_url and self._s3_configured():
            key = self._extract_s3_key(image_url)
            if not key:
                return
            try:
                self.s3_client.delete_object(Bucket=self.s3_bucket, Key=key)
            except ClientError as exc:
                logger.error('Error deleting image from S3: %s', exc)

    def _upload_to_s3(self, file_obj, filename, content_type):
        payload = file_obj.read()
        extra_args = {'ContentType': content_type}

        try:
            self.s3_client.upload_fileobj(
                io.BytesIO(payload),
                self.s3_bucket,
                filename,
                ExtraArgs={**extra_args, 'ACL': 'public-read'},
            )
        except ClientError as exc:
            error_code = exc.response.get('Error', {}).get('Code', '')
            if error_code in {'AccessControlListNotSupported', 'AccessDenied'}:
                self.s3_client.upload_fileobj(
                    io.BytesIO(payload),
                    self.s3_bucket,
                    filename,
                    ExtraArgs=extra_args,
                )
            else:
                logger.error('Error uploading to S3: %s', exc)
                raise ValueError(
                    f'Failed to upload image to S3: {exc.response["Error"]["Message"]}'
                ) from exc
        return f'https://{self.s3_bucket}.s3.{self.aws_region}.amazonaws.com/{filename}'

    def _upload_to_local(self, file_obj, filename):
        target = self.upload_root / filename
        target.parent.mkdir(parents=True, exist_ok=True)
        with open(target, 'wb') as output:
            output.write(file_obj.read())
        return f'/api/uploads/{filename}'

    def resolve_local_path(self, subpath):
        if isinstance(subpath, (list, tuple)):
            subpath = '/'.join(str(part) for part in subpath if part)
        base = self.upload_root.resolve()
        candidate = (self.upload_root / subpath).resolve()
        if not str(candidate).startswith(str(base)):
            return None
        if candidate.exists() and candidate.is_file():
            return candidate
        return None
