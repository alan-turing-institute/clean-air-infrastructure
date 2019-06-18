
FROM osgeo/gdal:ubuntu-full-latest

# Install jq for parsing json files
RUN apt-get update && apt-get install -y \
    jq \
    apt-transport-https \ 
    python3 \
    python3-pip \
    libpq-dev

RUN pip3 install --upgrade pip
# Copy the current directory contents into the container at /app
COPY . /app

# Install any needed packages specified in requirements.txt
RUN pip3 install --trusted-host pypi.python.org -r app/requirements.txt


ENTRYPOINT ["/bin/bash", "/app/insert_gdb_file_to_postGIS.sh"]


