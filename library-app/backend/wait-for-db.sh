#!/usr/bin/env bash
set -e

host="$1"
shift
cmd="$@"

echo "Waiting for Postgres to be ready on $host:5432..."
until pg_isready -h "$host" -p "5432"; do
  >&2 echo "Postgres is unavailable - sleeping"
  sleep 1
done

>&2 echo "Postgres is up! Executing command: $cmd"
exec $cmd
