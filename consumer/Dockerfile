# Use the official Python 3.10 slim image
FROM python:3.10-slim

# Install Poetry
RUN pip install --no-cache-dir poetry==1.8.4

# Switch working directory
WORKDIR /app

# Copy only the Poetry files first to leverage Docker caching
COPY pyproject.toml poetry.lock* /app/

# Install dependencies using Poetry and pip
RUN poetry export --without-hashes --format=requirements.txt > requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of your application code (e.g., consumer.py)
COPY consumer/consumer.py .
COPY consumer/db_manager.py .

# Run the consumer.py script
CMD ["python", "consumer.py"]

