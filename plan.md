Project Structure
├── backend/
│   ├── palm_app/
│   │   ├── __init__.py
│   │   ├── models/
│   │   ├── views/
│   │   ├── services/
│   │   ├── api/
│   │   ├── templates/
│   │   ├── static/
│   │   ├── tests/
│   │   └── utils/
│   ├── alembic/
│   ├── setup.py
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   ├── public/
│   ├── tests/
│   └── Dockerfile
├── docker-compose.yml
└── README.md


Backend Implementation Plan (Pyramid + SQLAlchemy)
1. Database Models
python
# backend/palm_app/models/palm.py
from sqlalchemy import Column, Integer, String, Float, DateTime, JSON
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class PalmProfile(Base):
    __tablename__ = 'palm_profiles'
    
    id = Column(Integer, primary_key=True)
    palm_id = Column(String(50), unique=True, nullable=False)
    palm_code = Column(String(50), unique=True, nullable=False, index=True)
    plant_date = Column(DateTime, nullable=False)
    donner_name = Column(String(100), index=True)
    donner_phone_number = Column(String(20), index=True)
    harvest_amount = Column(Float)
    last_harvest = Column(DateTime)
    age = Column(Integer)
    images = Column(JSON)  # Store S3 URLs
    area = Column(String(100))
    section = Column(String(100))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    email = Column(String(100), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(100))
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class SiteVisit(Base):
    __tablename__ = 'site_visits'
    
    id = Column(Integer, primary_key=True)
    ip_address = Column(String(45))
    user_agent = Column(String(255))
    page_visited = Column(String(255))
    visited_at = Column(DateTime, default=datetime.utcnow)
2. Backend Core Files
python
# backend/palm_app/__init__.py
from pyramid.config import Configurator
from pyramid.authentication import AuthTktAuthenticationPolicy
from pyramid.authorization import ACLAuthorizationPolicy
from pyramid.session import SignedCookieSessionFactory

def main(global_config, **settings):
    # Session factory
    session_factory = SignedCookieSessionFactory('your-secret-key')
    
    # Authentication policy
    authn_policy = AuthTktAuthenticationPolicy(
        'your-secret-key',
        hashalg='sha512'
    )
    authz_policy = ACLAuthorizationPolicy()
    
    config = Configurator(
        settings=settings,
        session_factory=session_factory
    )
    
    config.set_authentication_policy(authn_policy)
    config.set_authorization_policy(authz_policy)
    
    # Include routes
    config.include('.routes')
    
    # Static views
    config.add_static_view('static', 'static', cache_max_age=3600)
    
    # Scan views
    config.scan('.views')
    
    return config.make_wsgi_app()
3. Services Layer
python
# backend/palm_app/services/palm_service.py
import boto3
from botocore.exceptions import ClientError
from ..models.palm import PalmProfile
from sqlalchemy.exc import IntegrityError
import logging

logger = logging.getLogger(__name__)

