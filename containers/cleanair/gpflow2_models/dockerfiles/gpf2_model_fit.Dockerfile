# Use an official Python runtime as a parent image
FROM python:3.10

# Set the working directory to /app
WORKDIR /app

# Copy the gpflow2_models directory contents into the container
COPY gpflow2_models /app/gpflow2_models

# Install any needed packages specified
RUN pip install /app/gpflow2_models
RUN pip check

# run comand that upload training data in to the blob storage 
CMD urbanair_gpf2 model fit train 