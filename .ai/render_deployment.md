# RENDER DEPLOYMENT CONFIGURATION INSTRUCTIONS:

#

# To deploy this image to Render Web Service, follow these steps:

#

# 1. Create a new Web Service in Render Dashboard:

# - Go to https://dashboard.render.com

# - Click "New +" → "Web Service"

# - Select "Deploy an existing image from a registry"

#

# 2. Configure the Web Service:

# - Image URL: ghcr.io/mizaqq/yetanotherhealthyapp:latest

# (or use specific SHA: ghcr.io/mizaqq/yetanotherhealthyapp:<commit-sha>)

# - Region: Choose closest to your users

# - Instance Type: Choose based on your needs (Free/Starter/Standard)

#

# 3. Set Environment Variables in Render:

# - Add all required environment variables from your .env file

# - Example: SUPABASE_URL, SUPABASE_KEY, OPENROUTER_API_KEY, etc.

# - PUBLIC_ENV_NAME: production (or staging)

#

# 4. Configure Service Settings:

# - Port: 8000 (FastAPI default)

# - Health Check Path: /api/v1/health

# - Auto-Deploy: Enable "Auto-Deploy from Image Registry"

#

# 5. Authentication for Private Registry (GHCR):

# - In Render Dashboard → Service Settings → Environment

# - Add Registry Credentials:

# \* Registry: ghcr.io

# \* Username: Your GitHub username (mizaqq)

# \* Password: GitHub Personal Access Token with read:packages scope

#

# 6. Optional - Get Deploy Hook for Manual Triggers:

# - Go to Service Settings → Deploy Hook

# - Copy the Deploy Hook URL

# - Add it as a secret in GitHub: Settings → Secrets → Actions → New repository secret

# Name: RENDER_DEPLOY_HOOK_URL

# Value: <your-deploy-hook-url>

#

# 7. Verify Deployment:

# - Check Render logs for startup messages

# - Test health endpoint: https://<your-service>.onrender.com/api/v1/health

#

# Note: With "Auto-Deploy from Image Registry" enabled in Render,

# new images pushed to GHCR will automatically trigger deployments.

# Manual deploy hook call is only needed for forced redeployments.
