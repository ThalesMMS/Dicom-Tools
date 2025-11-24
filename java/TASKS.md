# Java Tasks (dcm4chee)
- CLI/REST de contrato: criar um entrypoint em `dcm4che-tests` (ou módulo dedicado) que mapeie operações do contrato (info/anonymize/to_image/transcode/validate/echo/dump/stats) com saída JSON.
- Empacotar como jar executável (`JAVA_DICOM_TOOLS_CMD=java -jar ...`) compatível com `interface/adapters/java_cli.py` e documentar opções.
- Reutilizar/expandir os testes existentes (`mvn test` já passa) para cobrir o contrato completo com `sample_series` e validar stdout/JSON.
