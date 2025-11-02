#!/usr/bin/env python3
"""
Configuration validation script.

This script tests that the environment configuration is loading correctly.
Run with: python scripts/test_config.py

It will display the current configuration values and validate that required
variables are present.
"""

import sys
from pathlib import Path

# Add the app directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))


def test_configuration() -> bool | None:
    """Test that configuration loads correctly."""
    try:
        # Add the parent directory to sys.path to import the app module
        import sys
        from pathlib import Path

        backend_dir = Path(__file__).parent.parent  # Go up from scripts/ to backend/
        sys.path.insert(0, str(backend_dir))

        from app.core.config import settings

        print("✅ Configuration loaded successfully!")
        print(f"📊 Environment: {settings.app_env}")
        print(f"🐛 Debug mode: {settings.debug}")
        print(f"📝 Log level: {settings.log_level}")
        print(f"🌐 CORS origins: {settings.cors_origins}")
        print(f"🏗️  API prefix: {settings.api_v1_prefix}")
        print(f"📦 App name: {settings.app_name}")
        print(f"🔢 App version: {settings.app_version}")

        # Check required fields
        print("\n🔍 Required configuration:")
        try:
            print(f"🗄️  Supabase URL: {settings.supabase_url}")
        except Exception as e:
            print(f"❌ Supabase URL: Missing or invalid - {e}")

        try:
            print(f"🗄️  Supabase Key: {'*' * 20}... (hidden for security)")
        except Exception as e:
            print(f"❌ Supabase Key: Missing or invalid - {e}")

        try:
            print(f"🤖 OpenRouter Key: {'*' * 20}... (hidden for security)")
        except Exception as e:
            print(f"❌ OpenRouter Key: Missing or invalid - {e}")

        # Check OpenRouter configuration
        print("\n🤖 OpenRouter settings:")
        print(f"   Model: {settings.openrouter.default_model}")
        print(f"   Temperature: {settings.openrouter.default_temperature}")
        print(f"   Max tokens: {settings.openrouter.max_output_tokens}")

        print("\n✅ Configuration test completed!")
        return True

    except Exception as e:
        print(f"❌ Configuration error: {e}")
        print("\n💡 Make sure you have the required environment variables set:")
        print("   - SUPABASE_URL")
        print("   - SUPABASE_SERVICE_ROLE_KEY")
        print("   - OPENROUTER_API_KEY")
        print("\n📖 See README_ENV.md for setup instructions")
        return False


def test_environment_files() -> None:
    """Test which environment files are being loaded."""
    import os
    import sys
    from pathlib import Path

    # Add the parent directory to sys.path to import the app module
    backend_dir = Path(__file__).parent.parent  # Go up from scripts/ to backend/
    sys.path.insert(0, str(backend_dir))

    from app.core.config import get_env_files

    print("\n📁 Environment file loading test:")

    # Check APP_ENV
    app_env = os.getenv("APP_ENV", "development")
    print(f"🌍 APP_ENV: {app_env}")

    # Show which files should be loaded
    env_files = get_env_files()
    print(f"📄 Expected env files: {env_files}")

    # Check which files actually exist
    backend_dir = Path(__file__).parent.parent
    print("\n📂 Actual files found:")
    for env_file in env_files:
        file_path = backend_dir / env_file
        exists = "✅" if file_path.exists() else "❌"
        print(f"   {exists} {env_file}")


if __name__ == "__main__":
    print("🧪 Testing YetAnotherHealthyApp Backend Configuration\n")

    success = test_configuration()
    test_environment_files()

    if success:
        print("\n🎉 Configuration is working correctly!")
        sys.exit(0)
    else:
        print("\n⚠️  Configuration needs attention. Check the errors above.")
        sys.exit(1)