class PalmService:
    def __init__(self, request):
        self.request = request
        self.db = request.dbsession
        self.s3_client = boto3.client('s3')
    
    def create_palm(self, data, images=None):
        """Create a new palm profile with image upload to S3"""
        try:
            image_urls = []
            if images:
                image_urls = self._upload_images_to_s3(images)
            
            palm = PalmProfile(
                palm_id=data['palm_id'],
                palm_code=data['palm_code'],
                plant_date=data['plant_date'],
                donner_name=data.get('donner_name'),
                donner_phone_number=data.get('donner_phone_number'),
                harvest_amount=data.get('harvest_amount'),
                last_harvest=data.get('last_harvest'),
                age=data.get('age'),
                images=image_urls,
                area=data.get('area'),
                section=data.get('section')
            )
            
            self.db.add(palm)
            self.db.flush()
            return palm
            
        except IntegrityError as e:
            self.db.rollback()
            raise ValueError(f"Palm with code {data['palm_code']} already exists")
    
    def _upload_images_to_s3(self, images):
        """Upload images to S3 and return URLs"""
        bucket_name = self.request.registry.settings['s3_bucket']
        image_urls = []
        
        for image in images:
            filename = f"palms/{image.filename}"
            try:
                self.s3_client.upload_fileobj(
                    image.file,
                    bucket_name,
                    filename,
                    ExtraArgs={'ACL': 'public-read'}
                )
                url = f"https://{bucket_name}.s3.amazonaws.com/{filename}"
                image_urls.append(url)
            except ClientError as e:
                logger.error(f"Error uploading to S3: {e}")
                raise
                
        return image_urls
    
    def search_palms(self, palm_code=None, donner_name=None, donner_phone=None, 
                     page=1, per_page=20):
        """Search palms with pagination"""
        query = self.db.query(PalmProfile)
        
        if palm_code:
            query = query.filter(PalmProfile.palm_code.ilike(f'%{palm_code}%'))
        if donner_name:
            query = query.filter(PalmProfile.donner_name.ilike(f'%{donner_name}%'))
        if donner_phone:
            query = query.filter(
                PalmProfile.donner_phone_number.ilike(f'%{donner_phone}%')
            )
        
        total = query.count()
        palms = query.offset((page - 1) * per_page).limit(per_page).all()
        
        return {
            'palms': palms,
            'total': total,
            'page': page,
            'per_page': per_page,
            'pages': (total + per_page - 1) // per_page
        }
    
    def get_statistics(self):
        """Get dashboard statistics"""
        total_palms = self.db.query(PalmProfile).count()
        
        stats = self.db.query(
            func.count(PalmProfile.id).label('total_palms'),
            func.sum(PalmProfile.harvest_amount).label('total_harvest'),
            func.avg(PalmProfile.age).label('avg_age')
        ).first()
        
        areas = self.db.query(
            PalmProfile.area,
            func.count(PalmProfile.id).label('count')
        ).group_by(PalmProfile.area).all()
        
        return {
            'total_palms': stats.total_palms,
            'total_harvest': float(stats.total_harvest or 0),
            'average_age': float(stats.avg_age or 0),
            'areas': [{'name': area[0], 'count': area[1]} for area in areas]
        }
    
    def update_palm(self, palm_id, data):
        """Update palm profile"""
        palm = self.db.query(PalmProfile).filter(
            PalmProfile.id == palm_id
        ).first()
        
        if not palm:
            raise ValueError("Palm not found")
        
        for key, value in data.items():
            if hasattr(palm, key):
                setattr(palm, key, value)
        
        self.db.flush()
        return palm
    
    def delete_palm(self, palm_id):
        """Delete palm profile and associated images from S3"""
        palm = self.db.query(PalmProfile).filter(
            PalmProfile.id == palm_id
        ).first()
        
        if not palm:
            raise ValueError("Palm not found")
        
        # Delete images from S3
        if palm.images:
            bucket_name = self.request.registry.settings['s3_bucket']
            for image_url in palm.images:
                key = image_url.split('.com/')[-1]
                try:
                    self.s3_client.delete_object(Bucket=bucket_name, Key=key)
                except ClientError as e:
                    logger.error(f"Error deleting image from S3: {e}")
        
        self.db.delete(palm)
4. Views Layer
python
# backend/palm_app/views/palm_views.py
from pyramid.view import view_config, view_defaults
from pyramid.httpexceptions import HTTPNotFound, HTTPBadRequest
from pyramid.response import Response
from ..services.palm_service import PalmService
import json

