FROM tiangolo/uvicorn-gunicorn-fastapi:python3.7

RUN pip install mkdocs-material 
RUN python3.7 -m pip install mkdocstrings
# Copy the cleanair package into the container and install
COPY cleanair /apps/cleanair
RUN pip install -e '/apps/cleanair[models, dashboard]'

# Install traffic app
COPY odysseus /apps/odysseus
RUN pip install -e '/apps/odysseus'

# Copy the API into the container
COPY urbanair /apps/urbanair
RUN pip install -e '/apps/urbanair'

COPY docs /app/docs
COPY mkdocs.yml /app/mkdocs.yml
RUN mkdocs build -d /apps/urbanair/urbanair/packages