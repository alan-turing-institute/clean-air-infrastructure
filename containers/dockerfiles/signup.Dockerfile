FROM tiangolo/uwsgi-nginx-flask:python3.8

COPY signup/ /app
RUN pip install -U pip && pip install /app