@view_defaults(renderer='json')
class PalmViews:
    def __init__(self, request):
        self.request = request
        self.palm_service = PalmService(request)
    
    @view_config(route_name='home', renderer='../templates/home.jinja2')
    def home(self):
        """Public home page with statistics"""
        stats = self.palm_service.get_statistics()
        return {'stats': stats}
    
    @view_config(route_name='search_palms', renderer='../templates/search.jinja2')
    def search_palms(self):
        """Public search page"""
        palm_code = self.request.params.get('palm_code')
        donner_name = self.request.params.get('donner_name')
        donner_phone = self.request.params.get('donner_phone')
        page = int(self.request.params.get('page', 1))
        
        results = self.palm_service.search_palms(
            palm_code=palm_code,
            donner_name=donner_name,
            donner_phone=donner_phone,
            page=page
        )
        
        return {'results': results, 'search_params': self.request.params}
    
    @view_config(route_name='palm_detail', renderer='../templates/palm_detail.jinja2')
    def palm_detail(self):
        """View palm details"""
        palm_id = self.request.matchdict['id']
        palm = self.request.dbsession.query(PalmProfile).filter(
            PalmProfile.id == palm_id
        ).first()
        
        if not palm:
            raise HTTPNotFound()
        
        return {'palm': palm}

@view_defaults(route_name='admin', renderer='json')
class AdminViews:
    def __init__(self, request):
        self.request = request
        self.palm_service = PalmService(request)
    
    @view_config(route_name='admin_dashboard', renderer='../templates/admin/dashboard.jinja2',
                 permission='admin')
    def dashboard(self):
        """Admin dashboard"""
        stats = self.palm_service.get_statistics()
        recent_visits = self.request.dbsession.query(SiteVisit).order_by(
            SiteVisit.visited_at.desc()
        ).limit(10).all()
        
        return {'stats': stats, 'recent_visits': recent_visits}
    
    @view_config(route_name='admin_palms_list', renderer='../templates/admin/palms.jinja2',
                 permission='admin')
    def list_palms(self):
        """Admin palm management page"""
        page = int(self.request.params.get('page', 1))
        results = self.palm_service.search_palms(page=page, per_page=50)
        return {'results': results}
    
    @view_config(route_name='admin_add_palm', request_method='POST',
                 permission='admin')
    def add_palm(self):
        """Add new palm profile"""
        try:
            data = {
                'palm_id': self.request.params['palm_id'],
                'palm_code': self.request.params['palm_code'],
                'plant_date': self.request.params['plant_date'],
                'donner_name': self.request.params.get('donner_name'),
                'donner_phone_number': self.request.params.get('donner_phone_number'),
                'harvest_amount': self.request.params.get('harvest_amount'),
                'last_harvest': self.request.params.get('last_harvest'),
                'age': self.request.params.get('age'),
                'area': self.request.params.get('area'),
                'section': self.request.params.get('section')
            }
            
            images = self.request.POST.getall('images')
            palm = self.palm_service.create_palm(data, images)
            
            return {'success': True, 'palm_id': palm.id}
        except Exception as e:
            return Response(
                json.dumps({'error': str(e)}),
                status=400,
                content_type='application/json'
            )
    
    @view_config(route_name='admin_reports', renderer='../templates/admin/reports.jinja2',
                 permission='admin')
    def reports(self):
        """Generate reports"""
        start_date = self.request.params.get('start_date')
        end_date = self.request.params.get('end_date')
        section = self.request.params.get('section')
        
        query = self.request.dbsession.query(
            PalmProfile.section,
            func.count(PalmProfile.id),
            func.sum(PalmProfile.harvest_amount)
        )
        
        if start_date:
            query = query.filter(PalmProfile.plant_date >= start_date)
        if end_date:
            query = query.filter(PalmProfile.plant_date <= end_date)
        if section:
            query = query.filter(PalmProfile.section == section)
        
        report_data = query.group_by(PalmProfile.section).all()
        
        return {
            'report_data': report_data,
            'filters': {
                'start_date': start_date,
                'end_date': end_date,
                'section': section
            }
        }
5. Tests
python
# backend/palm_app/tests/test_palm_service.py
import pytest
from unittest.mock import Mock, patch
from ..services.palm_service import PalmService
from ..models.palm import PalmProfile

