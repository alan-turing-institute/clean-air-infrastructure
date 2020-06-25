# Use an official tensorflow gpu runtime as a parent image
FROM tensorflow/tensorflow:1.15.0-gpu-py3

# Set the working directory to /app
WORKDIR /app

# Copy the cleanair directory contents into the container
COPY cleanair /app/cleanair

# Install any needed packages - note tensorflow-gpu 1.15.0 is already installed
RUN pip install gpflow==1.5.1
RUN pip install '/app/cleanair'

# Copy the run script into the container
COPY entrypoints/model_fitting/model_fitting.py /app

# Run the entrypoint script when the container launches
ENTRYPOINT ["python", "model_fitting.py"]
