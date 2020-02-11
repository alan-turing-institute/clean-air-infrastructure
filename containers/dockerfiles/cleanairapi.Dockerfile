FROM python:3.7

RUN apt-get update && apt-get install -y python3 python3-pip

COPY . /tmp/containers
RUN pip3 install /tmp/containers


COPY requirements.txt /var/www/html/my_app/requirements.txt
COPY API /var/www/html/my_app

# RUN ls /var/www/html/my_app
# RUN cat /etc/supervisord.conf
# RUN cat /etc/nginx/nginx.conf

# Install any needed packages specified in requirements.txt
RUN pip3 install --trusted-host pypi.python.org -r var/www/html/my_app/api-requirements.txt
RUN pip3 install --trusted-host pypi.python.org -r var/www/html/my_app/requirements.txt


WORKDIR /var/www/html/my_app

# ### Run the development server
# CMD [ "python3", "./wsgi.py"]

### Run on uwsgi
# CMD [ "uwsgi", "--ini", "app_nginx.ini" ]

### Run on Nginx
ENTRYPOINT ["/usr/local/bin/uwsgi", "--ini", "/var/www/html/my_app/app_nginx.ini"]