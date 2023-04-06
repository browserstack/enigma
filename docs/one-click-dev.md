# Setup for Local Development

## Pre-requisistes

### Install Docker

- For macOS(brew)
    ```
    brew install docker docker-compose
    ```
-  For windows/linux/macOS refer to
  https://docs.docker.com/get-docker/

### Install Docker Container Runtime
https://github.com/abiosoft/colima
```bash
brew install colima
colima start
```

## Setup

## Clone Repository
Clone the repo in local system
```bash
git clone https://github.com/browserstack/enigma-public-central.git
```
- copy config.json.sample to config.json
```bash
{
  "googleapi": {
    "SOCIAL_AUTH_GOOGLE_OAUTH2_KEY": "",
    "SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET": "",
  },
  "database": {
    "engine": "sqlite3"
  },
  "access_modules": {
    "git_urls": [
      "https://github.com/browserstack/enigma-public-access-modules.git"
    ]
  },
  "enigmaGroup": {
    "MAIL_APPROVER_GROUPS": [
      "devnull@browserstack.com"
    ]
  },
  "emails": {
    "access-approve": "<access-approve-email>"
  },
  "background_task_manager": {
    "type": "celery",
    "config": {
      "broker": "<celery-broker-url>",
      "backend": "<celery-result-backend-url>",
      "need_monitoring": true,
      "monitoring_apps": "django_celery_results"
    }
  }
}
```
#### For private repo in git_urls in `config.json`
```bash
 "https://<git-username>:<github-token>@github.com/browserstack/enigma-public-access-modules.git"
```
where `github-token` is a pat token from https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/creating-a-personal-access-token


### Add the config of broker and database in `config.json`
-  For self-hosted celery
    ```bash
    celery-broker-url="redis://localhost:6379/0"
    celery-result-backend-url="redis://localhost:6379/0"
    ```
-  For self-hosted databases
      ```bash
    celery-broker-url="redis://localhost:6379/0"
    celery-result-backend-url="db+mysql://root@localhost:3306/<name_of_db>"
      ```
### Add the config of access_modules in `config.json`

```bash
   "access_modules": {
    ....

        "aws_access": {
            "aws_accounts": [
                {
                    "account": "<your-account>",
                    "access_key_id": "<access_key_id>",
                    "secret_access_key": "<secret_access_key>"
                }
            ]
        },
        ....
    },
```
Add configuration for all access_module as here added for aws_access.

3. Start the service
```bash
make dev
```
4. Check logs with
```bash
make logs
```
5. Create superuser (Admin) with:
```bash
# Access the container with:
docker exec  -it  dev  bash
#In the container:
python manage.py  createsuperuser
# Set email to admin email id and password to anything you want
```
6. Enigma should be up and running on port 8000!
- Login at localhost:8000/admin
- Login here with your superuser credentials

## How to run tests

1. Tests:
If Web service is not running, the command will first load up the service and then run the tests.
```bash
make test
```

2. Linter:
Docker should be running for linter tool:
```bash
   docker exec dev make lint
```

For a deeper understanding on how to create and integrate new modules, user creation and permissions. Refer ["How-to" guides](/docs/%E2%80%9CHow-to%E2%80%9D%20guides/)

## Nginx Setup (Optional)

Following are the steps to Setup Nginx in enigma

1. **Pre-requisistes** 
    - Should have a host(domain) with ssl certificats that can be attached to nginx.
    - Make sure the host points the public IP of the machine in which enigma is running on. (i.e., create an dns A record with host pointing to public IP of machine)
2. Copy the following code block under the services of docker-compose.yml
    ```
      nginx:
        container_name: enigma_nginx
        image: nginx:latest
        ports:
          - "80:80"
          - "443:443"
        volumes:
          - ./nginx.conf:/etc/nginx/nginx.conf:ro
          - ./certs:/certs
        environment:
          - SSL_KEY_FILE_NAME=<ssl_key_file_name>
          - SSL_CRT_FILE_NAME=<ssl_crt_file_name>
          - HOSTNAME=<hostname>
        depends_on:
          - web
    ```
    This will create `enigma_nginx` container.
3. Update `make dev` command to create nginx when executed.
    ```diff
    .PHONY: dev
    dev: export APPUID = $(APP_UID)
    dev: setup_mounts
    -  @docker-compose build && docker-compose up -d web celery
    +  @docker-compose build && docker-compose up -d web celery nginx
    ```
4. Create `nginx.conf` file in the root folder of enigma-public-central repo.
    **TODO**
5. Create a folder in the root folder of enigma-public-central named `certs` which contains ssl certificate and key.
6. Update the key file and certificate file name respectively in `docker-compose.yml` accordingly.

:tada: Congrats you are done. You can now run `make dev` and you should be able to access enigma from your host.
