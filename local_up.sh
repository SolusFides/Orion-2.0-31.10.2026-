#!/bin/bash
if ! [ -x "$(command -v docker)" ]; then
  echo 'Error: docker is not installed.' >&2
  exit 1
fi

cd "$(dirname "$0")"
[ -f api_gateway/.env ] || cp api_gateway/.env.example api_gateway/.env

echo "Building and starting Orion Home..."
docker compose up -d --build

echo ""
echo "Local machine is up!"
echo ""
echo "You can check API docs at: http://localhost:8000/docs"
echo ""
echo "Command to down all containers:"
echo "/bin/bash local_down.sh"
echo ""
