Feature: Validate Approver Permission
   
    Scenario: User who made the request has primary approver access & access_mapping is not in pending state & module does not need secondary approval
        Given User who made request has primary approver access
        And access_mapping is not in pending state
        And Modules does not need secondary approval
        When validate_approver_permissions function is called 
        Then Return value should be empty json

    Scenario: _get_approver_permissions raises an Exception, the function should return error message as json  
        Given _get_approver_permissions raises an exception when called
        When validate_approver_permissions function is called
        Then Return value should be error json

    Scenario: User who made the request does not have any approver access & access_mapping is not in pending state & module does not need secondary approval
        Given User who made request not have any approver access
        And access_mapping is in pending state
        And Modules does not need secondary approval
        When validate_approver_permissions function is called
        Then Return value should be permission denied json
    
    Scenario: User who made the request has secondary approver access & access_mapping is not in pending state & module supports secondary approval
        Given User who made request has secondary approver access
        And access_mapping is not in pending state
        And Modules supports secondary approval
        When validate_approver_permissions function is called
        Then Return value should be empty json

    Scenario: User who made the request has primary approver access & access_mapping is not in pending state & module supports secondary approval 
        Given User who made request has primary approver access
        And access_mapping is not in pending state
        And Modules supports secondary approval
        When validate_approver_permissions function is called
        Then Return value should be permission denied json


    Scenario: When the user who made the request has primary approver access & access_mapping is in pending state & module does not need secondary approval 
        Given User who made request has primary approver access
        And access_mapping is in pending state
        And Modules does not need secondary approval
        When validate_approver_permissions function is called
        Then Return value should be empty json

    Scenario: When the user who made the request has primary approver access & access_mapping is in pending state & module does needs secondary approval 
        Given User who made request has primary approver access
        And access_mapping is in pending state
        And Modules supports secondary approval
        When validate_approver_permissions function is called 
        Then Return value should be empty json

    Scenario: When the user who made the request has secondary approver access & access_mapping is in primary pending state & module does needs secondary approval 
        Given User who made request has secondary approver access
        And access_mapping is in pending state
        And Modules does not need secondary approval
        When validate_approver_permissions function is called 
        Then Return value should be permission denied json

  