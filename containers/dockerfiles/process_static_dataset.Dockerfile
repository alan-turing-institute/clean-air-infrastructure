FROM continuumio/miniconda3




RUN echo "source activate env" > ~/.bashrc
ENV PATH /opt/conda/envs/env/bin:$PATH
# # Install psql, python and pip
# ENV DEBIAN_FRONTEND=noninteractive
# RUN apt-get update && apt-get install -y \
#     postgresql \
#     python3-pip
RUN conda install -c conda-forge gdal
# # Upgrade pip
# RUN pip3 install --upgrade pip

# Set the working directory to /app
WORKDIR /app

# Copy the cleanair directory contents into the container
COPY cleanair /tmp/cleanair

# Install any needed packages specified in requirements.txt
RUN pip install '/tmp/cleanair[setup]'

# # # Copy the run script into the container
COPY entrypoints/insert_static_datasets.py /app

# # # Run the entrypoint script when the container launches
ENTRYPOINT ["python", "insert_static_datasets.py"]
