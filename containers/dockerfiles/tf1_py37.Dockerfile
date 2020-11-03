FROM python:3.7

# Install any needed packages - move to top for better caching
RUN pip install tensorflow==1.15.0
RUN pip install gpflow==1.5.1
