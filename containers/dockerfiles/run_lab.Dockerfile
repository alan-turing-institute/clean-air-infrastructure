
# Use python 3.7 and jupyter notebook as parent images
FROM jupyter/minimal-notebook

# Set the working directory to /app
WORKDIR /app

EXPOSE 8888

# Change user to allow permissions
USER root

RUN apt-get update
RUN apt-get install -y curl
RUN curl -sL https://deb.nodesource.com/setup_13.x | sudo -E bash -
RUN apt-get install -y nodejs

# Copy the requirements file into the container
# -> this reduces rebuilding by separating code changes from dependency changes
COPY requirements.txt /app/requirements.txt
COPY setup.py /app/setup.py

# Copy the cleanair directory contents into the container
COPY cleanair /app/cleanair

# Copy the lab directory containing notebooks
COPY labs /app/labs

# Install any needed packages specified in requirements.txt
RUN pip install --trusted-host pypi.python.org -r requirements.txt

# Add the jupyter lab extension for dash
RUN jupyter labextension install jupyterlab-dash --no-build
RUN jupyter labextension install jupyterlab-plotly --no-build
RUN jupyter labextension install @jupyter-widgets/jupyterlab-manager --no-build
RUN jupyter labextension install plotlywidget

# install cleanair
WORKDIR /
RUN pip install -e app
WORKDIR /app

CMD ["start-notebook.sh", "--port", "8888"]
