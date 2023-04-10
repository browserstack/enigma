This document has info regarding GCP Module.

### What it does
- Module is responsible for adding a user into GCP (google) group.


### Config Parameters:
Parameter | Type | Required | Description
--- | ---| --- | ---
`domains` | Array `domain` | True | Array of `domain` which is a JSON object with keys `domain_id`, `admin_id`, `service_account_path`
`domain_id` | STRING | True | Domain of the Google workspace. <br> For example, `browserstack.com`
`admin_id` | STRING | True | Email of the Admin for the Google Workspace.
`service_account_path` | STRING | True | Path to the service account credentials generated.<br> Note: Make sure to allow service account to list groups and members, add/delete the members of the group.<br> Note: Also make sure path to be relative w.r.t the root central enigma repo.



