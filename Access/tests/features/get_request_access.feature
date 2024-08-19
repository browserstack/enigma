Feature: Get Request Access

    Scenario: verify generic form key
        Given empty configured access_modules are There
        And get_request has zero modules
        When get_request_access function is called
        Then Return value should be empty access list

    Scenario: get_access_request returns correct response
        Given four configured access_modules are There
        And get_request has four modules
        When get_request_access function is called
        Then Return value should return all four access list with all seven present keynames

    Scenario: get_access_request returns correct response with extra fields
        Given four configured access_modules are There
        And two with extra fields and two without extra fields
        When get_request_access function is called
        Then Return value should return all four access with extra fields

     Scenario: get_access_request returns correct response with notice/alert
        Given four configured access_modules are There
        And two with extra notice/alert and two without notice/alert
        When get_request_access function is called
        Then Return value should return all four access with notice/alert

    Scenario: verify response with array of access list with two elements
        Given four configured access_modules are There
        And get_request has two modules
        When get_request_access function is called
        Then Return value should be access list with two modules

    Scenario: verify response with array of access list with empty elements
        Given four configured access_modules are There
        And get_request has zero modules
        When get_request_access function is called
        Then Return value should be empty access list

    Scenario: verify response with array of access list with all elements
        Given four configured access_modules are There
        And get_request has four modules
        When get_request_access function is called
        Then Return value should return all four access list with all seven present keynames

     Scenario: get_request_access is called with invalid parameters
        Given four configured access_modules are There
        And get_request does not have accesses key
        When get_request_access function is called
        Then Return value should be error json

    Scenario: get_request_access is called with invalid request type
        Given request is post request
        When get_request_access function is called for invalid request type
        Then Return value should be error json
