FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app.py .

# Create directory for data files and set proper permissions (as root)
RUN mkdir -p /app/data && \
    touch /app/data/database.db /app/data/error.log && \
    chmod 666 /app/data/database.db /app/data/error.log

# Create a non-root user and switch to it
RUN useradd -m -u 1000 user
USER user

# Expose the port the app runs on
EXPOSE 5000

# Run the application
CMD ["python", "app.py"]