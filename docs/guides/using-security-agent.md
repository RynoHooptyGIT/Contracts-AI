# Using the Security Agent

Complete guide to using the Security Agent for vulnerability detection, NIST compliance, and risk assessment.

## Overview

The Security Agent provides comprehensive security analysis based on:
- OWASP Top 10
- NIST Cybersecurity Framework
- CWE Top 25
- CVE Database

## Modes

### audit - Full Security Audit
```bash
security audit
```

### scan - Quick Vulnerability Scan
```bash
security scan
```

### deps - Dependency Vulnerabilities
```bash
security deps
```

### secrets - Exposed Secrets Detection
```bash
security secrets
```

### compliance - NIST Compliance Check
```bash
security compliance
```

## Quick Start

Run a security scan before commits:
```bash
security scan
```

For full details, see: [Security Agent Specification](../../.claude/agents/security.md)

---

**Last Updated**: 2026-01-17
