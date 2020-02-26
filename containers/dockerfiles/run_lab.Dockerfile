
# Use python 3.7 and jupyter notebook as parent images
FROM jupyter/minimal-notebook
# FROM python:3.7

# Set the working directory to /app
WORKDIR /app

# Change user to allow permissions
USER root

# Copy the requirements file into the container
# -> this reduces rebuilding by separating code changes from dependency changes
COPY requirements.txt /app/requirements.txt
COPY setup.py /app/setup.py

# Copy the cleanair directory contents into the container
COPY cleanair /app/cleanair

# Copy the lab directory containing notebooks
COPY lab /app/lab

# Install any needed packages specified in requirements.txt
RUN pip install --trusted-host pypi.python.org -r requirements.txt

# Add the jupyter lab extension for dash
RUN jupyter labextension install jupyterlab-dash

# install cleanair
# RUN pip install -e /app/

CMD ["start-notebook.sh", "--port", "8888"]