@pytest.fixture
def mock_request():
    request = Mock()
    request.dbsession = Mock()
    request.registry.settings = {'s3_bucket': 'test-bucket'}
    return request

@pytest.fixture
def palm_service(mock_request):
    return PalmService(mock_request)

class TestPalmService:
    def test_create_palm_success(self, palm_service):
        """Test successful palm creation"""
        data = {
            'palm_id': 'P001',
            'palm_code': 'CODE001',
            'plant_date': '2020-01-01',
            'donner_name': 'John Doe',
            'area': 'Area A'
        }
        
        with patch.object(palm_service, '_upload_images_to_s3') as mock_upload:
            mock_upload.return_value = ['https://s3.url/image1.jpg']
            
            palm = palm_service.create_palm(data)
            
            assert palm.palm_code == 'CODE001'
            palm_service.db.add.assert_called_once()
            palm_service.db.flush.assert_called_once()
    
    def test_create_palm_duplicate(self, palm_service):
        """Test duplicate palm creation"""
        from sqlalchemy.exc import IntegrityError
        
        palm_service.db.flush.side_effect = IntegrityError(
            'duplicate', {'params': []}, None
        )
        
        data = {'palm_code': 'CODE001'}
        
        with pytest.raises(ValueError, match="already exists"):
            palm_service.create_palm(data)
        
        palm_service.db.rollback.assert_called_once()
    
    def test_search_palms(self, palm_service):
        """Test palm search functionality"""
        # Setup mock query
        mock_query = palm_service.db.query.return_value
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 1
        mock_query.offset.return_value.limit.return_value.all.return_value = [
            PalmProfile(palm_code='CODE001')
        ]
        
        results = palm_service.search_palms(palm_code='CODE')
        
        assert results['total'] == 1
        assert len(results['palms']) == 1
        assert results['palms'][0].palm_code == 'CODE001'
    
    def test_get_statistics(self, palm_service):
        """Test statistics generation"""
        from sqlalchemy import func
        
        # Setup mock for statistics query
        mock_stats = Mock()
        mock_stats.total_palms = 100
        mock_stats.total_harvest = 5000.5
        mock_stats.avg_age = 15.2
        
        mock_query = palm_service.db.query
        mock_query.return_value.first.return_value = mock_stats
        
        # Setup mock for area grouping
        mock_areas = [
            ('Area A', 50),
            ('Area B', 30),
            ('Area C', 20)
        ]
        mock_query.return_value.group_by.return_value.all.return_value = mock_areas
        
        stats = palm_service.get_statistics()
        
        assert stats['total_palms'] == 100
        assert stats['total_harvest'] == 5000.5
        assert stats['average_age'] == 15.2
        assert len(stats['areas']) == 3

# backend/palm_app/tests/test_views.py
class TestPalmViews:
    def test_home_view(self, test_app):
        """Test home page loads with statistics"""
        response = test_app.get('/')
        assert response.status_code == 200
        assert 'stats' in response.json
    
    def test_search_no_params(self, test_app):
        """Test search with no parameters"""
        response = test_app.get('/search')
        assert response.status_code == 200
    
    def test_search_with_palm_code(self, test_app):
        """Test search by palm code"""
        response = test_app.get('/search?palm_code=CODE001')
        assert response.status_code == 200
        assert 'results' in response.json
    
    def test_palm_detail_not_found(self, test_app):
        """Test 404 for non-existent palm"""
        response = test_app.get('/palm/99999', expect_errors=True)
        assert response.status_code == 404

