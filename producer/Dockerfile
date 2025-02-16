# Use the official Python 3.10 slim image
FROM python:3.10-slim

# Install Poetry
RUN pip install --no-cache-dir poetry

# Switch working directory
WORKDIR /app

# Copy only the Poetry files first to leverage Docker caching
COPY pyproject.toml poetry.lock* /app/

# Install dependencies using Poetry and pip
RUN poetry export --without-hashes --format=requirements.txt > requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of your application code (e.g., producer.py)
COPY producer.py .

# Run the producer.py script
CMD ["python", "producer.py"]

