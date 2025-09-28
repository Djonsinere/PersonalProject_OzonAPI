# Example usage local
`git clone https://github.com/Djonsinere/PersonalProject_OzonAPI.git`
`cd ~/PersonalProject_OzonAPI/ && source .venv/bin/activate`
`brew services start postgresql@15 redis`
`psql -U username`
    -`CREATE DATABASE local_db;`
    -`CREATE USER local_user WITH PASSWORD 'local_pass';`
    -`GRANT ALL PRIVILEGES ON DATABASE local_db TO local_user;`
    -`\q`
`cd personalproject && python manage.py makemigrations personalproject_main && python manage.py migrate`
`redis-server --port 6379`
`python manage.py runserver`
`celery -A personalproject_main worker --loglevel=info`
`celery -A personalproject_main beat --loglevel=info`

# Example usage production
future

## Docs
future