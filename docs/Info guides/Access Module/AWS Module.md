This document has info regarding AWS Module.

### What it does
- Module is responsible for adding a user to a AWS group.
- The username that is added to the AWS group is beginning part of the email till `@`. For example if email is `test@gmail.com` AWS username is test. If its different for your organisation you can change the function `__get_username` inside the `aws_access/helper.py` file

### Config Parameters:
Parameter | Type | Required | Description
--- | ---| --- | ---
`aws_accounts` | Array `AWS_ACCOUNT` | True | Array of `AWS_ACCOUNT` which is a JSON object with keys `account`, `access_key_id`, `secret_access_key`
`account` | STRING | True | Can be any identifier that is used to identity the Account.
`access_key_id` | STRING | True | AWS Access Key for the Account.
`secret_access_key` | STRING | True | AWS Secrete Key for the Account.


Please note that the accounts added should have the permissions to list all the groups and add the members to the group
