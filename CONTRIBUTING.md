Read our [Code of Conduct](CODE_OF_CONDUCT.md) to keep our community approachable and respectable.

This guide will give you an overview of the contribution workflow from opening an issue, creating a PR, reviewing, and merging the PR.

# Local Setup
- Follow https://github.com/browserstack/enigma-public-central#setup for setting up the project locally.

# Issues

## Create a new issue
If you spot an issue with the tool or you want to improve the tool by adding some functionality, search if an issue already exists for the same.

If you're unable to find an open issue addressing the problem, open a new one. Be sure to include a title and clear description, as much relevant information as possible, and a code sample or an executable test case demonstrating the expected behavior that is not occurring.

 ## Solve an issue
Scan through our existing issues to find one that interests you. You can narrow down the search using labels as filters. As a general rule, we don’t assign issues to anyone. If you find a problem to work on, you are welcome to open a PR with a fix.

## Did you write a patch that fixes a bug or adds functionality?
- Commit the changes once you are happy with them. Always write a clear log message for your commits.
  - For commit message we follow [Conventional Commit Message Guideline](https://www.conventionalcommits.org). To enforce this we use [pre-commit](https://pre-commit.com), to setup the same go through [pre-commit setup section of the README](https://github.com/browserstack/enigma-public-central#for-contributing-code)
  - Make sure there are no lint issues, check lint issues by running `make lint`. If there are some in the portion which you have touched, fix those lint issues.
  - If you are making changes to config then please update [schema.json file](schema.json) also.
  - We use [semgrep](https://semgrep.dev) for static code analysis and finding vulnerabilities. To check issues locally run `make run_semgrep`.
- Please test the tool locally so that by doing the above change there is nothing breaking in the project elsewhere.
  - To test project locally you can run `make test`
- Don't forget to self-review to speed up the review process.
- Open a new GitHub pull request with the fix/patch.
- Ensure the PR description clearly describes the problem and solution. Include the relevant issue number if applicable.
- Before submitting, please read the [Contributing to Django project](https://docs.djangoproject.com/en/dev/internals/contributing/writing-code/) guide to know more about coding conventions and unit tests, etc.
- Your PR is merged!
- Congratulations 🎉 The Enigma team thanks you ✨.
- Once your PR is merged, your contributions will be publicly visible on the Project Repo.

## Coding conventions
[Coding style | Django documentation](https://docs.djangoproject.com/en/dev/internals/contributing/writing-code/coding-style/)
