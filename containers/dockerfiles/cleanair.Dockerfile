# key dependencies are already installed in the base image
ARG  CLEANAIR_BASE_TAG=latest
FROM cleanairdocker.azurecr.io/cleanair_base:${CLEANAIR_BASE_TAG}

# Set the working directory to /app
WORKDIR /app

# Copy the cleanair directory contents into the container
COPY cleanair /app/cleanair
COPY scripts/ /app/scripts

# set the version of cleanair
ARG urbanair_version
ENV SETUPTOOLS_SCM_PRETEND_VERSION ${urbanair_version}

# Install packages
RUN pip install "/app/cleanair" pyopenssl
