ARG git_hash
FROM cleanairdocker.azurecr.io/cleanair:${git_hash}
COPY urbanair/ /modules/urbanair/
RUN pip install -e /modules/urbanair/

# Set the working directory to /scripts
WORKDIR /scripts

# Copy the jamcam entrypoints into the container
COPY entrypoints/jamcam_processing /scripts