class TestAdminViews:
    def test_admin_dashboard_unauthorized(self, test_app):
        """Test admin dashboard requires authentication"""
        response = test_app.get('/admin', expect_errors=True)
        assert response.status_code == 403
    
    def test_admin_dashboard_authorized(self, test_app, auth_headers):
        """Test admin dashboard with authentication"""
        response = test_app.get('/admin', headers=auth_headers)
        assert response.status_code == 200
        assert 'stats' in response.json
    
    def test_add_palm_validation(self, test_app, auth_headers):
        """Test palm creation with missing required fields"""
        response = test_app.post(
            '/admin/palms/add',
            {'palm_id': '', 'palm_code': ''},
            headers=auth_headers,
            expect_errors=True
        )
        assert response.status_code == 400
        assert 'error' in response.json
    
    def test_reports_generation(self, test_app, auth_headers):
        """Test report generation with filters"""
        params = {
            'start_date': '2024-01-01',
            'end_date': '2024-12-31',
            'section': 'Area A'
        }
        response = test_app.get('/admin/reports', params=params, headers=auth_headers)
        assert response.status_code == 200
        assert 'report_data' in response.json
Frontend (React + Vite)
javascript
// frontend/src/App.jsx
import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Home from './pages/Home';
import Search from './pages/Search';
import PalmDetail from './pages/PalmDetail';
import AdminLogin from './pages/admin/Login';
import AdminDashboard from './pages/admin/Dashboard';
import AdminPalms from './pages/admin/Palms';
import AdminReports from './pages/admin/Reports';

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/search" element={<Search />} />
        <Route path="/palm/:id" element={<PalmDetail />} />
        <Route path="/admin/login" element={<AdminLogin />} />
        <Route path="/admin" element={<AdminDashboard />} />
        <Route path="/admin/palms" element={<AdminPalms />} />
        <Route path="/admin/reports" element={<AdminReports />} />
      </Routes>
    </Router>
  );
}

// frontend/src/pages/Home.jsx
import React, { useState, useEffect } from 'react';
import { fetchStatistics } from '../services/api';
import StatsCards from '../components/StatsCards';
import SearchBar from '../components/SearchBar';

const Home = () => {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadStats();
  }, []);

  const loadStats = async () => {
    try {
      const data = await fetchStatistics();
      setStats(data);
    } catch (error) {
      console.error('Failed to load statistics:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-100">
      <header className="bg-green-600 text-white p-6">
        <h1 className="text-3xl font-bold">Palm Management System</h1>
        <p className="mt-2">Track and manage your palm profiles</p>
      </header>

      <main className="container mx-auto px-4 py-8">
        <SearchBar />
        
        {loading ? (
          <div className="text-center py-8">Loading statistics...</div>
        ) : (
          <StatsCards stats={stats} />
        )}
        
        <div className="mt-8">
          <h2 className="text-2xl font-semibold mb-4">Quick Search</h2>
          <div className="bg-white rounded-lg shadow p-6">
            <p>Use the search above or browse our database of {stats?.total_palms || 0} palms</p>
          </div>
        </div>
      </main>
    </div>
  );
};

// frontend/src/services/api.js
import axios from 'axios';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:6543';

const api = axios.create({
  baseURL: API_URL,
  withCredentials: true,
});

export const fetchStatistics = async () => {
  const response = await api.get('/api/statistics');
  return response.data;
};

export const searchPalms = async (params) => {
  const response = await api.get('/api/search', { params });
  return response.data;
};

export const getPalmDetail = async (id) => {
  const response = await api.get(`/api/palms/${id}`);
  return response.data;
};

// Admin APIs
export const adminLogin = async (credentials) => {
  const response = await api.post('/admin/login', credentials);
  return response.data;
};

export const adminAddPalm = async (palmData) => {
  const formData = new FormData();
  Object.keys(palmData).forEach(key => {
    if (key === 'images') {
      palmData[key].forEach(image => formData.append('images', image));
    } else {
      formData.append(key, palmData[key]);
    }
  });
  
  const response = await api.post('/admin/palms', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  });
  return response.data;
};

// frontend/src/__tests__/Home.test.jsx
import { render, screen, waitFor } from '@testing-library/react';
import Home from '../pages/Home';
import { fetchStatistics } from '../services/api';

jest.mock('../services/api');

