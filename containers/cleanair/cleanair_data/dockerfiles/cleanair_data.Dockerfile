# Use an official Python runtime as a parent image
FROM python:3.10
RUN pip install geoalchemy2==0.9.3 
RUN pip install sqlalchemy==1.4.23  

# Set the working directory to /app
WORKDIR /app

# Copy the cleanair directory contents into the container
COPY cleanair_data /app/cleanair_data

# Install any needed packages specified
RUN pip install /app/cleanair_data
RUN pip check

# run comand that upload training data in to the blob storage 
CMD urbanair_db dataset upload-bl .