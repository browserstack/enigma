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
- Add __init__.py:

    ```bash
        from . import access  # noqa
    ```
- Add access.py (Following implementations to be added in this file)
- Implement functions which are specified in BaseEmailAccess Module (overridde based on use case):

    `from Access.base_email_access.access import BaseEmailAccess` class for helper functions.
- Create template for access request as `<module_name>/templates/<module_name>/access_request_form.html` and return this path in function `fetch_access_request_form_path`.
- When adding a new access module, it is required to verify the module's identity (If it does not use user's email ID):
    Add functions `get_identity_template` and `verify_identity` and corresponsing identity template as `<module_name>/templates/<module_name>/identity_form.html`
- Add `validate_request` function to verify `access_labels` in request. The validation is required to address and rule out all vulnerabilities (frontend issues / form issues / value injection / hacks ).
    ```
    Note: `access_label` signifies the access related data requested by the user. The json constitutes of the fields defined by the access request form template.
    ```
- Add module name as return for `access_desc` and `tag` functions.
    ```
    Note: The tag uniquely identifies access
    This tag is used as configuration key to set properties required by the module in file `config.json` in the central repository.
    ```
- Implement `approve` and `revoke` functions to implement respective functionalities.

Refer to [Engima Access Modules](https://github.com/browserstack/enigma-public-access-modules.git) for further understanding of the default implementations and file structure.

Once the implementation is in place, the module needs to be integrated with the central code.
Refer to [Integrations doc](/docs/%E2%80%9CHow-to%E2%80%9D%20guides/Integrating%20Modules.md) for further steps.
