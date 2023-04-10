This document has info regarding confluence Module.

### What it does
- Module is responsible for giving Admin, edit or read access to a particular confluence space.


### Config Parameters:
Parameter | Type | Required | Description
--- | ---| --- | ---
`CONFLUENCE_BASE_URL` | STRING | True | The base URL of the atlassian Account. <br> For example `https://test.atlassian.net` <br> Note: Should have the same format, should have `https://` and should not end with `/`
`ADMIN_EMAIL` | STRING | True | Email of the user who have admin permission for the Atlassian account
`API_TOKEN` | STRING | True | API token which is created by account with email `ADMIN_EMAIL`. Learn more about creating [api token in here.](https://support.atlassian.com/atlassian-account/docs/manage-api-tokens-for-your-atlassian-account/)
