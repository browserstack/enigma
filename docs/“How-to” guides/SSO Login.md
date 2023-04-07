Enigma uses [python-social-auth/social-core](https://github.com/python-social-auth/social-core) to setup social authentication.
Enigma uses Google SSO as default. To integrate another SSO application, refer the following steps:

1. Add chosen SSO backend to `AUTHENTICATION_BACKENDS` in settings.py
    - Github
        ```json
        AUTHENTICATION_BACKENDS = (
            ....
            'social_core.backends.github.GithubOAuth2',
            ....
        )
        ```
    - Microsoft Azure Active Directory
        ```json
        AUTHENTICATION_BACKENDS = (
            ....
            'social_core.backends.azuread_tenant.AzureADOAuth2',
            ....
        )
        ```
2. Edit `config.json` to accept the required keys for authentication.
    Example:
    - Github
        ```json
        "sso": {
            "githubapi": {
                "SOCIAL_AUTH_GITHUB_KEY" = "",
                "SOCIAL_AUTH_GITHUB_SECRET" = "",
                "SOCIAL_AUTH_GITHUB_ORG_NAME" = ""
            },
            ....
        },
        ....
        ```
    - Microsoft Azure Active Directory
        ```json
         "sso": {
            "azureapi": {
                "SOCIAL_AUTH_AZUREAD_OAUTH2_KEY" = "",
                "SOCIAL_AUTH_AZUREAD_OAUTH2_SECRET" = "",
            },
            ....
        },
        ....
        ```
3. Edit [Login.html](/templates/registration/login.html):
    Get the name from file `backend-name`.py

    Refer: [social-core backends](https://github.com/python-social-auth/social-core/blob/master/social_core/backend/)

    Example:
    ```bash
    Google SSO has name = "google-oauth2" defined in class `GoogleOAuth2`

    <a href="{% url "social:begin" "google-oauth2" %}" style="margin-top:2%">
        <button type="button"class="...." style="....">
            Sign In
        </button>
    </a>
    ```

Reference:
- Here’s a [list and detailed instructions](https://python-social-auth.readthedocs.io/en/latest/backends/index.html) on how to set up the support for each backend.
