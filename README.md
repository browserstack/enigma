# enigma-public-central
Central Codebase for access management tool

## Local setup

After cloning this repository, make sure that the dependencies are installed on your local machine by running:
`pip install -r requirments.txt`

### For contributing code

- Python 3.11.0
- pre-commit (see rules [below](#rules-enforced-by-the-pre-commit-hooks))
  - run: `brew install pre-commit` or `pip install pre-commit`
  - run: `pre-commit install --install-hooks --overwrite` in the base directory of this project

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
=======
##  License
See [LICENSE.md](.github/LICENSE.md)
