#!/bin/bash
# Build Lambda deployment packages

set -e

echo "Building Lambda deployment packages..."

# Check if running from lambda directory
if [ ! -f "webhook_handler.py" ]; then
    echo "Error: Must run from lambda directory"
    exit 1
fi

# Clean previous builds
rm -rf package webhook_handler.zip audio_processor.zip

# Build webhook handler
echo ""
echo "Building webhook_handler.zip..."
mkdir -p package
pip install boto3 requests -t package/ --quiet
cp webhook_handler.py package/
cd package
zip -r ../webhook_handler.zip . > /dev/null
cd ..
rm -rf package
echo "✓ webhook_handler.zip created"

# Build audio processor
echo ""
echo "Building audio_processor.zip..."
mkdir -p package
pip install boto3 requests -t package/ --quiet
cp audio_processor.py package/
cd package
zip -r ../audio_processor.zip . > /dev/null
cd ..
rm -rf package
echo "✓ audio_processor.zip created"

echo ""
echo "Done! Lambda packages are ready for deployment."
echo ""
echo "Next steps:"
echo "  cd .."
echo "  terraform init"
echo "  terraform apply"
