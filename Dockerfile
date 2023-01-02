############################################################
# Dockerfile to run a Django-based web application
# Based on an AMI
############################################################
# Set the base image to use to Ubuntu
FROM python:3.11-slim-buster AS base

RUN DEBIAN_FRONTEND=noninteractive \
  apt-get update -y \
  && apt-get install --no-install-recommends -y \
  openssh-client curl procps git vim gcc linux-libc-dev libc6-dev build-essential \
  && apt-get clean \
  && apt-get autoremove -y

# Set env variables used in this Dockerfile (add a unique prefix, such as DEV)
RUN apt update && apt install -y netcat dnsutils

RUN useradd -rm -d /home/app -s /bin/bash -g root -G sudo -u 1001 app
USER app

# Directory in container for all project files
ENV DEV_SRVHOME=/srv

# Local directory with project source
ENV DEV_SRC=code/dev

# Directory in container for project source files
ENV DEV_SRVPROJ=$DEV_SRVHOME/$DEV_SRC

# Create application subdirectories
WORKDIR $DEV_SRVPROJ

# Copy just requirements.txt
COPY requirements.txt /tmp/requirements.txt

# Install Python dependencies
RUN pip install -r /tmp/requirements.txt --no-cache-dir

COPY . .

FROM base as test
ENTRYPOINT [ "python" ]
CMD [ "-m", "pytest", "-v", "--cov", "--disable-warnings" ] 

FROM base as web
COPY ./docker-entrypoint.sh /tmp/entrypoint.sh
ENTRYPOINT ["/tmp/entrypoint.sh"]
