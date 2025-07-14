# BookSelf Backend

A Django-based backend application for a book/article sharing platform with user authentication, article management, collections, and notebook functionality.

## Features

- **User Authentication**: Google OAuth2 integration, email verification, session-based authentication
- **Article Management**: Create, edit, publish articles with draft functionality
- **Collections**: Organize articles into collections
- **Notebooks**: Create structured notebooks with pages
- **Social Features**: Follow users, like articles, comments system
- **GraphQL API**: Modern API with Strawberry GraphQL
- **Vector Search**: PostgreSQL with pgvector for semantic search
- **File Storage**: AWS S3 integration for media files
- **Background Tasks**: Celery with Redis for async processing

## Tech Stack

- **Backend**: Django 5.0.6, Django REST Framework
- **Database**: PostgreSQL with pgvector extension
- **Authentication**: Django Sessions, Google OAuth2
- **API**: GraphQL (Strawberry), REST API
- **Storage**: AWS S3 for media files
- **Cache/Queue**: Redis, Celery
- **Containerization**: Docker

## Prerequisites

- Python 3.11+
- PostgreSQL with pgvector extension
- Redis server
- AWS S3 bucket (for file storage)
- Google OAuth2 credentials

## Setup

### 1. Virtual Environment
Create and activate a virtual environment:
```bash
python3 -m venv env

# On Windows
env\Scripts\activate

# On macOS/Linux
source env/bin/activate
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Environment Variables
Create a `.env` file in the project root:
```env
# CSRF & Sessions
CSRF_ALLOW_ORIGIN=http://127.0.0.1:3000
CSRF_COOKIE_DOMAIN=127.0.0.1
SESSION_COOKIE_DOMAIN=127.0.0.1

# Frontend
BASE_FRONTEND_URL=http://127.0.0.1:3000

# Google OAuth2
GOOGLE_OAUTH2_CLIENT_ID=your_google_client_id
GOOGLE_OAUTH2_CLIENT_SECRET=your_google_client_secret

# AWS S3
AWS_ACCESS_KEY_ID=your_aws_access_key
AWS_SECRET_ACCESS_KEY=your_aws_secret_key
AWS_STORAGE_BUCKET_NAME=your_s3_bucket_name
AWS_S3_REGION_NAME=us-east-1

# Database
POSTGRES_DB=your_postgres_db
POSTGRES_USER=your_postgres_user
POSTGRES_PASSWORD=your_postgres_password
POSTGRES_HOST=127.0.0.1
POSTGRES_PORT=5432

# Email
EMAIL_HOST_USER=your_email@gmail.com
EMAIL_HOST_PASSWORD=your_app_password
```

### 4. Database Setup
Ensure PostgreSQL is running and create the database:
```bash
createdb pagekeep
```

Run migrations:
```bash
python manage.py migrate
```

### 5. Create Superuser
```bash
python manage.py createsuperuser
```

### 6. Start Redis Server
```bash
redis-server
```

### 7. Start Celery Worker (Optional)
In a separate terminal:
```bash
celery -A backend worker --loglevel=info
```

## Running the Application

### Development Server
```bash
python manage.py runserver 0.0.0.0:8000
```

### Using Docker
```bash
docker-compose up -d redis  # Start Redis
docker build -t bookself-backend .
docker run -p 8000:8000 bookself-backend
```

### GraphQL API
Access the GraphQL interface at: `http://localhost:8000/graphql/`


## Authentication

The application supports multiple authentication methods:
- Google OAuth2 (primary)
- Email verification system
- Django session-based authentication

## Admin Interface

Access the admin interface at `http://localhost:8000/admin/`


## API Documentation

Detailed API documentation is available at: https://documenter.getpostman.com/view/38819876/2sAYJ6BK58

## Development

### Running Tests
```bash
python manage.py test
```

## Deployment

### Production Settings
- Set `DEBUG=False`
- Configure proper CORS settings
- Set up SSL certificates
- Configure production database
- Set up proper logging

### Docker Deployment
```bash
docker-compose up -d
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License.