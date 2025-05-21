# Makefile for managing Docker + Django project

.PHONY: run stop restart rebuild logs shell

# Run the Django app in Docker (builds if needed)
run:
	docker-compose up -d

# Stop the containers
stop:
	docker-compose down

# Restart the app (stop and then run again)
restart: stop run

# Rebuild the Docker image
rebuild:
	docker-compose down --volumes --remove-orphans
	docker-compose build
	docker-compose up -d

# View logs
logs:
	docker-compose logs -f

# Open a shell in the Django container
shell:
	docker-compose exec django bash

# Run migrations
migrate:
	docker-compose exec django python3 manage.py migrate

# Create a superuser
superuser:
	docker-compose exec django python3 manage.py createsuperuser

# Collect static files
collectstatic:
	docker-compose exec django python3 manage.py collectstatic --noinput


# Clean up Docker containers and images
clean:
	docker-compose down --volumes --remove-orphans
	docker system prune -f
	docker image prune -a -f

