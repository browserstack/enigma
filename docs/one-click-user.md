# Setup for User

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

1. create config.json
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


### Add the config of broker and database in `config.json`
-  For self-hosted celery
    ```bash
      "config": {
            "broker": "redis://host.docker.internal:6379/0",
            "backend": "redis://host.docker.internal:6379/0",
            "need_monitoring": true,
            "monitoring_apps": "django_celery_results"
        }
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

2. clone the images 


```
1.enigma-public-central-web
2.redis
3.mysql/mysql-server 
```
then run following commands
```cmd
#run the web container
docker run -p 8000:8000 -v $(pwd)/config.json:/srv/code/dev/config.json enigma-public-central-web
 
#run redis container
docker run redis:alpine

#run celery container
docker run -v $(pwd)/config.json:/srv/code/dev/config.json --entrypoint /bin/bash enigma-public-central-web -c 'python3 -m celery -A BrowserStackAutomation worker -n worker1 -l DEBUG’
```

3. Start the service
```bash
make dev
```
4. Check logs with
```bash
make logs
```
