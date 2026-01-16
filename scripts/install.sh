#!/bin/bash
# Multi-AI MCP Server Installation Script

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

echo "=================================================="
echo "Multi-AI MCP Server Installation"
echo "=================================================="

# Check Python version
echo ""
echo "Checking Python version..."
PYTHON_VERSION=$(python3 --version 2>&1 | cut -d' ' -f2 | cut -d'.' -f1,2)
if [[ $(echo "$PYTHON_VERSION < 3.10" | bc -l) -eq 1 ]]; then
    echo "Error: Python 3.10+ required. Found: $PYTHON_VERSION"
    exit 1
fi
echo "✓ Python $PYTHON_VERSION"

# Check Node.js
echo ""
echo "Checking Node.js..."
if command -v node &> /dev/null; then
    NODE_VERSION=$(node --version)
    echo "✓ Node.js $NODE_VERSION"
else
    echo "Warning: Node.js not found. Some CLI tools may not work."
fi

# Check CLI tools
echo ""
echo "Checking CLI tools..."

check_cli() {
    local name=$1
    local cmd=$2
    if command -v "$cmd" &> /dev/null; then
        local version=$("$cmd" --version 2>&1 | head -n1)
        echo "✓ $name: $version"
    else
        echo "✗ $name: Not installed"
    fi
}

check_cli "Claude CLI" "claude"
check_cli "Codex CLI" "codex"
check_cli "Gemini CLI" "gemini"
check_cli "Antigravity" "antigravity"

# Install Python dependencies
echo ""
echo "Installing Python dependencies..."
cd "$PROJECT_DIR"

# Check if using shared-mcp-env
if [[ -d "/Users/rush/mcp-servers/shared-mcp-env" ]]; then
    echo "Using shared MCP environment..."
    source /Users/rush/mcp-servers/shared-mcp-env/bin/activate
fi

pip install -e . --quiet

echo "✓ Dependencies installed"

# Create .env if not exists
if [[ ! -f "$PROJECT_DIR/.env" ]]; then
    echo ""
    echo "Creating .env from template..."
    cp "$PROJECT_DIR/.env.example" "$PROJECT_DIR/.env"
    echo "✓ Created .env (please update with your settings)"
fi

# Verify installation
echo ""
echo "Verifying installation..."
python3 -c "from src import mcp, main; print('✓ Module imports successful')"

echo ""
echo "=================================================="
echo "Installation Complete!"
echo "=================================================="
echo ""
echo "To use with Claude Code, add to your .mcp.json:"
echo ""
echo "  \"multi-ai\": {"
echo "    \"command\": \"python\","
echo "    \"args\": [\"$PROJECT_DIR/src/server.py\"]"
echo "  }"
echo ""
echo "Or use the shared MCP environment:"
echo ""
echo "  \"multi-ai\": {"
echo "    \"command\": \"/Users/rush/mcp-servers/shared-mcp-env/bin/python\","
echo "    \"args\": [\"$PROJECT_DIR/src/server.py\"]"
echo "  }"
echo ""
