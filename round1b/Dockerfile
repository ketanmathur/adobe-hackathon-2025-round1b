FROM python:3.9-slim

# Install dependencies
RUN apt-get update && apt-get install -y build-essential

WORKDIR /app

# Copy all source code
COPY . .

# Install Python packages
RUN pip install --no-cache-dir -r requirements.txt

# Run pipeline
CMD ["python", "pipeline.py"]
