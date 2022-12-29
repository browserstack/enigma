# enigma-public-central
Central Codebase for access management tool

<<<<<<< HEAD
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

## Commit Message Guideline

Format: `<type>(<scope>): <subject>`

`<scope>` is optional

`Type` can be of following type:

- `feat`: new feature for the user, not a new feature for build script
- `fix`: bug fix for the user, not a fix to a build script
- `docs`: changes to the documentation
- `style`: formatting, missing semi colons, etc; no production code change
- `refactor`: refactoring production code, eg. renaming a variable
- `test`: adding missing tests, refactoring tests; no production code change
- `chore`: updating grunt tasks etc; no production code change
- `bump`: increase the version of something e.g. dependency

## Example

```
feat: add hat wobble
^--^  ^------------^
|     |
|     +-> Summary in present tense.
|
+-------> Type: Feature addition

fix: fixes #xxx
^--^  ^------------^
|     |
|     +-> Reference to the github issue.
|
+-------> Type: Bug fix
```

References:
- https://www.conventionalcommits.org/en/v1.0.0/
- https://gist.github.com/joshbuchea/6f47e86d2510bce28f8e7f42ae84c716#file-semantic-commit-messages-md
- https://www.conventionalcommits.org/
- https://seesparkbox.com/foundry/semantic_commit_messages
- http://karma-runner.github.io/1.0/dev/git-commit-msg.html

##  License
See [LICENSE.md](.github/LICENSE.md)
