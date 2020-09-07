FROM tiangolo/uvicorn-gunicorn-fastapi:python3.7

RUN pip install mkdocs-material==5.3.0 mkdocstrings==0.12.0

# Copy the cleanair package into the container and install
COPY cleanair /apps/cleanair
RUN pip install '/apps/cleanair'

#  Install urbanair.  Have to make editable for static files to work
COPY urbanair/ /modules/urbanair/
RUN pip install -e /modules/urbanair/

# Build the documentation
COPY docs /app/docs
RUN mkdocs build -d /modules/urbanair/urbanair/docs/dev -f /app/docs/dev/mkdocs.yml
RUN mkdocs build -d /modules/urbanair/urbanair/docs/urbanair -f /app/docs/urbanair/mkdocs.yml