# IDIO DID - Identity Bound Data: Decentralized Identity and Policy Management

A comprehensive system for managing decentralized identifiers (DIDs) and implementing policy-based access control for data objects. This project provides tools for creating, managing, and verifying DIDs, as well as enforcing age-based policies using Open Policy Agent (OPA).

## Project Overview

This project consists of multiple components implemented in different languages:

- **Python**: Core data object management, PDF handling, and DID generation
- **Go**: SSN hashing functionality
- **Rust**: Policy enforcement and WASM compilation
- **JavaScript**: Browser extension and UI components

## Key Features

- **Decentralized Identity Management**
  - Generate ED25519 key pairs for DID creation
  - Create DID:Key identifiers following W3C standards
  - Support for multiple cryptographic operations

- **Data Object Management**
  - Create and manage PDF data objects with embedded metadata
  - Verify PDF documents with embedded data objects
  - Comprehensive logging and debugging support

- **Policy-Based Access Control**
  - Age-based policies (e.g., under_18, over21)
  - Policy enforcement using Open Policy Agent (OPA)
  - WASM-based policy execution

## Technical Stack

- **Backend**
  - Python 3.8+
  - Go for cryptographic operations
  - Rust for policy compilation
  - Streamlit for web interface

- **Frontend**
  - JavaScript/HTML/CSS
  - Browser extension support

## Requirements

- Python 3.8+
- Required Python packages (see requirements.txt):
  - PyPDF2
  - cryptography
  - base58
  - streamlit
- Go 1.18+
- Rust 1.60+
- Node.js for browser extension development

## Installation

1. Clone the repository:
```bash
git clone [https://github.com/IDObjects/main.git](https://github.com/IDObjects/main.git)
cd idio_did
```

2. Install Python dependencies:
```bash
pip install -r requirements.txt
```

3. Build the policy WASM module:
```bash
cargo build --release
```

4. Build the browser extension (if needed):
```bash
npm install
npm run build
```

## Usage

The project includes several main components:

- `app.py`: Main Streamlit application for data object management
- `pdf_data_object.py`: PDF data object creation and verification
- `did_generator.py`: DID generation utilities
- `policies/`: OPA policy definitions
- `ssn_hash.go`: SSN hashing implementation
- `over21.rs`: Policy enforcement module

## Security

The system implements multiple security measures:

- Cryptographic signing of DIDs
- Secure SSN handling
- Policy-based access control
- End-to-end encryption for sensitive data

## Contributing

Contributions are welcome! Please see CONTRIBUTING.md for details on how to contribute to this project.

## License

[Add appropriate license information here]