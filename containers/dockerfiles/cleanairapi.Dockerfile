FROM python:3.7

# Copy the cleanair package into the container and install
COPY cleanair /app/cleanair
RUN pip install /app/cleanair

# Copy the API into the container
COPY API /var/www/html/my_app

# Install any needed packages specified in requirements.txt
RUN pip install --trusted-host pypi.python.org -r var/www/html/my_app/api-requirements.txt

WORKDIR /var/www/html/my_app

ENTRYPOINT ["/usr/local/bin/uwsgi", "--ini", "/var/www/html/my_app/app_uwsgi.ini"]
