This document describes how to add modules on Enigma.

- When adding a new access module, it is required to setup the module's identity (If it does not use user's email ID):
    Add functions `get_identity_template` and `verify_identity` to <your_module>/access.py and corresponsing access template as `identity_form.html` in <your_module>/templates/
- Add `validate_request` to verify access_labels in request.
- If request has extra fields, define `get_extra_fields` to add these to access_labels. In `access_request_form.html` template, these fields need to be defined with `name=extraFields[]` or `name=extraFields` depending on data.
- Add `approve` and `revoke` functionality.
- Add module name as return for `access_desc` and `tag` functions.

Once the implementation is in place, the module needs to be integrated with the central code.
Refer to [Integrations doc](/docs/%E2%80%9CHow-to%E2%80%9D%20guides/Integrating%20Modules) for further steps.
