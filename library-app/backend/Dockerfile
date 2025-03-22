FROM python:3.8-slim

# Install psql client so we can use pg_isready
RUN apt-get update && apt-get install -y postgresql-client && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .

# Copy in wait-for-db script
COPY wait-for-db.sh .
RUN chmod +x wait-for-db.sh

# Instead of CMD ["python", "app.py"], we run our wait script, then app
CMD ["./wait-for-db.sh", "db", "python", "app.py"]