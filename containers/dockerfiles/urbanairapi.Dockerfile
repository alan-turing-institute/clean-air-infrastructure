FROM tiangolo/uvicorn-gunicorn-fastapi:python3.7

RUN pip install mkdocs-material==5.3.0 mkdocsstring==0.12.0
# Copy the cleanair package into the container and install
COPY cleanair /apps/cleanair
RUN pip install /apps/cleanair

# Install traffic app
COPY odysseus /apps/odysseus
RUN pip install /apps/odysseus

# Copy the API into the container
COPY urbanair /apps/urbanair
RUN pip install /apps/urbanair