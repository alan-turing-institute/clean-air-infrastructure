FROM python:3.7

COPY . /tmp/containers
RUN pip install /tmp/containers

COPY requirements.txt /var/www/html/my_app/requirements.txt
COPY API /var/www/html/my_app

# Install any needed packages specified in requirements.txt
RUN pip install --trusted-host pypi.python.org -r var/www/html/my_app/api-requirements.txt
RUN pip install --trusted-host pypi.python.org -r var/www/html/my_app/requirements.txt

WORKDIR /var/www/html/my_app

### Run on Nginx
ENTRYPOINT ["/usr/local/bin/uwsgi", "--ini", "/var/www/html/my_app/app_uwsgi.ini"]