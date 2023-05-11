# How to add users on Enigma

## Manual Creation

To manually create a user, login as superuser into the admin portal:

- Add user in "Authentication and Authorization administration" section.

Set email to user email id and password to anything you want. Save user details.

- Add new user in "Access" and save.

- The user can now log on to Enigma using the credentials.

## Allow all users to sign-in with Google SSO

### Obtain google OAuth key and secret

Follow the steps [here](https://developers.google.com/identity/protocols/oauth2/web-server#creatingcred) to generate `client_secret.json` file.


The content of the file will have `client_id` key in `web` section. This is `SOCIAL_AUTH_GOOGLE_OAUTH2_KEY` in the below config.


The value for `client_secret` in `web` section is for `SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET`.

### Add the config of googleapi in `config.json`

```bash
....
"sso": {
    "googleapi": {
        "SOCIAL_AUTH_GOOGLE_OAUTH2_KEY": "<your_google_auth_key>",
        "SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET": "<your_google_auth_secret>"
    }
}
....
```

Sign in to enigma using your Google Mail to create a user on Enigma.
