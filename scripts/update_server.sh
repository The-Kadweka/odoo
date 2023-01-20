#/bin/sh
set -e
git pull origin main
docker build -t auraska:16.0 .
docker-compose down
docker-compose up -d
docker system prune -f
