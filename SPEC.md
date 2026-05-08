# Project Specification — fatturapa-mcp-server

## Overview

An MCP (Model Context Protocol) server exposing tools for working with Italian
electronic invoices (FatturaPA) and the SDI (Sistema di Interscambio) system.

The server is designed to be used with Claude Desktop or any MCP-compatible
client, enabling AI assistants to validate, inspect, and reason about Italian
e-invoices.

---

## Tools

### 1. `validate_invoice`

Validates a FatturaPA XML document against the official AdE XSD schemas.

**Input**:
- `xml_content` (string): Raw XML content of the FatturaPA document

**Output**:
- `valid` (bool): Whether the document passed XSD validation
- `version` (string): Detected schema version (`"1.2"` or `"1.3"`)
- `errors` (array of strings): Validation error messages; empty if valid

**Notes**:
- Schema version is auto-detected from the XML namespace
- XSD files must be present in `src/fatturapa_mcp/schemas/`

---

### 2. `extract_invoice_data`

Extracts key structured data from a valid FatturaPA XML document.

**Input**:
- `xml_content` (string): Raw XML content of a validated FatturaPA document

**Output**:
- `invoice_number` (string)
- `invoice_date` (string, ISO 8601)
- `total_amount` (number)
- `currency` (string)
- `supplier_piva` (string)
- `supplier_name` (string)
- `customer_piva` (string)
- `customer_name` (string)
- `document_type` (string, e.g. `"TD01"`)
- `line_items` (array)

---

### 3. `lookup_sdi_error`

Returns the human-readable description and resolution hint for an SDI error code.

**Input**:
- `error_code` (string): SDI error code (e.g., `"00001"`)

**Output**:
- `code` (string)
- `description` (string): Official Italian description
- `category` (string)
- `resolution` (string): Suggested resolution

---

### 4. `check_piva`

Validates an Italian P.IVA (VAT number) using the official checksum algorithm.
No network call required.

**Input**:
- `piva` (string): 11-digit P.IVA, optionally prefixed with `"IT"`

**Output**:
- `valid` (bool)
- `piva` (string): Normalised 11-digit form
- `reason` (string or null): Failure reason if invalid

---

### 5. `verify_piva_vies`

Verifies a European VAT number against the EU VIES REST API.

**Input**:
- `country_code` (string): ISO 3166-1 alpha-2 country code
- `vat_number` (string): VAT number without country prefix

**Output**:
- `valid` (bool)
- `name` (string or null): Business name if disclosed
- `address` (string or null): Address if disclosed
- `source` (string): `"vies"` or `"unavailable"`

---

## Constraints

- Python 3.11+
- MCP transport: stdio (default for Claude Desktop)
- No persistent state between tool calls
- No direct SDI communication
- No authentication required on the server

---

## Reference Documents

- FatturaPA format specification: https://www.fatturapa.gov.it/
- MCP specification: https://modelcontextprotocol.io/
- EU VIES API: https://ec.europa.eu/taxation_customs/vies/
