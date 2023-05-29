This document describes how to add user identity on Enigma.

To manage access Enigma needs to store every User’s Identity for each module. If a module, uses identity other than email then the identity has to be defined so access can be provided.
For this, every module which requires such an identity has to define the template and JSON in the module implementation.

- Navigate to 'Profile' on the Enigma dashboard and fill in the details and 'Update'. An error/success messgae will be displayed depending on the request status.

Note: If a situation arises, where the User updates their identity for a module, then any and all accesses they have to this module will be revoked from old identity and new accesses will be raised for the updated details.
