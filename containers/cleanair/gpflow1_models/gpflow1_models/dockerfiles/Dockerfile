# Use TensorFlow 1.x base image since GPflow 1.x is being used
FROM tensorflow/tensorflow:1.15.5-py3

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    python3-pip \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first to leverage Docker cache
COPY requirements.txt .

# Install Python dependencies
RUN pip3 install --no-cache-dir -r requirements.txt

# Install GPflow 1.x
RUN pip3 install gpflow==1.5.1

# Copy the application code
COPY containers/cleanair/gpflow1_models /app/gpflow1_models

# Set Python path
ENV PYTHONPATH=/app

# Default command (can be overridden)
CMD ["python3"] 