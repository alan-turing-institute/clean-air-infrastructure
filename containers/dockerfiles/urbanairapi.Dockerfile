FROM tiangolo/uvicorn-gunicorn-fastapi:python3.7

RUN pip install mkdocs-material==5.3.0 mkdocstrings==0.12.0

# Copy the cleanair package into the container and install
COPY cleanair /apps/cleanair
RUN pip install /apps/cleanair

# Install package
COPY urbanair /urbanair_package
RUN pip install /urbanair_package

# But copy the contents to here as we only install package to get dependencies
COPY urbanair/urbanair /app/app

