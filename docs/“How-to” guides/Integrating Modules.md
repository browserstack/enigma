# ACCESS MODULES INTEGRATION

For every new access modules repository, the following settings have to be added:
- add git_urls in `config.json
```bash
"access_modules": {
    "git_urls": [
      "https://github.com/browserstack/enigma-public-access-modules.git",
      "https://github-new-access-module.git"
    ],
    ....
}
```
### For private repos:
```bash
 "https://<git-username>:<github-token>@github.com/browserstack/enigma-public-access-modules.git"
```
where github-token is a pat token from https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/creating-a-personal-access-token


The added URLs will be integrated by the cloning script `scripts/clone_access_modules.py`. Once the data is available in the central code, thr requirements need to be installed as defined by the modules:
```bash
  pip install -r Acess/access_modules/requirements.txt --no-cache-dir --ignore-installed
```

- configure access_modules from `config.json`
```bash
   "access_modules": {
    ....
        "<module_name>": {
            "properties_key": "properties_value",
        },
        ....
    }
```
