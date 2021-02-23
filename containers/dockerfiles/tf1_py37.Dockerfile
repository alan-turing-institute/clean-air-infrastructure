FROM python:3.7

RUN apt-get update && apt-get install -y python3.7-dev

# Install any needed packages - move to top for better caching
RUN pip install tensorflow==1.15.0
RUN pip install gpflow==1.5.1
