# ACCESS MODULES INTEGRATION

For every new access modules repository, the following settings have to be added:
### add git_urls in `config.json
```bash
"access_modules": {
    "git_urls": [
      "https://github.com/browserstack/enigma-public-access-modules.git",
      "https://github-new-access-module.git"
    ]
},
```
For private repos:
    "https://<git-username>:<github-token>@github.com/browserstack/enigma-public-access-modules.git"
where github-token is a pat token from https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/creating-a-personal-access-token


The added URLs will be integrated from the cloning script `scripts/clone_access_modules.py`