describe('Home Component', () => {
  test('renders loading state initially', () => {
    fetchStatistics.mockResolvedValue(null);
    render(<Home />);
    expect(screen.getByText('Loading statistics...')).toBeInTheDocument();
  });

  test('renders statistics after loading', async () => {
    const mockStats = {
      total_palms: 100,
      total_harvest: 5000,
      average_age: 15
    };
    fetchStatistics.mockResolvedValue(mockStats);
    
    render(<Home />);
    
    await waitFor(() => {
      expect(screen.getByText('100')).toBeInTheDocument();
      expect(screen.getByText('Total Palms')).toBeInTheDocument();
    });
  });

  test('handles error state', async () => {
    fetchStatistics.mockRejectedValue(new Error('Failed to load'));
    render(<Home />);
    
    await waitFor(() => {
      expect(screen.getByText(/browse our database/i)).toBeInTheDocument();
    });
  });
});
Docker Configuration
dockerfile
# backend/Dockerfile
FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN pip install -e .

EXPOSE 6543

CMD ["pserve", "production.ini", "http_port=6543"]

# frontend/Dockerfile
FROM node:18-alpine as build

WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci

COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
Kubernetes Deployments
yaml
# k8s/deployments/backend-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: palm-backend
  namespace: palm-system
spec:
  replicas: 3
  selector:
    matchLabels:
      app: palm-backend
  template:
    metadata:
      labels:
        app: palm-backend
    spec:
      containers:
      - name: backend
        image: ${DOCKER_REGISTRY}/palm-backend:${BUILD_NUMBER}
        ports:
        - containerPort: 6543
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: palm-secrets
              key: database-url
        - name: S3_BUCKET
          value: palm-images-bucket
        - name: AWS_ACCESS_KEY_ID
          valueFrom:
            secretKeyRef:
              name: aws-credentials
              key: access-key-id
        - name: AWS_SECRET_ACCESS_KEY
          valueFrom:
            secretKeyRef:
              name: aws-credentials
              key: secret-access-key
        - name: SECRET_KEY
          valueFrom:
            secretKeyRef:
              name: palm-secrets
              key: secret-key
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 6543
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 6543
          initialDelaySeconds: 5
          periodSeconds: 5

# k8s/deployments/frontend-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: palm-frontend
  namespace: palm-system
spec:
  replicas: 2
  selector:
    matchLabels:
      app: palm-frontend
  template:
    metadata:
      labels:
        app: palm-frontend
    spec:
      containers:
      - name: frontend
        image: ${DOCKER_REGISTRY}/palm-frontend:${BUILD_NUMBER}
        ports:
        - containerPort: 80
        resources:
          requests:
            memory: "128Mi"
            cpu: "100m"
          limits:
            memory: "256Mi"
            cpu: "200m"

# k8s/services/backend-service.yaml
apiVersion: v1
kind: Service
metadata:
  name: palm-backend-service
  namespace: palm-system
spec:
  selector:
    app: palm-backend
  ports:
    - protocol: TCP
      port: 6543
      targetPort: 6543
  type: ClusterIP

# k8s/ingress/palm-ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: palm-ingress
  namespace: palm-system
  annotations:
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
spec:
  tls:
  - hosts:
    - palm.yourdomain.com
    - admin.palm.yourdomain.com
    secretName: palm-tls
  rules:
  - host: palm.yourdomain.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: palm-frontend-service
            port:
              number: 80
  - host: admin.palm.yourdomain.com
    http:
      paths:
      - path: /api
        pathType: Prefix
        backend:
          service:
            name: palm-backend-service
            port:
              number: 6543
