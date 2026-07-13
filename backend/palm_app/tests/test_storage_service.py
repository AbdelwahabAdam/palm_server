from unittest.mock import Mock

from palm_app.services.storage_service import StorageService, _is_valid_upload


def test_is_valid_upload_rejects_empty_filename():
    image = Mock()
    image.filename = ''
    assert _is_valid_upload(image) is False


def test_is_valid_upload_accepts_named_file():
    image = Mock()
    image.filename = 'palm.jpg'
    assert _is_valid_upload(image) is True


def test_get_view_url_maps_private_s3_to_proxy():
    storage = StorageService({
        's3_bucket': 'my-bucket',
        'aws_access_key_id': 'key',
        'aws_secret_access_key': 'secret',
        'aws_region': 'eu-central-1',
    })
    stored = 'https://my-bucket.s3.eu-central-1.amazonaws.com/palms/abc.jpg'
    view_url = storage.get_view_url(stored)
    assert view_url.startswith('https://')
    assert 'palms/abc.jpg' in view_url
    assert 'X-Amz-Signature' in view_url or 'AWSAccessKeyId' in view_url


def test_get_view_url_keeps_local_path():
    storage = StorageService({'upload_dir': '/tmp'})
    assert storage.get_view_url('/api/uploads/palms/local.jpg') == '/api/uploads/palms/local.jpg'


def test_resolve_local_path_accepts_tuple_subpath(tmp_path):
    target = tmp_path / 'palms' / 'img.jpg'
    target.parent.mkdir(parents=True)
    target.write_bytes(b'x')
    storage = StorageService({'upload_dir': str(tmp_path)})
    assert storage.resolve_local_path(('palms', 'img.jpg')) == target


def test_upload_image_does_not_evaluate_fieldstorage_as_bool(tmp_path):
    settings = {'upload_dir': str(tmp_path)}
    storage = StorageService(settings)

    image = Mock()
    image.filename = 'palm.jpg'
    image.type = 'image/jpeg'
    image.file = Mock()
    image.file.seek = Mock(side_effect=ValueError('seek of closed file'))
    image.file.read = Mock(return_value=b'abc')

    type(image).__bool__ = Mock(side_effect=TypeError('Cannot be converted to bool.'))

    url = storage.upload_image(image)

    assert url.startswith('/api/uploads/palms/')
    assert url.endswith('.jpg')
