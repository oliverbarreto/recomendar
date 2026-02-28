#!/bin/bash

# LabCastARR Environment Setup Script (OPTIONAL)
#
# This script creates a symlink from .env to the appropriate environment file.
#
# NOTE: This script is optional. The recommended approach is to use the --env-file flag:
#   docker compose --env-file .env.production -f docker-compose.prod.yml up
#
# This script is provided as a convenience for users who prefer shorter commands:
#   ./scripts/setup-env.sh production
#   docker compose -f docker-compose.prod.yml up
#
# WARNING: Symlinks may not work properly on all systems (especially Windows).

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Get the environment argument (default to development)
ENVIRONMENT="${1:-development}"

# Validate environment
if [[ "$ENVIRONMENT" != "development" && "$ENVIRONMENT" != "production" ]]; then
    print_error "Invalid environment: $ENVIRONMENT"
    echo "Usage: $0 [development|production]"
    exit 1
fi

# Define source and target paths
SOURCE_FILE=".env.$ENVIRONMENT"
TARGET_FILE=".env"

cd "$PROJECT_ROOT"

# Check if source file exists
if [[ ! -f "$SOURCE_FILE" ]]; then
    print_error "Environment file $SOURCE_FILE does not exist!"
    exit 1
fi

# Remove existing .env if it exists (whether symlink or regular file)
if [[ -L "$TARGET_FILE" ]]; then
    print_info "Removing existing .env symlink..."
    rm "$TARGET_FILE"
elif [[ -f "$TARGET_FILE" ]]; then
    print_warn "Found regular .env file (not a symlink). Backing up to .env.backup..."
    mv "$TARGET_FILE" "${TARGET_FILE}.backup"
fi

# Create symlink
print_info "Creating symlink: .env → $SOURCE_FILE"
ln -s "$SOURCE_FILE" "$TARGET_FILE"

# Verify symlink
if [[ -L "$TARGET_FILE" ]]; then
    print_info "✓ Environment setup complete!"
    print_info "  Active environment: $ENVIRONMENT"
    print_info "  .env → $SOURCE_FILE"

    # Show key variables for verification
    echo ""
    print_info "Key configuration variables:"
    echo "  ENVIRONMENT=$(grep '^ENVIRONMENT=' "$SOURCE_FILE" | cut -d'=' -f2)"
    echo "  NEXT_PUBLIC_API_URL=$(grep '^NEXT_PUBLIC_API_URL=' "$SOURCE_FILE" | cut -d'=' -f2)"
    echo "  BASE_URL=$(grep '^BASE_URL=' "$SOURCE_FILE" | cut -d'=' -f2)"
else
    print_error "Failed to create symlink!"
    exit 1
fi
