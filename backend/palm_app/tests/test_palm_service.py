import pytest
from unittest.mock import Mock, patch
from sqlalchemy.exc import IntegrityError

from palm_app.models.palm import PalmProfile
from palm_app.services.palm_service import PalmService


@pytest.fixture
def mock_request():
    request = Mock()
    request.dbsession = Mock()
    request.registry.settings = {
        's3_bucket': 'test-bucket',
        'aws_access_key_id': 'test-key',
        'aws_secret_access_key': 'test-secret',
        'aws_region': 'us-east-1',
    }
    return request


@pytest.fixture
def palm_service(mock_request):
    with patch('palm_app.services.palm_service.StorageService') as storage_cls:
        storage_cls.return_value.upload_image.return_value = None
        storage_cls.return_value.delete_image.return_value = None
        yield PalmService(mock_request)


class TestPalmService:
    def test_create_palm_success(self, palm_service):
        data = {
            'palm_id': 'P001',
            'palm_code': 'CODE001',
            'plant_date': '2020-01-01',
            'donner_name': 'John Doe',
            'area': 'Area A',
        }

        palm = palm_service.create_palm(data)

        assert palm.palm_code == 'CODE001'
        palm_service.db.add.assert_called_once()
        palm_service.db.flush.assert_called_once()

    def test_create_palm_duplicate(self, palm_service):
        palm_service.db.flush.side_effect = IntegrityError(
            'duplicate', {'params': []}, None
        )

        data = {
            'palm_id': 'P001',
            'palm_code': 'CODE001',
            'plant_date': '2020-01-01',
        }

        with pytest.raises(ValueError, match='already exists'):
            palm_service.create_palm(data)

        palm_service.db.rollback.assert_called_once()

    def test_search_palms(self, palm_service):
        mock_query = palm_service.db.query.return_value
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 1
        mock_query.order_by.return_value.offset.return_value.limit.return_value.all.return_value = [
            PalmProfile(palm_code='CODE001')
        ]

        results = palm_service.search_palms(palm_code='CODE')

        assert results['total'] == 1
        assert len(results['palms']) == 1
        assert results['palms'][0].palm_code == 'CODE001'

    def test_get_statistics(self, palm_service):
        mock_stats = Mock()
        mock_stats.total_palms = 100
        mock_stats.total_harvest = 5000.5
        mock_stats.avg_age = 15.2

        mock_query = palm_service.db.query
        mock_query.return_value.first.return_value = mock_stats
        mock_query.return_value.group_by.return_value.all.return_value = [
            ('Area A', 50),
            ('Area B', 30),
        ]

        stats = palm_service.get_statistics()

        assert stats['total_palms'] == 100
        assert stats['total_harvest'] == 5000.5
        assert stats['average_age'] == 15.2
        assert len(stats['areas']) == 2
