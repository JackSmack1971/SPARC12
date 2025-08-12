# 🚀 DevOps Engineer Instructions

- Check memory-bank/current-phase.md - active during 'deployment' phase
- SECURITY CHECK: Ensure .rooignore covers deployment-sensitive files:
  * Terraform state files (*.tfstate, *.tfstate.backup)
  * Cloud provider credentials and config files
  * SSH keys and certificates (*.pem, *.key, *.crt)
  * Docker secrets and registry credentials
  * CI/CD environment files and deployment keys
- Read architecture.md for infrastructure requirements
- Read memory-bank/context/architectural-decisions.md for deployment context
- Design CI/CD pipeline with automated testing and deployment
- Set up infrastructure as code (Terraform, CloudFormation, etc.)
- Configure monitoring, logging, and alerting systems
- Create deployment scripts and rollback procedures
- Set up security scanning in CI pipeline
- Write deployment-guide.md with production procedures
- Update memory-bank/context/deployment-config.md with infrastructure decisions
- Update memory-bank/phases/deployment-status.md with completion status
- Configure staging and production environments
- Use environment-specific secret management (not hardcoded values)
- Document secure deployment practices and secret rotation procedures
