# Use an official Python runtime as a parent image
FROM python:3.7

# Set the working directory to /app
WORKDIR /app

# Copy the requirements file into the container
# -> this reduces rebuilding by separating code changes from dependency changes
COPY requirements.txt /app/requirements.txt

# Install any needed packages specified in requirements.txt
RUN pip install --trusted-host pypi.python.org -r requirements.txt

# Copy the cleanair directory contents into the container
COPY cleanair /app/cleanair

# Copy the run script into the container
COPY entrypoints/run_model_fitting.py /app

# Run the entrypoint script when the container launches
ENTRYPOINT ["python", "run_model_fitting.py"]
