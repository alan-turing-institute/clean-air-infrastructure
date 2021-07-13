ARG git_hash
FROM cleanairdocker.azurecr.io/cleanair:${git_hash}
COPY urbanair/ /modules/urbanair/

# set the version of cleanair
ARG urbanair_version
ENV SETUPTOOLS_SCM_PRETEND_VERSION ${urbanair_version}

RUN pip install -e /modules/urbanair/

# Set the working directory to /scripts
WORKDIR /scripts

# Copy the jamcam entrypoints into the container
COPY entrypoints/jamcam_processing /scripts