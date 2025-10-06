

# PersonalProject_OzonAPI

## Overview

PersonalProject_OzonAPI is a Django-based web application for integrating with the Ozon API, providing data synchronization, analytics, and management tools for Ozon marketplace sellers. The project leverages Celery for background tasks, Redis for caching and task brokering, and PostgreSQL for persistent storage.

---

## Architecture

- **Backend:** Django 4.x (Python 3.10+)
- **Database:** PostgreSQL 15
- **Cache/Broker:** Redis
- **Task Queue:** Celery
- **Web Server:** Gunicorn (production), Django dev server (local)
- **Reverse Proxy:** Nginx (production)
- **Frontend:** Django templates, static files (CSS/JS)

---

## Requirements

- Python 3.10+
- Django 4.x
- PostgreSQL 15
- Redis
- Celery
- Docker & Docker Compose (for containerized deployment)

---

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/Djonsinere/PersonalProject_OzonAPI.git
cd PersonalProject_OzonAPI
```

### 2. Set Up Python Environment

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

### 3. Set Up PostgreSQL and Redis

#### macOS (with Homebrew):

```bash
brew services start postgresql@15
brew services start redis
```

#### Create Database and User

```bash
psql -U postgres
# In psql shell:
CREATE DATABASE local_db;
CREATE USER local_user WITH PASSWORD 'local_pass';
GRANT ALL PRIVILEGES ON DATABASE local_db TO local_user;
\q
```

### 4. Configure Environment Variables

Create a `.env` file in the `personalproject/` directory:

```
DEBUG=True
SECRET_KEY=your_secret_key
DB_NAME=local_db
DB_USER=local_user
DB_PASSWORD=local_pass
DB_HOST=localhost
DB_PORT=5432
REDIS_URL=redis://localhost:6379/0
```

### 5. Run Migrations

```bash
cd personalproject
python manage.py makemigrations personalproject_main
python manage.py migrate
```

### 6. Collect Static Files

```bash
python manage.py collectstatic
```

### 7. Create Superuser

```bash
python manage.py createsuperuser
```

---

## Usage

### Local Development

Start Redis server (if not already running):

```bash
redis-server --port 6379
```

Start Django development server:

```bash
python manage.py runserver
```

Start Celery worker and beat:

```bash
celery -A personalproject_main worker --loglevel=info
celery -A personalproject_main beat --loglevel=info
```

Access the app at [http://localhost:8000](http://localhost:8000)

---

## Project Structure

- `personalproject/` — Django project root
  - `personalproject_main/` — Main Django app
    - `models.py`, `views.py`, `tasks.py`, etc.
    - `ozon_api/` — Ozon API integration code
  - `static/` — Static files (CSS, JS, images)
  - `templates/` — HTML templates
- `docker-compose.yml`, `Dockerfile` — Containerization
- `requirements.txt` — Python dependencies

---

## Development

- Follow PEP8 and Django best practices
- Use feature branches for new features
- Run tests before submitting pull requests
- Use `.env` for local configuration (never commit secrets)

---

## Testing

Run all tests:

```bash
python manage.py test
```

---

## Deployment

### Docker Compose (Production)

1. Build and start containers:
   ```bash
   docker-compose up --build -d
   ```
2. Run migrations and create superuser:
   ```bash
   docker-compose exec web python manage.py makemigrations
   docker-compose exec web python manage.py migrate
   docker-compose exec web python manage.py createsuperuser
   ```
3. View logs:
   ```bash
   docker-compose logs web
   docker-compose logs celery
   docker-compose logs celery-beat
   docker-compose logs nginx
   docker logs postgres
   ```

### Manual (Gunicorn + Nginx)

1. Set `DJANGO_SETTINGS_MODULE=personalproject_main.production`
2. Run migrations, collectstatic, create superuser
3. Start Gunicorn and Nginx

---


## License

MIT License. See [LICENSE](LICENSE) for details.

```
DEBUG=False
SECRET_KEY='key'
DB_NAME='local_db'
DB_USER='local_user'
DB_PASSWORD='local_pass'
DB_HOST='localhost'
DB_PORT='5432'
```

## Useful Commands

## Docs

*To be added in the future.*

## License

MIT License. See [LICENSE](LICENSE) for details.
