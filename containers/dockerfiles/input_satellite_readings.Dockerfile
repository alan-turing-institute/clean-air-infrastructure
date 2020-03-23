# Use an official Python runtime as a parent image
FROM python:3.7

# Set the working directory to /app
WORKDIR /app

# Copy the cleanair directory contents into the container
COPY cleanair /app/cleanair

# Install any needed packages specified in requirements.txt
RUN pip install /app/cleanair

# Install pygrib
RUN apt-get update
RUN apt-get -y install cmake build-essential

RUN apt-get -y install gfortran
RUN wget --output-document eccodes-2.13.0-Source.tar.gz https://confluence.ecmwf.int/download/attachments/45757960/eccodes-2.13.0-Source.tar.gz?api=v2
RUN ls
RUN tar -xzf eccodes-2.13.0-Source.tar.gz
RUN ls eccodes-2.13.0-Source.tar.gz
RUN mkdir build ; cd build
RUN cd build && cmake -DENABLE_JPG=ON ../eccodes-2.13.0-Source && make && ctest && make install

RUN apt-cache search libgeos
RUN apt-get -y install libgeos-dev libgeos-3.7.1
RUN pip install https://github.com/matplotlib/basemap/archive/master.zip

RUN git clone https://github.com/jswhit/pygrib.git
RUN cd pygrib && mv setup.cfg.template setup.cfg
RUN pip install pygrib


# Copy the run script into the container
COPY entrypoints/input_satellite_readings.py /app

# Run the entrypoint script when the container launches
ENTRYPOINT ["python", "input_satellite_readings.py"]