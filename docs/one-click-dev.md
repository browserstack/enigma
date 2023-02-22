# one-click-dev-setup


### Pre-requisistes

- Install Docker
```
brew install docker docker-compose
```

- Install Docker Container Runtime
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
```pan
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
      "https://<user>:<github-token>@github.com/browserstack/enigma-public-access-modules.git"
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

replace this values in config.json
celery-broker-url= "redis://localhost:6379"
celery-result-backend-url = "redis://localhost:6379"

```
3. Start the service
```bash
make dev
```
4. Check logs with
```bash
make logs
```


