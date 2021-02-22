FROM nvidia/cuda:10.0-cudnn7-runtime-ubuntu18.04

CMD nvidia-smi#set up environment

RUN apt-get update && apt-get install --no-install-recommends --no-install-suggests -y curl

RUN apt-get -y install software-properties-common

RUN apt-get -y install unzip

RUN add-apt-repository ppa:deadsnakes/ppa

RUN apt-get -y install python3.7-dev

RUN update-alternatives --install /usr/bin/python python /usr/bin/python3.7 1

RUN update-alternatives  --set python /usr/bin/python3.7

RUN curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py

RUN python get-pip.py

# Install TF and gpflow
RUN pip install tensorflow-gpu==1.15.0
RUN pip install gpflow==1.5.1