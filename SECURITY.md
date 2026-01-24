# Security Policy

## Supported Versions

Currently, sonotheia-examples is in active development. Security updates are provided for:

| Version | Supported          |
| ------- | ------------------ |
| Latest  | :white_check_mark: |

## Reporting a Vulnerability

**Please do NOT report security vulnerabilities through public GitHub issues.**

Instead, please report them via email to: **security@sonotheia.com**

When reporting a vulnerability, please include:

1. **Type of vulnerability** (e.g., XSS, SQL injection, dependency vulnerability, etc.)
2. **Full paths** of affected source files
3. **Location** of the affected code (tag/branch/commit)
4. **Step-by-step instructions** to reproduce the issue
5. **Proof-of-concept or exploit code** (if possible)
6. **Impact** of the vulnerability
7. **Suggested fix** (if you have one)

### Response Timeline

- **Initial Response**: Within 48 hours
- **Status Update**: Within 7 days
- **Fix Timeline**: Depends on severity
  - Critical: 7 days
  - High: 14 days
  - Medium: 30 days
  - Low: Next release cycle

## Security Best Practices

### API Key Management

**CRITICAL: Never commit API keys to version control**

1. **Use environment variables only**

   ```bash
   export ANTHROPIC_API_KEY='your-key'
   export OPENAI_API_KEY='your-key'
   export GEMINI_API_KEY='your-key'
   export SONOTHEIA_API_KEY='your-key'
   ```

2. **Secure storage**
   - Use secret management tools (AWS Secrets Manager, HashiCorp Vault, etc.)
   - For local development, use `.env` files (ensure `.gitignore` includes them)
   - For CI/CD, use encrypted secrets

3. **Key rotation**
   - Rotate API keys every 90 days
   - Immediately rotate if compromised
   - Use different keys for dev/staging/prod

### Dependency Security

**Regular Updates**: Check for vulnerabilities

```bash
# Install safety
pip install safety

# Check dependencies
safety check

# Or use pip-audit
pip install pip-audit
pip-audit
```

**Known Issues**:

- Review `pyproject.toml` regularly
- Update dependencies with security patches
- Use `dependabot` for automated alerts

### Secret Management

**NEVER commit**:

- API keys
- Passwords
- Private keys
- `.env` files
- Database credentials
- AWS credentials
- Terraform state files with secrets

**Use**:

- Environment variables
- Secret management services (AWS Secrets Manager, HashiCorp Vault)
- `.env.example` for documentation (without real values)
- Terraform remote state backends with encryption

### Example Code Security

This repository contains example code. When using examples:

1. **Review before use**: Always review example code before using in production
2. **Remove hardcoded values**: Replace any placeholder credentials
3. **Validate inputs**: Add input validation for production use
4. **Error handling**: Add proper error handling
5. **Security headers**: Add security headers for web examples

### Terraform Security

For Terraform examples:

1. **State file security**: Use remote state backends with encryption
2. **Secrets management**: Use AWS Secrets Manager or similar
3. **IAM permissions**: Follow principle of least privilege
4. **Resource tagging**: Tag resources for security compliance
5. **State locking**: Enable state locking to prevent conflicts

```hcl
# Example: Secure state backend
terraform {
  backend "s3" {
    bucket         = "my-terraform-state"
    key            = "examples/terraform.tfstate"
    region         = "us-east-1"
    encrypt        = true
    dynamodb_table = "terraform-state-lock"
  }
}
```

## Security Features

### Built-in Protections

1. **Input validation**: Examples use Pydantic where applicable
2. **API key isolation**: Keys never logged or exposed in examples
3. **Error handling**: Examples demonstrate proper error handling
4. **Type safety**: Examples include type hints

### Secure Defaults

- Examples require explicit API key setup
- No hardcoded credentials in examples
- Environment variable configuration demonstrated
- Minimal network exposure in examples

## Security Checklist

Before using examples in production:

- [ ] Review all example code
- [ ] Remove any hardcoded credentials
- [ ] Add input validation
- [ ] Add error handling
- [ ] Configure API keys securely
- [ ] Review dependencies for vulnerabilities
- [ ] Add security headers (for web examples)
- [ ] Configure proper IAM permissions (for AWS examples)
- [ ] Enable encryption for state files (for Terraform examples)

## Security Resources

### Tools

- **Safety**: Dependency vulnerability scanner
- **pip-audit**: Python package vulnerability auditor
- **Bandit**: Python security linter
- **Trivy**: Container vulnerability scanner
- **Checkov**: Terraform security scanner

### References

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [Python Security Best Practices](https://python.readthedocs.io/en/latest/library/security_warnings.html)
- [Terraform Security Best Practices](https://www.terraform.io/docs/cloud/guides/recommended-practices/index.html)
- [AWS Security Best Practices](https://aws.amazon.com/security/best-practices/)

## Contact

For security concerns, contact: **security@sonotheia.com**

For general issues: <https://github.com/doronpers/sonotheia-examples/issues>

---

**Last Updated**: 2026-01-24
