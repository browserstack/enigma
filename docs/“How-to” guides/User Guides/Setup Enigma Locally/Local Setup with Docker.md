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

### Clone Repository
Clone the repo in local system
```bash
git clone https://github.com/browserstack/enigma.git
```
- copy config.json.sample to config.json

#### For private repo in git_urls in `config.json`
```bash
 "https://<git-username>:<github-token>@github.com/browserstack/enigma-access-modules.git"
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
