FROM python:3.9-slim

# Install system dependencies
RUN apt-get update && apt-get install -y wget unzip

# Set working directory
WORKDIR /app

# Copy project files
COPY . /app

# Install Python dependencies
RUN pip3 install -r requirements.txt

# Set entrypoint
CMD ["python", "main.py"]