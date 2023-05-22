# Setup Enigma Locally

## Pre-requisites
You should have python3 installed on your system and checked out the enigma repository locally.


## Steps
1. Ensure you have a valid `config.json` present locally.

The default [config.json.sample](https://github.com/browserstack/enigma-public-central/blob/main/config.json.sample) should be sufficient to start.

You can then add module-specific configuration for the modules you want integrated with Enigma.
For detailed instructions on configuration, follow [this doc](/docs/Configuration%20Guide.md)

2. Add folder `db` in root folder of the repository.
3. Add a package `access_modules` inside `Access`.

Copy this [file](../../Access/base_email_access/access_modules_init.py) as `__init__.py` of `access_modules`

4. Add access modules inside `access_modules` to integrate them with Enigma. (Optional and not needed to get started)

Copy each access module folder that you want to support manually here ensuring directory hierarchy in the following manner:
```
- Access
|-- access_modules
|--|-- __init__.py
|--|-- custom_module_1
|--|--|-- __init__.py
|--|--|-- access.py
|--|-- custom_module_2
|--|--|-- __init__.py
|--|--|-- access.py
```
For detailed instructions on how to add modules, follow [this doc](/docs/%E2%80%9CHow-to%E2%80%9D%20guides/Adding%20Modules.md)

5. Install all the requirements through requirements.txt and ensure dependencies for access modules are installed
```
pip3 install -r requirements.txt
```
6. Run Migrate to create all the database tables.
```
python3 manage.py migrate
```
7. Run the server
```
python3 manage.py runserver
```

Ensure that the 8000 port is free to use.

That's it! Enigma should be running locally on port 8000 http://localhost:8000

For first time user sign-in, follow [this doc](/docs/%E2%80%9CHow-to%E2%80%9D%20guides/User%20Guides/First%20User%20Setup.md)
