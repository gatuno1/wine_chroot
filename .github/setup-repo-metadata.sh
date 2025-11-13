#!/bin/bash
# Script to configure GitHub repository metadata
# Run this after authenticating with: gh auth login

set -e

REPO="gatuno1/wine_chroot"
DESCRIPTION="Tools to execute Windows amd64 applications on ARM64 hardware using Wine within a Debian chroot environment"
TOPICS="wine,arm64,debian,chroot,windows-apps,qemu,python,emulation"

echo "Configuring GitHub repository metadata for $REPO"
echo

# Set description
echo "Setting repository description..."
gh repo edit "$REPO" --description "$DESCRIPTION"

# Add topics
echo "Adding topics: $TOPICS"
gh repo edit "$REPO" --add-topic "$TOPICS"

# Show result
echo
echo "Repository metadata configured successfully!"
echo
gh repo view "$REPO"
