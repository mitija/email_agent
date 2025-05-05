# This script will reset the database migrations for the email agent project.
# It will also create a superuser with username admin and password mitija
# Usage: ./reset_migrations.sh
#
rm -rf db.sqlite3
find . -path "*/migrations/*.py" -not -name "__init__.py" -delete
./manage.py makemigrations
./manage.py migrate
DJANGO_SUPERUSER_PASSWORD=mitija ./manage.py createsuperuser --username admin --email admin@yopmail.com --noinput
