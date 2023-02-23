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

### Setup
Clone the repo in local system
```bash
git clone https://github.com/browserstack/enigma-public-central.git
```
1. Create .env file from .env.sample file. Edit the DOCKERIMAGE to the latest image URL.
2. copy config.json.sample to config.json
```bash
{
  "googleapi": {
    "SOCIAL_AUTH_GOOGLE_OAUTH2_KEY": "",
    "SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET": "",
    "SOCIAL_AUTH_GOOGLE_OAUTH2_WHITELISTED_DOMAINS": ""
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
### for private repo in git_urls in `config.json`
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
### Add the config of custom access-module repos `config.json`

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
        .....
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
