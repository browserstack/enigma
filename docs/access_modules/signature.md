# Access Modules can override the following properties / functions

## Property `available`
*Required*

#### Data Type
`bool`

#### Possible Values
`True`, `False`

#### Description
Boolean value `False` indicates that this module is disabled from the module code itself. This module won't show up in the list of modules to raise accesses for, and will be hidden from entire request flow.

## Property `group_access_allowed`
*Required*

#### Data Type
`bool`

#### Possible Values
`True`, `False`

#### Description
Boolean value `False` indicates that group request cannot be raised for this access module, only individual access requests are supported.

## Class method `grant_owner`
*Required*

#### Arguments
*None*

#### Return Value
An array of valid email ids.

#### Description
This is a list of email ids within the org, who are the owners for granting accesses for this module.
These will be tagged as module owners for granting accesses in audit reports and on dashboards.

## Class method `revoke_owner`
*Required*

#### Arguments
*None*

#### Return Value
An array of valid email ids.

#### Description
This is a list of email ids within the org, who are the owners for revoking accesses for this module.
These will be tagged as module owners for revoking accesses in audit reports and on dashboards.

If a special value `automated-grant` is present in this list, `revoke` function of the module will be called on these events:
- `Offboard User`: When `Start Offboarding` button is pressed for the user from users list
- `Remove User from group`: When `Remove User` button is pressed for the user from the group's access list

## Class method `access_mark_revoke_permission`
*Required*

#### Arguments
- `access_type`: The module's access type that is being revoked

#### Return Value
Valid email id as string

#### Description
This email id is notified in case of an exception in the grant flow for an access of this module.

## Class method `fetch_approver_permissions`
*Optional*

#### Default Value
```
{
  "1": "ACCESS_APPROVE"
}
```

#### Arguments
- `access_label`: The `access_label` mapping that uniquely identifies the access for this module

#### Return Value
A mapping with key-value pair as defined below

Key '1', Value: The permission label that the user should have to be the first approver for that particular access
(Optional) Key '2', Value: The permission label that the user should have to be the secondary approver for that particular access

#### Description
Access approve flow uses the corresponding permission label to allow users to press the `Approve` button from pending requests page.
Secondary approval flow is triggered based on whether key '2' is present in the response.

## Class method `get_label_desc`
*Required*

#### Arguments
- `access_label`: The `access_label` mapping that uniquely identifies the access for this module

#### Return Value
String describing the specific access for the module.

#### Description
This should return a string describing the access that the input label is referring to.
This is used on the UI to better describe the access.

eg return string: `Access to push commits to github repo github.com/rails/rails`

## Class method `combine_labels_desc`
*Required*

#### Arguments
- `access_labels`: A list of `access_label` mapping belonging to this module

#### Return Value
String describing all accesses in the list for this module.

#### Description
This should return a string describing all accesses that the input labels are referring to.
This is used on the UI to better describe a group of accesses.

eg return string: `Access to push commits to github repo github.com/rails/rails, github.com/expressjs/express and to merge pull requests for github repo github.com/nightwatchjs/nightwatch`

## Class method `get_label_meta`
*Required*

#### Arguments
- `access_label`: The `access_label` mapping that uniquely identifies the access for this module

#### Return Value
A mapping with key-value pair to add to the description of the access on UI

#### Description
If some additional details need to be addded to the description returned by `get_label_desc` method, those can be added as key-value pairs in the response from this function.

eg.
To describe slack access to workspace `ExampleWorkspace`,
return value of `Slack access to workspace ExampleWorkspace` for method `get_label_desc` AND
return value of `{"channels": "general,random"}` for method `get_label_meta`
will describe the access on the UI as `Slack access to workspace ExampleWorkspace details: {"channels": "general,random"}`

This makes it easier to read on the UI, grouping / sorting by accesses based on description and not by meta

## Class method `combine_labels_meta`
*Required*

#### Arguments

#### Return Value

#### Description

## Class method `access_request_data`
*Required*

#### Arguments

#### Return Value

#### Description

## Class method `approve`
*Required*

#### Arguments

#### Return Value

#### Description

## Class method `revoke`
*Required*

#### Arguments

#### Return Value

#### Description

## Class method `get_extra_fields`
*Required*

#### Arguments

#### Return Value

#### Description

## Class method `validate_request`
*Required*

#### Arguments

#### Return Value

#### Description

## Class method `fetch_access_approve_email`
*Required*

#### Arguments

#### Return Value

#### Description

## Class method `fetch_access_request_form_path`
*Required*

#### Arguments

#### Return Value

#### Description
