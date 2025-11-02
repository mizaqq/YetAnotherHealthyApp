#!/usr/bin/env python3
"""
Environment setup script for YetAnotherHealthyApp backend.

This script helps create environment files for different deployment environments.
Run with: python scripts/create_env.py [environment]

Example:
    python scripts/create_env.py development
    python scripts/create_env.py production
"""

import argparse
import sys
from pathlib import Path
from typing import Any

# Template configurations for different environments
ENV_TEMPLATES: dict[str, dict[str, Any]] = {
    "development": {
        "APP_ENV": "development",
        "DEBUG": "true",
        "LOG_LEVEL": "DEBUG",
        "CORS_ORIGINS": '["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:3000"]',
        "SUPABASE_URL": "https://your-dev-project.supabase.co",
        "SUPABASE_SERVICE_ROLE_KEY": "your_dev_service_role_key",
        "OPENROUTER_API_KEY": "your_dev_openrouter_key",
        "comments": [
            "# Development environment configuration",
            "# Copy this to .env.development and fill in your actual values",
            "#",
            "# For local development, you can use:",
            "# - Supabase local development instance",
            "# - OpenRouter test API key",
            "# - Local database if needed",
        ],
    },
    "staging": {
        "APP_ENV": "staging",
        "DEBUG": "false",
        "LOG_LEVEL": "INFO",
        "CORS_ORIGINS": '["https://your-staging-domain.com"]',
        "SUPABASE_URL": "https://your-staging-project.supabase.co",
        "SUPABASE_SERVICE_ROLE_KEY": "your_staging_service_role_key",
        "OPENROUTER_API_KEY": "your_staging_openrouter_key",
        "comments": [
            "# Staging environment configuration",
            "# Copy this to .env.staging and fill in your actual values",
            "#",
            "# For staging deployment:",
            "# - Use staging Supabase project",
            "# - Production-like OpenRouter key",
            "# - Limited debug logging",
        ],
    },
    "production": {
        "APP_ENV": "production",
        "DEBUG": "false",
        "LOG_LEVEL": "WARNING",
        "CORS_ORIGINS": '["https://your-production-domain.com", "https://www.your-production-domain.com"]',
        "SUPABASE_URL": "https://your-prod-project.supabase.co",
        "SUPABASE_SERVICE_ROLE_KEY": "your_prod_service_role_key",
        "OPENROUTER_API_KEY": "your_prod_openrouter_key",
        "comments": [
            "# Production environment configuration",
            "# Copy this to .env.production and fill in your actual values",
            "#",
            "# Production requirements:",
            "# - Production Supabase project",
            "# - Production OpenRouter API key",
            "# - Minimal logging for performance",
            "# - Strict CORS policy",
        ],
    },
    "test": {
        "APP_ENV": "test",
        "DEBUG": "false",
        "LOG_LEVEL": "ERROR",
        "CORS_ORIGINS": '["http://localhost:5173"]',
        "SUPABASE_URL": "https://your-test-project.supabase.co",
        "SUPABASE_SERVICE_ROLE_KEY": "your_test_service_role_key",
        "OPENROUTER_API_KEY": "your_test_openrouter_key",
        "comments": [
            "# Test environment configuration",
            "# Copy this to .env.test and fill in your actual values",
            "#",
            "# For testing:",
            "# - Test Supabase instance",
            "# - Test OpenRouter key",
            "# - Minimal logging to reduce noise",
            "# - FastAPI TestClient compatible settings",
        ],
    },
}

BASE_TEMPLATE = {
    "API_V1_PREFIX": "/api/v1",
    "APP_NAME": "YetAnotherHealthyApp",
    "APP_VERSION": "0.1.0",
    "ANALYSIS_MODEL": "google/gemini-2.0-flash-001",
    "OPENROUTER_DEFAULT_MODEL": "google/gemini-2.0-flash-001",
    "OPENROUTER_DEFAULT_TEMPERATURE": "0.2",
    "OPENROUTER_DEFAULT_TOP_P": "0.95",
    "OPENROUTER_MAX_OUTPUT_TOKENS": "600",
    "OPENROUTER_REQUEST_TIMEOUT_SECONDS": "30.0",
    "OPENROUTER_MAX_RETRIES": "3",
    "OPENROUTER_RETRY_BACKOFF_INITIAL": "2",
    "OPENROUTER_RETRY_BACKOFF_MAX": "10.0",
    "OPENROUTER_BASE_URL": "https://openrouter.ai/api/v1",
    "comments": [
        "# Base configuration - copy to .env and fill in your values",
        "# This file is loaded first, then environment-specific overrides",
        "#",
        "# REQUIRED VARIABLES:",
        "# - SUPABASE_URL: Your Supabase project URL",
        "# - SUPABASE_SERVICE_ROLE_KEY: Your Supabase service role key",
        "# - OPENROUTER_API_KEY: Your OpenRouter API key",
    ],
}


def create_env_file(env_name: str, output_path: Path) -> None:
    """Create an environment file for the specified environment."""

    if env_name not in ENV_TEMPLATES:
        print(f"Error: Unknown environment '{env_name}'")
        print(f"Available environments: {', '.join(ENV_TEMPLATES.keys())}")
        sys.exit(1)

    # Get template for the environment
    env_template = ENV_TEMPLATES[env_name]
    template = BASE_TEMPLATE.copy()
    template.update(env_template)

    # Generate content
    lines = []
    lines.extend(template.get("comments", []))
    lines.append("")  # Empty line after comments

    # Add configuration variables
    for key, value in template.items():
        if key != "comments":
            lines.append(f"{key}={value}")

    # Write to file
    try:
        with open(output_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
        print(f"✓ Created {output_path}")
        print(f"  Environment: {env_name}")
        print("  Edit this file and add your actual API keys and URLs")
        print("  ⚠️  Required: SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY, OPENROUTER_API_KEY")
    except Exception as e:
        print(f"Error creating {output_path}: {e}")
        sys.exit(1)


def create_base_env() -> None:
    """Create the base .env file."""
    create_env_file("base", Path(".env.example"))


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Create environment configuration files",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/create_env.py development    # Create .env.development
  python scripts/create_env.py production     # Create .env.production
  python scripts/create_env.py base           # Create .env.example

This will create template files that you need to edit with your actual
API keys and configuration values.
        """,
    )

    parser.add_argument(
        "environment",
        choices=list(ENV_TEMPLATES.keys()) + ["base"],
        help="Environment to create configuration for",
    )

    args = parser.parse_args()

    if args.environment == "base":
        create_base_env()
    else:
        filename = f".env.{args.environment}.example"
        create_env_file(args.environment, Path(filename))


if __name__ == "__main__":
    main()
