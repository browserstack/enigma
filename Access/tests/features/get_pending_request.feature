Feature : Get Pending Request

  Scenario: Retrieving All Pending Requests
        Given request to view all pending requests
        When the `get_pending_requests` method is called
        Then the method should retrieve all pending membership and group creation requests
        And all pending access requests from modules
        And return the retrieved requests in the context variable

  Scenario: Error Handling
        Given request to view pending requests
        And an error occurs while retrieving the requests
        When the `get_pending_requests` method is called
        Then the method should handle the error
        And return an error response
