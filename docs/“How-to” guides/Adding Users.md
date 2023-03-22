This document describes how to add users on Enigma.

## Create users on Enigma:
- To manually create a user, login as superuser into the admin portal:
    (i) Add user in "Authentication and Authorization administration".
        ``` Set email to user email id and password to anything you want. Save user details. ```
    (ii) Add new user in "Access" and save.
    (iii) The user can now log on to Enigma using the credentials set in (i)
- Google SSO:
    ### Add the config of googleapi in `config.json`
    ```bash
    "googleapi": {
        "SOCIAL_AUTH_GOOGLE_OAUTH2_KEY": "<your_google_auth_key>",
        "SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET": "<your_google_auth_secret>"
    }
    ```
Sign in to enigma using your Google Mail to create a user on Enigma.
