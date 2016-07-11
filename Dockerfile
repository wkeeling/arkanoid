FROM debian:jessie

MAINTAINER will@zifferent.com
ENV project platform

RUN apt-get update && \
    apt-get -y install apt-utils && \
    apt-get -y install build-essential && \
    apt-get -y install vim && \
    apt-get -y install git && \
    apt-get -y install mercurial && \
    apt-get -y install curl && \
    apt-get -y install zlib1g zlib1g-dev && \
    apt-get -y install libfreetype6-dev && \
    apt-get -y install python3 && \
    apt-get -y install python3-dev 

ADD sources.list /etc/apt/

RUN apt-get update 

RUN mknod /dev/fb0 c 29 0

ADD requirements.txt /${project}/

RUN \
    apt-get -y install python3-pip && \ 
    apt-get -y build-dep python-pygame && \ 
    cd /${project} && \
    pip3 install -r requirements.txt

RUN apt-get -y install x11-apps

COPY . /${project}/

WORKDIR /${project}

