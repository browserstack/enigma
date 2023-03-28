This document describes how to add modules on Enigma.

Enigma’s access management is built on modules, which refer to the resources/applications the user requires.
Each module needs to be added and integrated with Enigma's central code in order to provide access for the user.

Enigma provides the following modules as part of its default settings, these can be configured from `config.json`:
1. AWS
2. Confluence
3. GCP
4. Github
5. OpsGenie
6. Slack
7. Zoom

When a new resource is required, it's corresponding module has to be added in [Engima's modules repository](https://github.com/browserstack/enigma-public-access-modules.git) or it's own (as per the usecase):
- When adding a new access module, it is required to setup the module's identity (If it does not use user's email ID):
    Add functions `get_identity_template` and `verify_identity` to <your_module>/access.py and corresponsing access template as `identity_form.html` in <your_module>/templates/
- Add `validate_request` to verify access_labels in request.
- Inherit `baseemailaccess` class for helper functions.
- If request has extra fields, define `get_extra_fields` to add these to access_labels. In `access_request_form.html` template, these fields need to be defined with `name=extraFields[]` or `name=extraFields` depending on data.
- Add `approve` and `revoke` functionality.
- Add module name as return for `access_desc` and `tag` functions.
    ```bash
    Note: The tag name should be unique for the module
    ```

Once the implementation is in place, the module needs to be integrated with the central code.
Refer to [Integrations doc](/docs/%E2%80%9CHow-to%E2%80%9D%20guides/Integrating%20Modules.md) for further steps.
