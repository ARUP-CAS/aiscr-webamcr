## ADDED Requirements

### Requirement: IGSN failure does not undo a saved PAS API change

When a PAS API request that changes an archived (SN4) samostatný nález — PATCH `evidencni-cislo` or POST
`upload-foto` — has saved its database changes, the system SHALL also commit the request's Fedora transaction, even
if the subsequent IGSN (DataCite) update fails for any reason. The database and Fedora SHALL end the request in the
same state.

#### Scenario: Evidenční číslo PATCH with failing IGSN update

- **WHEN** an authorised client sends PATCH `evidencni-cislo` with a new value for an SN4 record and the IGSN update
  fails
- **THEN** the new `evidencni_cislo` and its history records are stored in the database
- **AND** the Fedora metadata of the record contains the new `evidencni_cislo`

#### Scenario: Photo upload with failing IGSN update

- **WHEN** an authorised client uploads a photo to an SN4 record and the IGSN update fails
- **THEN** the `Soubor` record and its history are stored in the database
- **AND** the binary file is committed in Fedora under the path stored in the `Soubor` record

### Requirement: IGSN update runs after the change is committed

For an SN4 record, the PAS API SHALL send the IGSN update only after the database transaction and the Fedora
transaction of the request have been committed, and the IGSN payload SHALL reflect the committed state including the
metadata written by `save_metadata()`.

#### Scenario: Fedora commit fails

- **WHEN** the Fedora transaction of a PATCH `evidencni-cislo` or POST `upload-foto` request fails to commit
- **THEN** no IGSN update is sent for that request
- **AND** the endpoint responds with HTTP 500 as before

#### Scenario: Successful update sends current data

- **WHEN** a PATCH `evidencni-cislo` request for an SN4 record succeeds
- **THEN** the IGSN update sent to DataCite contains the new `evidencni_cislo`

### Requirement: IGSN update outcome is classified

The PAS API and the retry task SHALL send the IGSN update with DataCite response status checking enabled. A failed
update SHALL be classified as retryable when DataCite cannot be reached (on the existence check or the update), the
existence check returns 5xx, or the update returns 429 or 5xx. Every other DataCite error response of the update,
including 401 and 403, SHALL be classified as non-retryable.

#### Scenario: DataCite unreachable

- **WHEN** the connection to DataCite fails during the IGSN update
- **THEN** the failure is classified as retryable

#### Scenario: DataCite server error

- **WHEN** DataCite answers the IGSN update with status 503
- **THEN** the failure is classified as retryable

#### Scenario: DataCite rejects the data

- **WHEN** DataCite answers the IGSN update with status 422
- **THEN** the failure is classified as non-retryable

#### Scenario: Wrong DataCite credentials

- **WHEN** DataCite answers the IGSN update with status 401
- **THEN** the failure is classified as non-retryable

### Requirement: Client is told the IGSN update outcome

When the IGSN update of an SN4 record fails after the change was committed, the PAS API SHALL return the endpoint's
normal success status and XML metadata body (200 for PATCH `evidencni-cislo`, 201 for POST `upload-foto`) and SHALL
add the response header `X-IGSN-Status` with value `retry-pending` for a retryable failure or `failed` for a
non-retryable failure. Responses in which the IGSN update succeeded or was not needed SHALL NOT carry the header.

#### Scenario: Retryable failure is signalled

- **WHEN** the IGSN update of a PATCH `evidencni-cislo` request for an SN4 record fails with a retryable failure
- **THEN** the response status is 200 with the XML metadata body and the headers `X-Record-ID` and `Location`
- **AND** the response carries the header `X-IGSN-Status: retry-pending`

#### Scenario: Non-retryable failure is signalled

- **WHEN** the IGSN update of a POST `upload-foto` request for an SN4 record is rejected by DataCite with status 422
- **THEN** the response status is 201 with the XML metadata body
- **AND** the response carries the header `X-IGSN-Status: failed`

#### Scenario: Successful IGSN update is not signalled

- **WHEN** the IGSN update of a POST `upload-foto` request succeeds
- **THEN** the response status is 201 and the response does not carry the `X-IGSN-Status` header

### Requirement: Retryable IGSN failure is retried in the background

When the IGSN update of an SN4 record fails with a retryable failure in a PAS API request, the system SHALL schedule a
background task that repeats the IGSN update for that record. A non-retryable failure SHALL NOT schedule the task. The
task SHALL reload the record from the database before each attempt and SHALL stop without sending anything when the
record no longer exists, is no longer in state SN4, or has no IGSN.

#### Scenario: DataCite becomes available again

- **WHEN** the retry task runs after DataCite has recovered
- **THEN** DataCite receives the record's current metadata and the task finishes without further retries

