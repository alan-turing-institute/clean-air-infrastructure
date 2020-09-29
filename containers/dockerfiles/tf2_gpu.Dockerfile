FROM tensorflow/tensorflow:2.2.0-gpu

CMD nvidia-smi#set up environment

RUN apt-get update && apt-get install --no-install-recommends --no-install-suggests -y curl

RUN apt-get -y install software-properties-common

RUN apt-get -y install unzip

RUN add-apt-repository ppa:deadsnakes/ppa

RUN apt-get -y install python3.7

RUN update-alternatives --install /usr/bin/python python /usr/bin/python3.7 1

RUN update-alternatives  --set python /usr/bin/python3.7

# Set Python 3.7 as 'python'
RUN ln -sf /usr/bin/python /usr/local/bin/python

RUN curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py

RUN python get-pip.py
RUN pip install --upgrade keyrings.alt 
RUN pip install -U pip


# Install TF and gpflow
RUN pip install tensorflow==2.2.0 gpflow==2.1.1