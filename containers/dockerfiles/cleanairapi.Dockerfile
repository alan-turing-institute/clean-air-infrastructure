FROM nginx

COPY containers/API/ /var/www/html/my_app
WORKDIR /var/www/html/my_app

# Copy the cleanair directory contents into the container
COPY cleanair /var/www/html/my_app

COPY containers/API/nginx.conf /etc/nginx/nginx.conf
COPY containers/API/supervisord.conf /etc/supervisord.conf

RUN apt-get update && apt-get install -y python3 python3-pip

# Install any needed packages specified in requirements.txt
RUN pip3 install --trusted-host pypi.python.org -r requirements.txt

### Run the development server
# CMD [ "python3", "./App.py"]

### Run on uwsgi
# CMD [ "uwsgi", "--ini", "app.ini" ]

### Run on Nginx
ENTRYPOINT ["/usr/local/bin/supervisord"]