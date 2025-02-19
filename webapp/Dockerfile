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

# Copy app.py to the working directory
COPY webapp/app.py .
COPY webapp/templates templates
COPY consumer/db_manager.py consumer/db_manager.py

# Expose port 5000
EXPOSE 5000

# Run the app.py script
CMD ["python", "app.py"]