Jenkins Pipeline
groovy
// jenkins/Jenkinsfile
pipeline {
    agent any
    
    environment {
        DOCKER_REGISTRY = 'your-registry.com'
        APP_NAME = 'palm-management'
        KUBECONFIG = credentials('kubeconfig')
    }
    
    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }
        
        stage('Backend Tests') {
            steps {
                dir('backend') {
                    sh 'python -m pip install -r requirements.txt'
                    sh 'python -m pip install pytest pytest-cov'
                    sh 'python -m pytest tests/ --cov=palm_app --cov-report=xml'
                }
            }
        }
        
        stage('Frontend Tests') {
            steps {
                dir('frontend') {
                    sh 'npm ci'
                    sh 'npm test -- --coverage'
                }
            }
        }
        
        stage('Build & Push Backend') {
            steps {
                dir('backend') {
                    script {
                        docker.build("${DOCKER_REGISTRY}/${APP_NAME}-backend:${BUILD_NUMBER}")
                        docker.withRegistry('https://your-registry.com', 'docker-credentials') {
                            docker.image("${DOCKER_REGISTRY}/${APP_NAME}-backend:${BUILD_NUMBER}").push()
                        }
                    }
                }
            }
        }
        
        stage('Build & Push Frontend') {
            steps {
                dir('frontend') {
                    script {
                        docker.build("${DOCKER_REGISTRY}/${APP_NAME}-frontend:${BUILD_NUMBER}")
                        docker.withRegistry('https://your-registry.com', 'docker-credentials') {
                            docker.image("${DOCKER_REGISTRY}/${APP_NAME}-frontend:${BUILD_NUMBER}").push()
                        }
                    }
                }
            }
        }
        
        stage('Deploy to K3s') {
            steps {
                script {
                    sh """
                        # Update image tags in deployments
                        sed -i 's|\${BUILD_NUMBER}|${BUILD_NUMBER}|g' k8s/deployments/*.yaml
                        
                        # Apply Kubernetes configurations
                        kubectl apply -f k8s/namespace.yaml
                        kubectl apply -f k8s/configmaps/
                        kubectl apply -f k8s/secrets/
                        kubectl apply -f k8s/deployments/
                        kubectl apply -f k8s/services/
                        kubectl apply -f k8s/ingress/
                        
                        # Wait for deployments to be ready
                        kubectl wait --for=condition=available --timeout=300s deployment/palm-backend -n palm-system
                        kubectl wait --for=condition=available --timeout=300s deployment/palm-frontend -n palm-system
                        
                        # Check deployment status
                        kubectl rollout status deployment/palm-backend -n palm-system
                        kubectl rollout status deployment/palm-frontend -n palm-system
                    """
                }
            }
        }
        
        stage('Smoke Tests') {
            steps {
                script {
                    // Perform smoke tests after deployment
                    sh """
                        # Get the ingress host
                        BACKEND_URL=\$(kubectl get ingress palm-ingress -n palm-system -o jsonpath='{.spec.rules[0].host}')
                        
                        # Test health endpoints
                        curl -f http://\$BACKEND_URL/api/health || exit 1
                        curl -f http://\$BACKEND_URL/ || exit 1
                        
                        # Test API functionality
                        curl -f http://\$BACKEND_URL/api/statistics || exit 1
                    """
                }
            }
        }
    }
    
    post {
        success {
            // Notify on success
            emailext(
                subject: "✅ Deployment Successful: ${APP_NAME} - Build #${BUILD_NUMBER}",
                body: "The deployment of ${APP_NAME} build #${BUILD_NUMBER} was successful.",
                to: 'team@example.com'
            )
        }
        failure {
            // Notify on failure and rollback
            emailext(
                subject: "❌ Deployment Failed: ${APP_NAME} - Build #${BUILD_NUMBER}",
                body: "The deployment of ${APP_NAME} build #${BUILD_NUMBER} failed. Rolling back...",
                to: 'team@example.com'
            )
            
            script {
                // Rollback to previous version
                if (env.BUILD_NUMBER.toInteger() > 1) {
                    sh """
                        PREV_BUILD=\$((BUILD_NUMBER - 1))
                        kubectl rollout undo deployment/palm-backend -n palm-system
                        kubectl rollout undo deployment/palm-frontend -n palm-system
                    """
                }
            }
        }
        always {
            // Clean up old images
            cleanWs()
        }
    }
}
Database Migration (Alembic)
python
# backend/alembic/versions/001_initial_schema.py
"""initial schema

Revision ID: 001
Create Date: 2024-01-01
"""
from alembic import op
import sqlalchemy as sa

