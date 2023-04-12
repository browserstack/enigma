# ACCESS MODULES INTEGRATION

For every new access modules repository, the following settings have to be added:
- add git_urls in `config.json`
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
where github-token is a [PAT Token](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/creating-a-personal-access-token)


The added URLs will be integrated by the cloning script `scripts/clone_access_modules.py`. Once the data is available in the central code, requirements need to be installed as defined by the modules:
```bash
  pip install -r Acess/access_modules/requirements.txt --no-cache-dir --ignore-installed
```

- configure access_modules in `config.json`
```bash
   "access_modules": {
    ....
        "<module_tag>": {
            "properties_key": "properties_value",
        },
        ....
    }
```


#### Configuring secondary approver for access modules

- Any access requested by the user has to go though the approver which will then be granted accordingly. Engima allows to configure approvers for access modules to be at most 2 approvers for a request. 
- By default access modules are configured to have single approver for request to proceed. The user with the permission `ACCESS_APPROVE` is allowed to approve or decline the request in that case. 
- You can configure an access module to have a secondary approver if necessary. This can be done by overriding a function in module class which inherits from BaseEmailAccess class in `access.py` of the access module.
- Overide `fetch_approver_permissions` function which return 
  ```
  {"1": PERMISSION_CONSTANTS["DEFAULT_APPROVER_PERMISSION"]}
  ```
  by default. Which says primary approver should have permission `PERMISSION_CONSTANTS["DEFAULT_APPROVER_PERMISSION"]` which is equal `ACCESS_APPROVE`. You can override this by specifing the permission that secondary approver should have. For example lets say permission required for secondary approver is `SECONDARY_ACCESS_APPROVE` then your updated funtion looks like follows:
  ```python
  def fetch_approver_permissions(self, access_label=None):
    return {"1": PERMISSION_CONSTANTS["DEFAULT_APPROVER_PERMISSION"], "2": "SECONDARY_ACCESS_APPROVE"}
  ```
- Once the function is overridden admin can now create a permission with the label and then assign user that permission (learn more about adding permission is Adding Permissions Section). And the user will be asked for the secondary approver for a request.

#### Disabling Access module
- For one click setup it clone all the access modules from the `enigma-public-access-modules` repo. So in the UI you can see all the access modules.
- Which can be disabled by removing the non required access moduled folder from `Access/access_modules` path.
