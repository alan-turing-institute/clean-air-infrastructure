# Use an official Python runtime as a parent image
FROM python:3

# Set the working directory to /app
WORKDIR /app

# Copy the datasources directory contents into the container
COPY datasources /app/datasources

# Install any needed packages specified in requirements.txt
RUN pip install --trusted-host pypi.python.org -r datasources/requirements.txt

# Copy the run script into the container
COPY entrypoints/update_scoot_database.py /app

# Run the entrypoint script when the container launches
ENTRYPOINT ["python", "update_scoot_database.py"]