---
name: security-audit
description: Guide for scanning repositories for vulnerabilities, CVEs, and insecure code patterns in Python FastAPI and Node projects.
license: See LICENSE.txt
---

# Security Audit Guide

## Overview

Perform a security audit on the repository to identify:

- dependency vulnerabilities
- insecure coding practices
- OWASP risks
- potential CVE exposures

The project technology stack includes:

- Python FastAPI backend
- Nuxt.js / Vue frontend
- Docker-based deployment

## When to Use

Use this skill when performing:

- vulnerability analysis
- dependency audits
- security reviews
- pre-release security checks

---

# Process

## Step 1 — Install Required Security Tools

Run the setup script to create a local virtual environment and  install security scanning dependencies by invoking [script](./scripts/install-scan-utils.sh)

This script installs required tools such as:

- pip-audit
- bandit
- semgrep (optional)
- project Python dependencies from `requirements.txt`

---

## Step 2 — Run Vulnerability Scans

Execute the security scanning script [script](./scripts/scan.sh) to perform comprehensive vulnerability analysis.


The scan script should run tools such as:

Python dependency vulnerabilities
- `pip-audit` to identify vulnerable packages and versions
- `bandit -r .` to analyze code for insecure patterns
- `npm audit` for frontend dependency vulnerabilities (if applicable)
- `semgrep` for custom security rules (if configured)
- Static analysis for OWASP risks (e.g. injection, auth issues)


---

## Step 3 — Analyze Results

For each issue determine:

Severity  
OWASP category  
Affected component  
Exploit scenario  
Recommended fix

---

## Step 4 — Prioritize Issues

Prioritize vulnerabilities that:

- affect authentication
- expose sensitive data
- allow injection
- enable remote code execution
- affect production deployment security

---

# Output Format

Severity  
Location  
Issue  
Impact  
Suggested Fix

---

<!-- # Integration

This skill is typically invoked through the repository prompt:
- `dependency-audit` prompt should reference this skill for vulnerability scanning and classification. 
- `security-auditor` agent should use this process when performing vulnerability analysis. -->
