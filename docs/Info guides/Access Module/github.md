This document has info regarding Github Module.

### What it does
- Module is responsible for giving access to github repos.
- Access level:
  - Pull
  - Push
  - Admin
  - Push+merge



### Config Parameters:
Parameter | Type | Required | Description
--- | ---| --- | ---
`GITHUB_TOKEN` | STRING | True | Secret token which is a GitHub App installation access token. Learn more about the token [here](https://docs.github.com/en/actions/security-guides/automatic-token-authentication)
`GITHUB_BASE_URL` | STRING | True | The base URL of the github Account. <br> For example `https://api.github.com`
`GITHUB_ORG` | STRING | True | The organization name which is connected to the Github account.
