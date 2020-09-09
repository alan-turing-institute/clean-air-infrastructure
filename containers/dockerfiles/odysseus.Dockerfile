# Use an official Python runtime as a parent image
FROM cleanairdocker.azurecr.io/tf23_py37:latest

# Set the working directory to /app
WORKDIR /app

# Copy the cleanair directory contents into the container
COPY cleanair /app/cleanair/
COPY odysseus /app/odysseus/

# Install any needed packages specified in requirements.txt
RUN pip install /app/cleanair
RUN pip install /app/odysseus
