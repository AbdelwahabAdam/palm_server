# Palm Management System

A full-stack application for tracking and managing palm profiles. Built with Pyramid (Python), React + Vite, PostgreSQL, AWS S3, and SMTP email.

## Architecture

```
palm/
├── backend/          # Pyramid API (port 6543)
├── frontend/         # React + Vite + Tailwind (port 80 via nginx)
├── docker-compose.yml
├── .env.example
└── README.md
```

## Quick Start (Docker)

### 1. Configure environment

```bash
cp .env.example .env
```

Edit `.env` and fill in your **S3** and **SMTP** credentials (see [Environment Variables](#environment-variables) below).

### 2. Start all services

```bash
docker-compose up --build
```

This starts:
- **Frontend**: http://localhost (port 80)
- **Backend API**: http://localhost:6543
- **PostgreSQL**: localhost:5432

Migrations run automatically on backend startup.

### 3. Seed the database

In a separate terminal, after services are healthy:

```bash
docker-compose exec backend python seed_data.py
```

This creates:
- Admin user: `admin@gmail.com` / `Admin123`
- ~75 sample palm profiles

### 4. Log in

Go to http://localhost/admin/login and sign in with the admin credentials above.

## Local Development (without Docker)

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
pip install -e .

# Start PostgreSQL locally, then export env vars (see .env.example)
export DATABASE_URL=postgresql://palmuser:palmpass@localhost:5432/palmdb
export SECRET_KEY=dev-secret-key
# export S3_BUCKET, AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, SMTP_* as needed

alembic upgrade head
python seed_data.py

pserve development.ini
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend dev server runs at http://localhost:3000 with API proxy to backend.

## Environment Variables

Copy `.env.example` to `.env` and configure:

| Variable | Description | Required |
|----------|-------------|----------|
| `DATABASE_URL` | PostgreSQL connection string | Yes |
| `SECRET_KEY` | Pyramid session/auth secret | Yes |
| `S3_BUCKET` | AWS S3 bucket name for palm images | No (local fallback) |
| `AWS_ACCESS_KEY_ID` | AWS access key | No (local fallback) |
| `AWS_SECRET_ACCESS_KEY` | AWS secret key | No (local fallback) |
| `AWS_REGION` | AWS region (default: `us-east-1`) | No |
| `UPLOAD_DIR` | Local image storage path (default: `/app/uploads`) | No |
| `SMTP_HOST` | SMTP server hostname | Yes (for password reset) |
| `SMTP_PORT` | SMTP port (default: `587`) | No |
| `SMTP_USER` | SMTP username | Yes (for password reset) |
| `SMTP_PASSWORD` | SMTP password / app password | Yes (for password reset) |
| `SMTP_FROM` | From email address | No |
| `SMTP_USE_TLS` | Enable TLS (default: `true`) | No |
| `FRONTEND_URL` | Public frontend URL for reset links | Yes |

### Image Storage

- If **S3 credentials are configured**, images upload to AWS S3.
- If **S3 is not configured**, images are stored locally in the `palm_uploads` Docker volume and served from `/api/uploads/...`.

### AWS S3 Setup (optional)

1. Create an S3 bucket in your AWS account
2. Configure IAM credentials with `s3:PutObject`, `s3:DeleteObject`, `s3:GetObject` permissions
3. Set bucket CORS if accessing images directly from browser
4. Set `S3_BUCKET`, `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY` in `.env`

### SMTP Setup (Gmail example)

1. Enable 2FA on your Google account
2. Generate an [App Password](https://myaccount.google.com/apppasswords)
3. Set:
   ```
   SMTP_HOST=smtp.gmail.com
   SMTP_PORT=587
   SMTP_USER=your-email@gmail.com
   SMTP_PASSWORD=your-16-char-app-password
   SMTP_FROM=your-email@gmail.com
   FRONTEND_URL=http://localhost
   ```

## API Endpoints

### Public
| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Health check |
| GET | `/ready` | Readiness (DB connected) |
| GET | `/api/statistics` | Dashboard statistics |
| GET | `/api/search` | Search palms |
| GET | `/api/palms/{id}` | Palm detail |

### Auth
| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/admin/login` | Admin login |
| POST | `/api/admin/logout` | Admin logout |
| POST | `/api/admin/password-reset/request` | Request reset email |
| POST | `/api/admin/password-reset/confirm` | Confirm reset with token |

### Admin (requires auth)
| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/admin/dashboard` | Admin dashboard |
| GET | `/api/admin/palms` | List palms |
| POST | `/api/admin/palms` | Create palm (multipart) |
| GET | `/api/admin/palms/{id}` | Get palm |
| PUT | `/api/admin/palms/{id}` | Update palm |
| DELETE | `/api/admin/palms/{id}` | Delete palm |
| GET | `/api/admin/reports` | Generate reports |
| GET | `/api/admin/visits` | Site visit log |

## Running Tests

### Backend

```bash
cd backend
pip install -r requirements.txt
pytest
```

### Frontend

```bash
cd frontend
npm install
npm test
```

## Admin Credentials

| Field | Value |
|-------|-------|
| Email | `admin@gmail.com` |
| Password | `Admin123` |

Created by `seed_data.py`. Change the password after first login in production.

## Database Migrations

```bash
# Apply migrations
cd backend
alembic upgrade head

# Create new migration after model changes
alembic revision --autogenerate -m "description"
```

## Seed Data

```bash
# Via Docker
docker-compose exec backend python seed_data.py

# Locally
cd backend
DATABASE_URL=postgresql://... python seed_data.py
```

The seed script is idempotent — it skips existing admin and palms.

## Troubleshooting

- **403 on admin pages**: Log in at `/admin/login` first; cookies require `withCredentials`
- **S3 upload fails**: Verify bucket name, IAM permissions, and region in `.env`
- **Password reset email not sent**: Check SMTP settings; emails are logged if SMTP is not configured
- **Backend won't start**: Ensure PostgreSQL is running and `DATABASE_URL` is correct
