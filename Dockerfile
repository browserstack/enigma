############################################################
# Dockerfile to run a Django-based web application
# Based on an AMI
############################################################
# Set the base image to use to Ubuntu
FROM python:3.11-slim-buster AS base

ENV DJANGO_SETTINGS_MODULE=BrowserStackAutomation.settings 
RUN DEBIAN_FRONTEND=noninteractive \
  apt-get update -y \
  && apt-get install --no-install-recommends -y \
  openssh-client curl procps git vim gcc linux-libc-dev libc6-dev build-essential \
  && apt-get clean \
  && apt-get autoremove -y

# Set env variables used in this Dockerfile (add a unique prefix, such as DEV)
RUN apt update && apt install -y netcat dnsutils libmariadbclient-dev
RUN useradd -rm -d /home/app -s /bin/bash -g root -G sudo -u 1001 app
WORKDIR /srv/code/dev
RUN mkdir -p logs
RUN chown -R app /srv/code/dev
USER app



# Copy just requirements.txt
COPY requirements.txt /tmp/requirements.txt
COPY config.json.sample config.json

# Install Python dependencies
RUN pip install -r /tmp/requirements.txt --no-cache-dir --ignore-installed

COPY --chown=app:root . .
FROM base as test
CMD ["python" "-m", "pytest", "-v", "--cov", "--disable-warnings" ]


FROM base as celery
COPY ./docker-entrypoint-celery.sh /tmp/entrypoint-celery.sh
ENTRYPOINT ["/tmp/entrypoint-celery.sh"]

FROM base as web
COPY ./docker-entrypoint.sh /tmp/entrypoint.sh
ENTRYPOINT ["/tmp/entrypoint.sh"]

FROM base as static_resource_builder
RUN python manage.py collectstatic --clear --noinput \
    && python manage.py collectstatic --noinput

FROM nginx:1.23.3 as nginx
COPY --from=static_resource_builder /srv/code/dev/public /etc/nginx/html/
COPY --from=static_resource_builder /srv/code/dev/public /usr/share/nginx/html/
