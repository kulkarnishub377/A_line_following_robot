# Security Policy

## Supported Versions

The following versions of the Line Following Robot project are currently receiving security updates:

| Version | Supported          |
|---------|--------------------|
| 1.0.x   | ✅ Yes             |
| < 1.0   | ❌ No              |

## Reporting a Vulnerability

We take the security of this project seriously. If you have discovered a security vulnerability, we appreciate your responsible disclosure.

### How to Report

**Please do NOT report security vulnerabilities via public GitHub issues.**

Instead, please report them using one of the following methods:

1. **GitHub Private Vulnerability Reporting** (preferred):
   - Go to the [Security tab](https://github.com/kulkarnishub377/A_line_following_robot/security/advisories/new) of this repository
   - Click **"Report a vulnerability"**
   - Fill in the details

2. **Email**: Contact the maintainer directly through the GitHub profile at [@kulkarnishub377](https://github.com/kulkarnishub377)

### What to Include

When reporting a vulnerability, please include:

- A clear description of the vulnerability
- Steps to reproduce the issue
- Potential impact of the vulnerability
- Any suggested mitigations or fixes (optional)

### What to Expect

- **Acknowledgement**: You will receive a response within **48 hours** confirming receipt of your report.
- **Assessment**: Within **7 days**, we will assess the severity and impact.
- **Resolution**: We aim to address confirmed vulnerabilities within **30 days**.
- **Credit**: With your permission, we will acknowledge your contribution in the release notes.

## Security Scope

This is an open-source educational robotics project. The primary security considerations are:

### In Scope
- Vulnerabilities in Python scripts that could cause unintended system behavior
- Issues in CI/CD workflows that could expose secrets or allow privilege escalation
- Dependency vulnerabilities in `python/requirements.txt`

### Out of Scope
- The Arduino firmware itself (runs on isolated embedded hardware with no network access)
- Physical hardware safety (always follow safe electronics practices)
- Issues requiring physical access to the hardware

## Best Practices for Users

When using this project:

1. **Keep dependencies updated**: Regularly update Python packages listed in `python/requirements.txt`
2. **Review CI/CD workflows**: Before forking and running workflows, review `.github/workflows/` files
3. **Secure your Arduino**: Do not expose your Arduino to untrusted networks
4. **Power safety**: Always follow proper power supply guidelines to avoid hardware damage

## Attribution

This security policy is adapted from common open-source security policy templates. Thank you for helping keep this project safe.
