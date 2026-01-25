# dcm4che-tests (Java)

Small CLI/test harness around dcm4che for DICOM operations.

## Commands
- `java -jar dcm4che-tests.jar store-scu <input> --target host:port [--calling AET] [--called AET]`
- `java -jar dcm4che-tests.jar store-scp --port N --output <dir> [--aet AET]`
- `java -jar dcm4che-tests.jar find <host:port> --level patient|study|series [--patient NAME] [--study UID]`
- `java -jar dcm4che-tests.jar c-move <host:port> --dest DEST_AET [--study UID]`
- `java -jar dcm4che-tests.jar c-get <host:port> --output <dir> [--study UID]`
- `java -jar dcm4che-tests.jar stgcmt <host:port> --files file1,file2`
- `java -jar dcm4che-tests.jar qido <url>` / `stow <url> <input>` / `wado <url> --output <file>`
- Structured report summary: `sr-summary <input>`
- RT consistency: `rt-check --plan <plan.dcm> [--dose <dose.dcm>] [--struct <rtstruct.dcm>]`

## Code layout
- `DicomOperations` stays as a thin facade over modular helpers.
- File/metadata actions live in `DicomFileOperations`; DIMSE echo/store in `DicomDimseOperations`.
- Query/Retrieve (C-FIND/MOVE/GET/Storage Commitment) is handled by `DicomQueryRetrieveOperations`.
- SR/RT checks are grouped in `DicomSrRtOperations`; shared IO helpers sit in `DicomIOUtils`.

## Tests
- Run fast unit slice: `mvn -q -Dtest=DicomOperationsTest,DicomWebOperationsTest test`
- DIMSE integration checks (local echo/store/find/move/stg cmt): `mvn -q -Dtest=DimseExpandedTest test`
  - `cgetStoresLocally` is currently `@Disabled` due to flaky in-process C-GET handshakes.
- CLI parsing/integration sanity: `mvn -q -Dtest=DicomToolsCliIntegrationTest test`

Logs are verbose because dcm4che networking uses INFO by default; set `-Dorg.slf4j.simpleLogger.defaultLogLevel=error` to reduce noise when running tests.***