def upgrade():
    # Create palm_profiles table
    op.create_table(
        'palm_profiles',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('palm_id', sa.String(50), nullable=False),
        sa.Column('palm_code', sa.String(50), nullable=False),
        sa.Column('plant_date', sa.DateTime(), nullable=False),
        sa.Column('donner_name', sa.String(100)),
        sa.Column('donner_phone_number', sa.String(20)),
        sa.Column('harvest_amount', sa.Float()),
        sa.Column('last_harvest', sa.DateTime()),
        sa.Column('age', sa.Integer()),
        sa.Column('images', sa.JSON()),
        sa.Column('area', sa.String(100)),
        sa.Column('section', sa.String(100)),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('palm_id'),
        sa.UniqueConstraint('palm_code')
    )
    
    # Create indexes for search performance
    op.create_index('ix_palm_code', 'palm_profiles', ['palm_code'])
    op.create_index('ix_donner_name', 'palm_profiles', ['donner_name'])
    op.create_index('ix_donner_phone', 'palm_profiles', ['donner_phone_number'])
    
    # Create users table
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('email', sa.String(100), nullable=False),
        sa.Column('password_hash', sa.String(255), nullable=False),
        sa.Column('full_name', sa.String(100)),
        sa.Column('is_admin', sa.Boolean(), default=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email')
    )
    
    # Create site_visits table
    op.create_table(
        'site_visits',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('ip_address', sa.String(45)),
        sa.Column('user_agent', sa.String(255)),
        sa.Column('page_visited', sa.String(255)),
        sa.Column('visited_at', sa.DateTime(), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id')
    )

def downgrade():
    op.drop_table('site_visits')
    op.drop_table('users')
    op.drop_table('palm_profiles')
Setup Instructions
Initialize the project:

bash
# Create project directory
mkdir palm-management-system
cd palm-management-system

# Initialize backend
cd backend
python -m venv venv
source venv/bin/activate
pip install pyramid sqlalchemy alembic psycopg2-binary boto3
pip install -e .

# Initialize frontend
cd ../frontend
npm create vite@latest . -- --template react
npm install axios react-router-dom @tanstack/react-query
Configure environment variables:

bash
# .env file
DATABASE_URL=postgresql://user:password@localhost:5432/palmdb
S3_BUCKET=palm-images-bucket
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
SECRET_KEY=your-secret-key
Run database migrations:

bash
alembic upgrade head
Seed initial data:

python
# seed_data.py
from palm_app.models.palm import PalmProfile, User
import random
from datetime import datetime, timedelta

def seed_palms(session, count=100):
    for i in range(count):
        palm = PalmProfile(
            palm_id=f'P{i:04d}',
            palm_code=f'CODE{i:04d}',
            plant_date=datetime.now() - timedelta(days=random.randint(365, 3650)),
            donner_name=f'Donor {i}',
            donner_phone_number=f'050{i:07d}',
            harvest_amount=random.uniform(100, 1000),
            age=random.randint(1, 20),
            area=random.choice(['Area A', 'Area B', 'Area C']),
            section=random.choice(['North', 'South', 'East', 'West'])
        )
        session.add(palm)
    session.commit()
Deploy to K3s:

bash
# Apply Kubernetes manifests
kubectl apply -f k8s/namespace.yaml
kubectl create secret generic palm-secrets \
  --from-literal=database-url='postgresql://...' \
  --from-literal=secret-key='your-secret' \
  -n palm-system

# Deploy application
kubectl apply -f k8s/deployments/
kubectl apply -f k8s/services/
kubectl apply -f k8s/ingress/