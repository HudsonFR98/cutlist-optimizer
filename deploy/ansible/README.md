# Ansible Deployment Structure

This directory contains the modularized Ansible deployment configuration for the cutlist_optimizer application.

## Structure

```
deploy/ansible/
├── docker_deploy.yml          # Main playbook
├── inventory.ini              # Host inventory
├── requirements.yml           # Ansible dependencies
├── README.md                 # This file
└── roles/                    # Modular roles
    ├── docker/               # Docker installation
    │   └── tasks/main.yml
    ├── directories/          # Directory and permission setup
    │   └── tasks/main.yml
    ├── registry/             # Docker registry authentication
    │   └── tasks/main.yml
    ├── files/                # File copying tasks
    │   └── tasks/main.yml
    ├── containers/           # Container management
    │   └── tasks/main.yml
    └── verification/         # Verification and testing
        └── tasks/main.yml
```

## Roles Description

### docker
- Installs Docker dependencies and packages
- Adds Docker repository and GPG key
- Installs Docker CE and related tools
- Installs PostgreSQL client

### directories
- Creates necessary directories for logs, data, and configuration
- Sets proper permissions for Docker containers
- Creates log files with correct ownership

### registry
- Authenticates with GitLab Container Registry
- Handles Docker login for image pulling

### files
- Copies initialization scripts to remote server
- Copies SQL reset script
- Copies Nginx configuration files

### containers
- Manages Docker containers (stop, remove, create)
- Creates Docker network
- Runs PostgreSQL, application, and Nginx containers
- Handles health checks and container readiness
- Manages different deployment scenarios (deploy vs update)

### verification
- Verifies network connectivity between containers
- Runs tests in test environment
- Displays test results and handles failures

## Usage

The main playbook `docker_deploy.yml` now uses a modular approach with roles instead of inline tasks. This provides:

- **Better organization**: Each role has a specific responsibility
- **Easier maintenance**: Changes to specific functionality are isolated
- **Reusability**: Roles can be reused in other playbooks
- **Readability**: The main playbook is much shorter and clearer

## Benefits of Modularization

1. **Maintainability**: Each role focuses on a specific aspect of deployment
2. **Reusability**: Roles can be used independently or in different combinations
3. **Testing**: Individual roles can be tested separately
4. **Documentation**: Each role is self-documenting through its structure
5. **Version Control**: Changes to specific functionality are easier to track

## Original vs New Structure

**Before**: Single 284-line file with all tasks mixed together
**After**: 6 focused roles with clear responsibilities, plus a concise main playbook

This modular approach makes the deployment process more maintainable and easier to understand. 