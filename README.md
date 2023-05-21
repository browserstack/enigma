## Enigma Access Management

![BrowserStack Logo](https://d98b8t1nnulk5.cloudfront.net/production/images/layout/logo-header.png?1469004780)



[![Unit Tests and Lint](https://github.com/browserstack/enigma/actions/workflows/unit-tests.yml/badge.svg)](https://github.com/browserstack/enigma/actions/workflows/unit-tests.yml)
[![Security Scan](https://github.com/browserstack/enigma/actions/workflows/semgrep.yml/badge.svg)](https://github.com/browserstack/enigma/actions/workflows/semgrep.yml)



This tool consists of 2 different components: a central webserver and pluggable access modules.

This repo is the code-base for the central webserver.
Refer to [this](https://github.com/browserstack/enigma-access-modules) for published access modules with this tool.

Refer to [this doc](/docs/%E2%80%9CHow-to%E2%80%9D%20guides/Adding%20Modules.md) on how to create custom access modules

## Usage

The following steps are for hosting Enigma locally from published docker container images.

For development setup, follow this [doc](/docs/one-click-dev.md)

### Pre-requisistes

You will need to have docker daemon running locally to run the published containers.
If you don't have docker setup, follow the guidelines [here](https://docs.docker.com/get-docker/)

### Steps

1. Ensure you have a valid `config.json` present locally.

The default [config.json.sample](https://github.com/browserstack/enigma/blob/main/config.json.sample) should be sufficient to start.

You can then add module-specific configuration for the modules you want integrated with Enigma.
For detailed instructions on configuration, follow [this doc](/docs/Configuration%20Guide.md)

2. Run the enigma docker container by mounting the downloaded config to the container

```bash
docker run --rm --name enigma -p 8000:8000 -v "$(pwd)/config.json":/srv/code/dev/config.json browserstack/enigma:v1
```

Ensure that you 8000 port is free to use, and ensure that path to config.json is correct.

That's it! Enigma should be running locally on port 8000


For first time user sign-in, follow [this doc](/docs/%E2%80%9CHow-to%E2%80%9D%20guides/User%20Guides/First%20User%20Setup.md)


## Contributing code

- Python 3.11.0
- pre-commit (see rules [below](#rules-enforced-by-the-pre-commit-hooks))
  - run: `npm install @commitlint/cli @commitlint/config-conventional`
  - run: `pip install pre-commit==2.21.0`
  - run: `pre-commit install --install-hooks --overwrite` in the base directory of this project
  - run: `pre-commit autoupdate`
  - run: `pre-commit run --all-files --show-diff-on-failure --color always`

### Commit Message Guideline

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
- `build`: changes that affect the build system or external dependencies
- `ci`: changes to our CI configuration files and scripts
- `perf`: a code change that improves performance
- `revert`: revert to a commit

### Example

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
