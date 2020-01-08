FROM nginx

COPY . /var/www/html/my_app
WORKDIR /var/www/html/my_app

COPY nginx.conf /etc/nginx/nginx.conf

COPY supervisord.conf /etc/supervisord.conf

RUN apt-get update && apt-get install -y python3 python3-pip 

# Install any needed packages specified in requirements.txt
RUN pip3 install --trusted-host pypi.python.org -r requirements.txt

### Run the development server
# CMD [ "python3", "./App.py"] 

### Run on uwsgi
# CMD [ "uwsgi", "--ini", "app.ini" ] 

### Run on Nginx
ENTRYPOINT ["/usr/local/bin/supervisord"]