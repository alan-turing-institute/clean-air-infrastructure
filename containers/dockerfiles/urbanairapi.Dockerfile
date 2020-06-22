FROM tiangolo/uvicorn-gunicorn-fastapi:python3.7

RUN pip install mkdocs-material 
RUN python3.7 -m pip install mkdocstrings

# Copy the cleanair package into the container and install
COPY cleanair /apps/cleanair
RUN pip install -e '/apps/cleanair[models, dashboard]'

#  Install urbanair.  Have to make editable for static files to work
COPY urbanair/ /modules/urbanair/
RUN pip install -e /modules/urbanair/


