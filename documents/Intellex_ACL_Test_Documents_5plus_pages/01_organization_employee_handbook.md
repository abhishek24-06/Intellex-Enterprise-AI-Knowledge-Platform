# Organization Employee Handbook

**Visibility:** ORGANIZATION

**ACL Test Marker:** `ORG-DOC-01-ALPHA`


## 1. Introduction

This handbook establishes common operating practices for employees working inside the Apple organization represented by organization_id 2 in the Intellex test environment. It explains how employees should approach collaboration, documentation, security, access management, operational changes, and internal knowledge sharing. The document is intentionally organization-wide so it can be used to validate that a user who belongs to the organization can retrieve a broad class of content while still being unable to retrieve department, team, or user-restricted material.


## 2. Working Practices

Employees should keep work records clear, factual, and sufficiently detailed for another employee to understand the decision that was made and why it was made. Project notes should identify the owner, relevant date, current status, dependencies, and next action. When information crosses department boundaries, the shared record should avoid embedding restricted information that is not necessary for the broader audience.


### Reference Table

| Field | Example | Purpose |
|---|---|---|
| Owner | Assigned employee | Accountability |
| Status | In progress | Current state |
| Priority | High | Ordering work |
| Review | Required | Quality control |


## 3. Information Handling

Company information should be handled according to its intended visibility. Organization-visible material can support common operations, while restricted material requires the applicable department, team, or user authorization. A search system must not treat the ability to formulate a query as evidence that the user is entitled to receive the matching content.


```python
record = {
    "owner": "assigned-user",
    "status": "in_progress",
    "priority": "high",
    "validated": True,
}
```


## 4. Authentication and Identity

Employees use authenticated accounts to access internal services. Credentials must remain private and should never be placed in ordinary project documents. Identity information is also relevant to authorization because the same user may belong to a department and a team while still being excluded from a document that is explicitly assigned to another user.


## 5. Collaboration

Cross-functional collaboration is encouraged when it improves delivery, but collaboration does not override access control. A Finance employee collaborating with an Engineering employee does not automatically gain access to Engineering-restricted documents. Similarly, membership in a team should not imply access to every document owned by another team.


## 6. Documentation Standards

Technical documents should use descriptive headings, meaningful filenames, clear tables where appropriate, and examples that can be understood without relying on hidden context. Operational records should identify assumptions and distinguish confirmed facts from proposed actions.


## 7. Incident Reporting

Employees should report operational and security incidents through the approved internal process. A useful report includes a concise description, affected service or workflow, observed impact, timestamps, actions already attempted, and the current owner. Incident reports should not expose unrelated restricted information.


```python
record = {
    "owner": "assigned-user",
    "status": "in_progress",
    "priority": "high",
    "validated": True,
}
```


## 8. Knowledge Retrieval

Intellex retrieval should return only chunks that the requesting user is authorized to see. Organization-visible documents are expected to be available broadly within the organization, while restricted documents must be filtered by the authorization conditions before generation. Retrieval ranking must never weaken ACL enforcement.


## 9. Example Access Matrix

The following matrix illustrates the intended model.


## 10. Test Marker

The unique validation marker ORG-DOC-01-ALPHA belongs to this organization-visible document. It is intentionally repeated in this document so retrieval testing can verify that authorized organization users can locate the correct source.


## Appendix 1: Operational Example

This synthetic appendix expands the Organization Employee Handbook scenario with an additional operational example. It provides enough natural-language context to exercise document parsing, chunk boundaries, metadata propagation, vector retrieval, reranking, and ACL filtering. The example remains within the same authorization boundary as the parent document. Test marker ORG-DOC-01-ALPHA remains associated with the document, while the surrounding prose provides semantically related material that can produce multiple retrieval candidates for the same query. This is appendix 1 of 6.


## Appendix 2: Operational Example

This synthetic appendix expands the Organization Employee Handbook scenario with an additional operational example. It provides enough natural-language context to exercise document parsing, chunk boundaries, metadata propagation, vector retrieval, reranking, and ACL filtering. The example remains within the same authorization boundary as the parent document. Test marker ORG-DOC-01-ALPHA remains associated with the document, while the surrounding prose provides semantically related material that can produce multiple retrieval candidates for the same query. This is appendix 2 of 6.


## Appendix 3: Operational Example

This synthetic appendix expands the Organization Employee Handbook scenario with an additional operational example. It provides enough natural-language context to exercise document parsing, chunk boundaries, metadata propagation, vector retrieval, reranking, and ACL filtering. The example remains within the same authorization boundary as the parent document. Test marker ORG-DOC-01-ALPHA remains associated with the document, while the surrounding prose provides semantically related material that can produce multiple retrieval candidates for the same query. This is appendix 3 of 6.


## Appendix 4: Operational Example

This synthetic appendix expands the Organization Employee Handbook scenario with an additional operational example. It provides enough natural-language context to exercise document parsing, chunk boundaries, metadata propagation, vector retrieval, reranking, and ACL filtering. The example remains within the same authorization boundary as the parent document. Test marker ORG-DOC-01-ALPHA remains associated with the document, while the surrounding prose provides semantically related material that can produce multiple retrieval candidates for the same query. This is appendix 4 of 6.


## Appendix 5: Operational Example

This synthetic appendix expands the Organization Employee Handbook scenario with an additional operational example. It provides enough natural-language context to exercise document parsing, chunk boundaries, metadata propagation, vector retrieval, reranking, and ACL filtering. The example remains within the same authorization boundary as the parent document. Test marker ORG-DOC-01-ALPHA remains associated with the document, while the surrounding prose provides semantically related material that can produce multiple retrieval candidates for the same query. This is appendix 5 of 6.


## Appendix 6: Operational Example

This synthetic appendix expands the Organization Employee Handbook scenario with an additional operational example. It provides enough natural-language context to exercise document parsing, chunk boundaries, metadata propagation, vector retrieval, reranking, and ACL filtering. The example remains within the same authorization boundary as the parent document. Test marker ORG-DOC-01-ALPHA remains associated with the document, while the surrounding prose provides semantically related material that can produce multiple retrieval candidates for the same query. This is appendix 6 of 6.
