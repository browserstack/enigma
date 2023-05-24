# Enigma Access Management

![BrowserStack Logo](https://d98b8t1nnulk5.cloudfront.net/production/images/layout/logo-header.png?1469004780)



[![Unit Tests and Lint](https://github.com/browserstack/enigma/actions/workflows/unit-tests.yml/badge.svg)](https://github.com/browserstack/enigma/actions/workflows/unit-tests.yml)
[![Security Scan](https://github.com/browserstack/enigma/actions/workflows/semgrep.yml/badge.svg)](https://github.com/browserstack/enigma/actions/workflows/semgrep.yml)


Manage access to tools through a single portal.

## What is Enigma?

Enigma is a web-based internal Access Management Tool that:
* helps employees get access to various in-house and third-party systems and components like git repositories, cloud machines (via ssh), and dashboards.
* facilitates book-keeping.
* helps with compliance.
* manages the inventory of all the tools in one place.


This tool consists of 2 different components: a central web server and pluggable access modules.

This repo is the code-base for the central webserver.
Refer to [this](https://github.com/browserstack/enigma-access-modules) for published access modules with this tool.

Refer to [this doc](/docs/%E2%80%9CHow-to%E2%80%9D%20guides/Adding%20Modules.md) on how to create custom access modules

### Problems Solved

Enigma access management tool was developed internally at BrowserStack to solve some of the problems we observed around access management for employees

* No single portal for an individual to view their access across tools
* No single portal to manage access for employees across vendors
* No central audit trail across tools for access granted and revoked for employees
* Repetitive Ops for DevOps teams and tool owners for access grant and revoke requests
* No standardized SOC2-compliant and GDPR-compliant method for managing individual and admin access for external tools
* No simple consolidated pipeline to trigger offboarding an exit-ing employee to revoke all employee access across tools
* No way for an individual to maintain separate identity per tool
  * Individuals might have multiple accounts for a single tool, there can be multiple org-wide domains for certain tools
* No way to request, audit and track employee access outside of org-team hierarchy. Adhoc teams / groups support is needed.
  * employees might migrate across teams, sometimes access are needed for temporary projects which are not required for the whole team
* No way of listing a bunch of access to grant to employees working on a project
  * In case an individual is added to a project, access request for all relavant tools should be raised with a single click (based on knowledge-base build on other individuals working on the project)

## Usage

The following steps are for hosting Enigma locally from published docker container images.

For development setup, follow this [doc](/docs/one-click-dev.md)

#### Pre-requisites

You will need to have docker daemon running locally to run the published containers.
If you don't have docker setup, follow the guidelines [here](https://docs.docker.com/get-docker/)

#### Steps

1. Ensure you have a valid `config.json` present locally.

The default [config.json.sample](https://github.com/browserstack/enigma/blob/main/config.json.sample) should be sufficient to start.

You can then add module-specific configuration for the modules you want to be integrated with Enigma.
For detailed instructions on configuration, follow [this doc](/docs/Configuration%20Guide.md)

2. Run the Enigma docker container by mounting the downloaded config to the container

```bash
docker run --rm --name enigma -p 8000:8000 -v "$(pwd)/config.json":/srv/code/dev/config.json browserstack/enigma:v1
```

Ensure that the 8000 port is free to use, and ensure that path to config.json is correct.

That's it! Enigma should be running locally on port 8000


For first time user sign-in, follow [this doc](/docs/%E2%80%9CHow-to%E2%80%9D%20guides/User%20Guides/First%20User%20Setup.md)


## Contributing to this tool

- The codebase is tested for Python 3.11.0
- Setup pre-commit hooks for development (see rules [below](#rules-enforced-by-the-pre-commit-hooks))
  - run: `npm install @commitlint/cli @commitlint/config-conventional`
  - run: `pip install pre-commit==2.21.0`
  - run: `pre-commit install --install-hooks --overwrite` in the base directory of this project
  - run: `pre-commit autoupdate`
  - run: `pre-commit run --all-files --show-diff-on-failure --color always`

#### Commit Message Guideline

Format: `<type>(<scope>): <subject>`

`<scope>` is optional

`Type` can be of the following type:

- `feat`: new feature for the user, not a new feature for build script
- `fix`: bug fix for the user, not a fix to a build script
- `docs`: changes to the documentation
- `style`: formatting, missing semi-colons, etc; no production code change
- `refactor`: refactoring production code, eg. renaming a variable
- `test`: adding missing tests, refactoring tests; no production code change
- `chore`: updating grunt tasks etc; no production code change
- `bump`: increase the version of something e.g. dependency
- `build`: changes that affect the build system or external dependencies
- `ci`: changes to our CI configuration files and scripts
- `perf`: a code change that improves performance
- `revert`: revert to a commit

#### Example

```
feat: add hat wobble
^--^  ^------------^
|     |
|     +-> Summary in the present tense.
|
+-------> Type: Feature addition

fix: fixes #xxx
^--^  ^------------^
|     |
|     +-> Reference to the GitHub issue.
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
See [LICENSE.md](/LICENSE.md)
