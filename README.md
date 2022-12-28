# enigma-public-central
Central Codebase for access management tool

### Pre-requisistes

- Install Docker
```bash
brew install docker docker-compose
```

- Install Docker Container Runtime
https://github.com/abiosoft/colima
```bash
brew install colima
colima start
```

### Setup

1. Start the service
```bash
make dev
```
2. Check logs with 
```bash
make logs
```
3. After seeing migration output in the logs (or waiting a minute after the containers come up), 
 create superuser with
```bash
# Access the container with:
docker exec -it dev bash
#In the container:
python manage.py createsuperuser
# Set email to your email id, and password to anything you want
```
4. Access the db container with below commands. Password for db container is testtest
```bash
docker exec -it db bash
mysql -u root -p
create database enigma;
```
4. Restart the server by runing below commands
```bash
docker-compose -f docker-compose.yml restart
```
Enigma should be up and running on port 8000!
  - Login at localhost:8000/admin
  - Login here with your superuser credentials, and click the View Site button on the top right after logging in.

### How to run tests

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
