# FatturaPA XSD Schemas

This directory stores the official XSD schema files published by the
Agenzia delle Entrate (AdE) for FatturaPA validation.

## How to download

1. Visit the official AdE page:
   https://www.fatturapa.gov.it/it/norme-e-regole/documentazione-fattura-elettronica/formato-fatturapa/

2. Download the XSD package for each schema version needed:
   - **v1.2**: `Schema_del_file_xml_FatturaPA_v1.2.xsd`
   - **v1.3**: `Schema_del_file_xml_FatturaPA_v1.3.1.xsd`

3. Place the files in this directory:
   ```
   src/fatturapa_mcp/schemas/
   ├── FatturaPA_v1.2.xsd
   └── FatturaPA_v1.3.xsd
   ```

## Why XSD files are not bundled

AdE updates the schemas occasionally. Bundling them would require a release
for every schema revision. Downloading them at setup time ensures you always
validate against the current official version.

## Namespaces

| Version | Namespace URI |
|---------|--------------|
| v1.2 | `http://ivaservizi.agenziaentrate.gov.it/docs/xsd/fatture/v1.2` |
| v1.3 | `http://ivaservizi.agenziaentrate.gov.it/docs/xsd/fatture/v1.3` |
