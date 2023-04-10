This document has info regarding SSH Module.

### What it does and definetions
- It gives SSH access for the machines mentioned in the `inventory.csv` file.
- Access Types
  -  Sudo: Creates a user with identity enigma username in the requested machine with sudo access, and gives SSH access for that requester.
  - Non Sudo: Creates user with identity enigma username in the requested machine without sudo access, and gives SSH access for the requester.
  - App: Gives SSH access for the app user in the requested Machine. (Module Assumes to have a user App which is commonly used by all users).
  - Other: The requester can specify other user for which they want SSH access. (Module assumes that this user exists).
- Inventory File: Comma separated value(CSV) file with headers hostname and ip.


### Config Parameters:
Parameter | Type | Required | Description
--- | ---| --- | ---
`engima_root_user` | STRING | True | Root user that enigma can use the create users and add users to Sudo group.<br> Note: Make sure this User is available in all the machines that is mentioned in `inventory.csv` file and other IPs that a user can request access for.
`app_user` | STRING | True | Username of the user which is considered to be APP user.
`inventory_file_path` | STRING | True | Relative Path w.r.t the enigma central repo or the Absolute path to the Inventory file Path.
`common_sudo_group` | STRING | True | Sudo Group name. All the users with sudo access are added in this group
`private_key_path` | STRING | True | The Private SSH key that can be used to SSH into the `enigma_root_user` for performing the operations.

