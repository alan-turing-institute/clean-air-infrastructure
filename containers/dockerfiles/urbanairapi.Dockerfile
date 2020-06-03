FROM python:3.7

# Copy the cleanair package into the container and install
COPY cleanair /app/cleanair
RUN pip install /app/cleanair

# Install traffic app
COPY odysseus /app/odysseus
RUN pip install /app/odysseus


# Copy the API into the container
COPY urbanair /var/www/html/urbanair

# Install any needed packages specified in requirements.txt
RUN pip install /var/www/html/urbanair

WORKDIR /var/www/html/urbanair

ENTRYPOINT ["/usr/local/bin/uwsgi", "--ini", "/var/www/html/urbanair/app_uwsgi.ini"]
