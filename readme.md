# PersonalProject_OzonAPI

## Example usage (local)

```bash
git clone https://github.com/Djonsinere/PersonalProject_OzonAPI.git
cd ~/PersonalProject_OzonAPI/ && source .venv/bin/activate
brew services start postgresql@15 redis
psql -U username
    # In psql shell:
    CREATE DATABASE local_db;
    CREATE USER local_user WITH PASSWORD 'local_pass';
    GRANT ALL PRIVILEGES ON DATABASE local_db TO local_user;
    \q
cd personalproject && python manage.py makemigrations personalproject_main && python manage.py migrate
redis-server --port 6379
python manage.py runserver
celery -A personalproject_main worker --loglevel=info
celery -A personalproject_main beat --loglevel=info
```

## Example usage (production)

Before starting, add your domain or IP to `personalproject/personalproject_main/production.py`.

### Run with Django

```bash
DJANGO_SETTINGS_MODULE=stockmind.production python manage.py runserver
```

### Run with Docker Compose

```bash
docker-compose down
docker-compose up --build -d

docker-compose exec web python manage.py makemigrations
docker-compose exec web python manage.py migrate
docker-compose exec web python manage.py createsuperuser
```

### Viewing Logs

```bash
docker-compose logs web
docker-compose logs celery
docker-compose logs celery-beat
docker-compose logs nginx
docker logs postgres
```

## Project Structure

- `personalproject/` — Django project root
  - `personalproject_main/` — Main Django app
    - `models.py`, `views.py`, `tasks.py`, etc.
    - `ozon_api/` — Ozon API integration code
  - `static/` — Static files (CSS, JS, images)
  - `templates/` — HTML templates

## Requirements

- Python 3.10+
- Django 4.x
- PostgreSQL 15
- Redis
- Celery

Install Python dependencies:
```bash
pip install -r requirements.txt
```

## Environment Variables

Create a `.env` file in the project root with the following variables:

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