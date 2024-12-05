# Use an official Python runtime as a parent image
FROM python:3.10

# Update certificates
RUN apt update \
    && apt install -y \
    build-essential \
    ca-certificates \
    cmake \
    gfortran \
    libgeos-dev

# download eccodes for ECMWF satellite
WORKDIR /app
ENV ECCODES_MAJOR_VERSION=2
ENV ECCODES_MINOR_VERSION=26
ENV ECCODES_PATCH_VERSION=0
ENV ECCODES_VERSION=${ECCODES_MAJOR_VERSION}.${ECCODES_MINOR_VERSION}.${ECCODES_PATCH_VERSION}
ENV ECCODES_SRC_DIR=eccodes-${ECCODES_VERSION}-Source
ENV ECCODES_TAR_NAME=eccodes-${ECCODES_VERSION}-Source.tar.gz
RUN wget -c https://confluence.ecmwf.int/download/attachments/45757960/${ECCODES_TAR_NAME}
RUN tar -xzf ${ECCODES_TAR_NAME}

# install eccodes with CMake
RUN mkdir ${ECCODES_SRC_DIR}/build
WORKDIR ${ECCODES_SRC_DIR}/build
RUN cmake -DENABLE_AEC=OFF ..
RUN cmake --build .
RUN cmake --install .

# remove eccodes build directory
WORKDIR /app
RUN rm -r ${ECCODES_SRC_DIR}/build