FROM tiangolo/uvicorn-gunicorn-fastapi:python3.7

RUN pip install mkdocs-material==5.3.0 mkdocstrings==0.12.0

# Copy the cleanair package into the container and install
COPY cleanair /apps/cleanair
RUN pip install /apps/cleanair

# Copy the API into the container
COPY urbanair/requirements.txt /app
RUN pip install -r /app/requirements.txt
COPY urbanair/urbanair /app/app

RUN ls /app