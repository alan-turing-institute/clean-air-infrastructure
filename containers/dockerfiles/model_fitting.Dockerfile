# Use an official tensorflow gpu runtime as a parent image
FROM cleanairdocker.azurecr.io/tf1_py37:latest

# Get the arg value of the git hash
ARG git_hash
ENV GIT_HASH=${git_hash}

# Stop git python errors
ENV GIT_PYTHON_REFRESH=quiet

# Set the working directory to /app
WORKDIR /app

# Copy the cleanair directory contents into the container
COPY cleanair /app/cleanair
COPY scripts/ /app/scripts

# Install cleanair
RUN pip install '/app/cleanair'