#### Scenario: Record left SN4 before the retry

- **WHEN** the retry task runs for a record that is no longer in state SN4
- **THEN** the task finishes without sending an IGSN update

#### Scenario: Non-retryable failure in the request

- **WHEN** the IGSN update of a PAS API request is rejected by DataCite with status 422
- **THEN** no retry task is scheduled

### Requirement: Retry delay grows exponentially

The delay before the n-th background attempt (n starting at 1) SHALL be
`min(IGSN_RETRY_BASE_DELAY × 2^(n−1), IGSN_RETRY_MAX_DELAY)`, and the task SHALL make at most
`1 + IGSN_RETRY_MAX_RETRIES` attempts. These values SHALL be named constants: `IGSN_RETRY_BASE_DELAY` = 60 s,
`IGSN_RETRY_MAX_DELAY` = 6 h, `IGSN_RETRY_MAX_RETRIES` = 20.

#### Scenario: Delay grows exponentially

- **WHEN** the first background attempts fail with a retryable failure
- **THEN** the delays before attempts 1, 2, 3 and 4 are 60 s, 120 s, 240 s and 480 s
- **AND** no delay exceeds 6 h

### Requirement: Retry stops on exhaustion or non-retryable failure

The retry task SHALL schedule another attempt only after a retryable failure. When the task stops without a successful
update, the system SHALL log an error that includes the record's `ident_cely`.

#### Scenario: Retries are exhausted

- **WHEN** every attempt of the retry task fails with a retryable failure until 20 retries have been made
- **THEN** the task stops and an error log entry with the record's `ident_cely` is written

#### Scenario: Non-retryable rejection during a retry

- **WHEN** DataCite answers a retried update with status 422
- **THEN** the task stops without scheduling another retry and logs an error with the record's `ident_cely`

### Requirement: IGSN outcome of a request is recorded in the API request log

The `ApiRequestLog` entry of a PAS API request SHALL keep status `success` when the IGSN update fails after the change
was committed, and SHALL store `igsn_status` = `retry_pending` for a retryable failure or `failed` for a non-retryable
failure. Entries of requests whose IGSN update succeeded or was not needed SHALL keep `igsn_status` empty. The field
SHALL be visible and filterable in the Django admin of `ApiRequestLog`.

#### Scenario: Pending update is audited

- **WHEN** a PATCH `evidencni-cislo` request returns `X-IGSN-Status: retry-pending`
- **THEN** its `ApiRequestLog` entry has status `success` and `igsn_status` `retry_pending`

#### Scenario: Rejected update is audited

- **WHEN** a POST `upload-foto` request returns `X-IGSN-Status: failed`
- **THEN** its `ApiRequestLog` entry has status `success` and `igsn_status` `failed`

#### Scenario: Normal request is not marked

- **WHEN** the IGSN update of a POST `upload-foto` request succeeds
- **THEN** its `ApiRequestLog` entry has an empty `igsn_status`

### Requirement: Retry outcome is recorded in the API request log

When the retry task ends, it SHALL set `igsn_status` of every `ApiRequestLog` entry of that record that is still
`retry_pending` to `updated` after a successful IGSN update, or to `failed` when it stops without one.

#### Scenario: Retry outcome is audited

- **WHEN** the retry task for that record later updates DataCite successfully
- **THEN** the `ApiRequestLog` entry has `igsn_status` `updated`

#### Scenario: Retry failure is audited

- **WHEN** the retry task stops because retries are exhausted or DataCite rejected the update
- **THEN** every `retry_pending` `ApiRequestLog` entry of that record has `igsn_status` `failed`

### Requirement: Failed IGSN updates can be re-run by an operator

The system SHALL provide the management command `retry_failed_igsn_updates`. For every samostatný nález that has at
least one `ApiRequestLog` entry with `igsn_status` `failed`, the command SHALL set those entries to `retry_pending` and
schedule the retry task for the record without delay. The option `--ident` SHALL limit the run to the given
`ident_cely` values, and the option `--dry-run` SHALL only list the affected records without changing anything.

#### Scenario: Re-run after a credentials fix

- **WHEN** an operator runs `retry_failed_igsn_updates` after correcting the DataCite credentials
- **THEN** every record with a `failed` entry gets one scheduled retry task
- **AND** its `failed` entries are set to `retry_pending`

#### Scenario: Dry run

- **WHEN** an operator runs `retry_failed_igsn_updates --dry-run`
- **THEN** the command prints the affected `ident_cely` values and changes no entry and schedules no task

#### Scenario: Limited to selected records

- **WHEN** an operator runs `retry_failed_igsn_updates --ident C-202009779-N00001`
- **THEN** only that record's `failed` entries are reset and only its retry task is scheduled
