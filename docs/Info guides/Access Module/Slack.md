This document has info regarding Slack Module.

### What it does
- Module is responsible for adding a user to a workspace.

### Config Parameters:
Parameter | Type | Required | Description
--- | ---| --- | ---
`<workspace_name>` | STRING | True | This is a dynamic value which represents the name of the slack workspace can be anything just to identity the workspace.
`AUTH_TOKEN` | STRING | True | Auth token of the perticular workspace.
`DEFAULT_CHANNELS` | Array | True | Default channels that the user should be part of when added to a workspace.
