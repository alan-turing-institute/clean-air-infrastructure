# Use an official tensorflow gpu runtime as a parent image
FROM python:3.7

# Install any needed packages - move to top for better caching
RUN pip install tensorflow==1.15.0
RUN pip install gpflow==1.5.1

# Get the arg value of the git hash
ARG git_hash
ENV GIT_HASH=${git_hash}

# Stop git python errors
ENV GIT_PYTHON_REFRESH=quiet

# Set the working directory to /app
WORKDIR /app

# Copy the cleanair directory contents into the container
COPY cleanair /app/cleanair
COPY dockerfiles/svgp.sh /app/svgp.sh

# Install cleanair
RUN pip install '/app/cleanair'

# Run the entrypoint
ENTRYPOINT [ "sh", "/app/svgp.sh" ]
