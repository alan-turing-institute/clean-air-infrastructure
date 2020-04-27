FROM cleanairdocker.azurecr.io/tensorflow/tensorflow-2.1.0

# Set the working directory to /app
WORKDIR /app

# Copy the cleanair directory contents into the container
COPY cleanair /app/cleanair/
COPY uatraffic /app/uatraffic/

# Install any needed packages specified in requirements.txt
# TODO: remove cache dir
RUN pip install '/app/cleanair'
RUN pip install '/app/uatraffic'

# Create directory for storing models
RUN mkdir /experiments

# Copy the run script into the container
COPY entrypoints/lockdown_train.py /app

# Run the entrypoint script when the container launches
ENTRYPOINT ["python", "/app/lockdown_train.py"]