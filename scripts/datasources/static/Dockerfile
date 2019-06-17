# Use an official Python runtime as a parent image
FROM osgeo/gdal:ubuntu-full-latest

# Install jq for parsing json files
RUN apt-get update && apt-get install -y \
    jq 


# Copy the current directory contents into the container at /app
COPY . /app

ENTRYPOINT ["/bin/bash", "/app/insert_gdb_file_to_postGIS.sh"]


