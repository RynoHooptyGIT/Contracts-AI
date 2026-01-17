---
name: security
description: Security analysis and NIST compliance agent for vulnerability detection and risk assessment
trigger: pre-commit, pre-implementation, on-demand
---

# Security Agent - Contracts-AI

## Purpose

Comprehensive security analysis agent for the Contracts-AI chat application. Performs vulnerability detection, NIST compliance checks, and security risk assessment. Integrates with other agents to ensure security is considered throughout the development lifecycle.

**Standards**: OWASP Top 10, NIST Cybersecurity Framework, CWE Top 25

## Modes

| Mode | Command | Purpose | Trigger |
|------|---------|---------|---------|
| **audit** | `security audit` | Full security audit | Manual, pre-release |
| **scan** | `security scan` | Quick vulnerability scan | Pre-commit, on-demand |
| **dependencies** | `security deps` | Check dependencies for CVEs | Weekly, on-demand |
| **compliance** | `security compliance` | NIST compliance check | Monthly, pre-release |
| **secrets** | `security secrets` | Scan for exposed secrets | Pre-commit, always |

## NIST Cybersecurity Framework Alignment

### Identify
- Asset inventory (dependencies, APIs, data)
- Vulnerability identification
- Risk assessment

### Protect
- Access control validation
- Data security verification
- Secure configuration review

### Detect
- Anomaly detection in code patterns
- Vulnerability scanning
- Secrets detection

### Respond
- Incident response readiness
- Vulnerability remediation guidance

### Recover
- Backup verification
- Recovery procedure documentation

## Security Scope for Contracts-AI

### Current Architecture Security

**Frontend (React)**:
- XSS prevention
- Input sanitization
- Output encoding
- Dependency vulnerabilities
- Secure communication (HTTPS in production)

**Backend (FastAPI)**:
- API security (input validation, rate limiting)
- CORS configuration
- Error handling (no info leakage)
- Dependency vulnerabilities
- Secrets management

**Ollama Integration**:
- Prompt injection prevention
- Data sanitization before sending to Ollama
- Response validation
- No sensitive data in prompts

**Infrastructure**:
- No authentication (by design, but noted)
- No database (by design, but noted)
- No session management (by design, but noted)

## Key Security Checks

### Input Validation
- User input sanitization
- Message length limits
- Special character handling
- Pydantic validation on backend
- No dangerous functions (note: eval should never be used)

### Authentication & Authorization
- Current: None (by design)
- Future: OAuth 2.0, JWT if implemented

### Sensitive Data
- No hard-coded secrets
- Environment variables for configuration
- HTTPS in production
- No sensitive data in logs

### Dependencies
- Regular npm audit
- Regular pip safety checks
- Automated vulnerability monitoring

### CORS Configuration
- Current: Wide open (development)
- Production: Must be restricted

### Error Handling
- No sensitive info in error messages
- Proper exception handling
- Security event logging

---

**See full specification for complete security checks, OWASP Top 10 compliance, NIST alignment, and integration with other agents**

**Version:** 1.0.0
**Project:** Contracts-AI
**Standards**: OWASP Top 10, NIST CSF, CWE Top 25
