# IDIO DID - PDF Data Object Management

This project provides tools for creating and managing decentralized identifiers (DIDs) and data objects for PDF documents. It includes functionality for generating DIDs, creating data objects with embedded metadata, and verifying PDF documents.

## Features

- Generate ED25519 key pairs for DID creation
- Create DID:Key identifiers following W3C standards
- Embed metadata into PDF documents
- Verify PDF documents with embedded data objects
- Comprehensive logging for debugging and tracking

## Requirements

- Python 3.8+
- Required Python packages (see requirements.txt):
  - PyPDF2
  - cryptography
  - base58

## Installation

1. Clone the repository:
```bash
git clone [https://github.com/IDObjects/main.git](https://github.com/IDObjects/main.git)
cd idio_did