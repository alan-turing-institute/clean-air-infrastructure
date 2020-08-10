# Use an official tensorflow gpu runtime as a parent image
FROM python:3.7

# Get the arg value of the git hash
ARG git_hash
ENV GIT_HASH=${git_hash}

# Stop git python errors
ENV GIT_PYTHON_REFRESH=quiet

# Set the working directory to /app
WORKDIR /app

# Copy the cleanair directory contents into the container
COPY cleanair /app/cleanair

# Install any needed packages - note tensorflow-gpu 1.15.0 is already installed
RUN pip install tensorflow==1.15.0
RUN pip install gpflow==1.5.1
RUN pip install '/app/cleanair'

# Run the entrypoint
ENTRYPOINT [ "urbanair", "model", "fit", "mrdgp" ]
