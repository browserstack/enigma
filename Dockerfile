############################################################
# Dockerfile to run a Django-based web application
# Based on an AMI
############################################################
# Set the base image to use to Ubuntu
FROM python:3.11-slim-buster AS base

RUN DEBIAN_FRONTEND=noninteractive \
  apt-get update -y \
  && apt-get install --no-install-recommends -y \
  openssh-client curl procps git vim gcc linux-libc-dev libc6-dev build-essential\
  && apt-get clean \
  && apt-get autoremove -y

# Set env variables used in this Dockerfile (add a unique prefix, such as DOCKYARD)
RUN apt update && apt install -y netcat dnsutils

# Directory in container for all project files
ENV DOCKYARD_SRVHOME=/srv

# Local directory with project source
ENV DOCKYARD_SRC=code/bsops

# Directory in container for project source files
ENV DOCKYARD_SRVPROJ=$DOCKYARD_SRVHOME/$DOCKYARD_SRC

# Create application subdirectories
WORKDIR $DOCKYARD_SRVPROJ

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
RUN chmod a+x /tmp/entrypoint.sh
ENTRYPOINT ["/tmp/entrypoint.sh"]
