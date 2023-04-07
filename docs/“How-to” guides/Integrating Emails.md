To configure email functionality in Enigma, refer the following steps:

Enigma uses SMTP as the default email backend. Email will be sent through a SMTP server.

In `config.json`, set the details for the mentioned keys:
```json
    ....
    "emails": {
        "access-approve": "",
        "EMAIL_HOST": "",
        "EMAIL_PORT": "",
        "EMAIL_HOST_USER": "",
        "EMAIL_HOST_PASSWORD": "",
        "EMAIL_USE_TLS": true,
        "EMAIL_USE_SSL": false,
        "DEFAULT_FROM_EMAIL": ""
    }
    ....
```

Once successfuly configured, Enigma will be able to send email messages to users regarding their access request status.

For example, Enigma can send email messages to users when modules are assigned to them for approval, or when any updates are available on a modules approval status.
