""" Test for individual pending requests"""

Scenario: No pending requests
          Given individual_pending_requests is empty
          When process_individual_requests is called
          Then individual_requests should remain unchanged

Scenario: Single pending request for a club
          Given individual_pending_requests contains a single pending request for a club
          And club id is "123"
          And access_tag is "access-tag-1"
          When process_individual_requests is called
          Then individual_requests should contain a single entry with module_tag "access-tag-1"
          And the entry should have club_id "123"
          And the entry should have userEmail, accessReason, accessType, requested_on, sla_breached, accessData

Scenario: Multiple pending requests for a club
          Given individual_pending_requests contains multiple pending requests for a club
          And club id is "123"
          And access_tag is "access-tag-1"
          When process_individual_requests is called
          Then individual_requests should contain a single entry with module_tag "access-tag-1"
          And the entry should have club_id "123"
          And the accessData should contain all the pending requests for the club

Scenario: Multiple pending requests for multiple clubs
          Given individual_pending_requests contains multiple pending requests for multiple clubs
          And access_tag is "access-tag-1"
          When process_individual_requests is called
          Then individual_requests should contain one entry for each club with module_tag "access-tag-1"
          And each entry should have club_id, userEmail, accessReason, accessType, requested_on, sla_breached, accessData
          And the accessData for each entry should contain all the pending requests for the corresponding club.
