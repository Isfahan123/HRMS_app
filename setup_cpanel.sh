#!/bin/bash
# HRMS Web Application - cPanel Setup Script
# This script helps automate the initial setup on cPanel hosting

set -e  # Exit on error

echo "=========================================="
echo "HRMS Web Application - cPanel Setup"
echo "=========================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Function to print colored output
print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_info() {
    echo -e "${NC}ℹ $1${NC}"
}

# Check if we're in the right directory
if [ ! -f "passenger_wsgi.py" ]; then
    print_error "Error: passenger_wsgi.py not found!"
    print_info "Please run this script from the HRMS_app root directory"
    exit 1
fi

print_success "Found HRMS application directory"

# Step 1: Check Python version
echo ""
echo "Step 1: Checking Python version..."
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
print_info "Found Python version: $PYTHON_VERSION"

PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)

# Check if Python version is at least 3.8
if [ "$PYTHON_MAJOR" -lt 3 ]; then
    print_error "Python 3.8 or higher is required!"
    print_info "Current version: $PYTHON_VERSION"
    exit 1
elif [ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 8 ]; then
    print_error "Python 3.8 or higher is required!"
    print_info "Current version: $PYTHON_VERSION (need at least 3.8)"
    exit 1
fi

print_success "Python version is compatible"

# Step 2: Check for virtual environment
echo ""
echo "Step 2: Checking virtual environment..."

# Try to find virtual environment
if [ -n "$VIRTUAL_ENV" ]; then
    print_success "Virtual environment is activated: $VIRTUAL_ENV"
else
    print_warning "Virtual environment not activated"
    print_info "Please activate it first or the script will try to find it"
    
    # Try common cPanel virtual environment locations
    VENV_PATHS=(
        "$HOME/virtualenv/HRMS_app/3.11/bin/activate"
        "$HOME/virtualenv/HRMS_app/3.10/bin/activate"
        "$HOME/virtualenv/HRMS_app/3.9/bin/activate"
        "$HOME/virtualenv/HRMS_app/3.8/bin/activate"
        "./venv/bin/activate"
    )
    
    for venv_path in "${VENV_PATHS[@]}"; do
        if [ -f "$venv_path" ]; then
            print_info "Found virtual environment: $venv_path"
            print_info "To activate it, run: source $venv_path"
            FOUND_VENV=true
            break
        fi
    done
    
    if [ -z "$FOUND_VENV" ]; then
        print_warning "No virtual environment found"
        print_info "You need to create one via cPanel Python App interface"
        read -p "Do you want to continue anyway? (y/n) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
fi

# Step 3: Check if requirements.txt exists
echo ""
echo "Step 3: Checking dependencies..."

if [ ! -f "requirements.txt" ]; then
    print_error "requirements.txt not found!"
    exit 1
fi

print_success "Found requirements.txt"

# Step 4: Install dependencies
echo ""
read -p "Do you want to install/update Python dependencies? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Installing dependencies..."
    pip install --upgrade pip
    pip install -r requirements.txt
    print_success "Dependencies installed"
else
    print_info "Skipping dependency installation"
fi

# Step 5: Check .env file
echo ""
echo "Step 5: Checking environment configuration..."

if [ ! -f ".env" ]; then
    print_warning ".env file not found!"
    
    if [ -f ".env.example" ]; then
        print_info "Found .env.example"
        read -p "Do you want to create .env from .env.example? (y/n) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            cp .env.example .env
            print_success "Created .env file"
            print_warning "IMPORTANT: Edit .env file with your Supabase credentials!"
            print_info "Run: nano .env"
        fi
    else
        print_error ".env.example not found either!"
        print_info "You'll need to create .env manually"
    fi
else
    print_success ".env file exists"
    
    # Check if it has the required variables
    if grep -q "SUPABASE_URL=" .env && grep -q "SUPABASE_KEY=" .env; then
        print_success "Environment variables configured"
    else
        print_warning "Some environment variables may be missing"
        print_info "Please verify your .env file contains:"
        print_info "  - SUPABASE_URL"
        print_info "  - SUPABASE_KEY"
    fi
fi

# Step 6: Check file permissions
echo ""
echo "Step 6: Setting file permissions..."

# Set directory permissions
find . -type d -exec chmod 755 {} \; 2>/dev/null || print_warning "Could not set all directory permissions"

# Set file permissions
find . -type f -exec chmod 644 {} \; 2>/dev/null || print_warning "Could not set all file permissions"

# Make scripts executable
chmod +x start_web.py 2>/dev/null || print_warning "Could not make start_web.py executable"
chmod +x setup_cpanel.sh 2>/dev/null || print_warning "Could not make setup_cpanel.sh executable"

print_success "File permissions set"

# Step 7: Check required files
echo ""
echo "Step 7: Verifying required files..."

REQUIRED_FILES=(
    "passenger_wsgi.py"
    ".htaccess"
    ".cpanel.yml"
    "web_app.py"
    "requirements.txt"
)

ALL_FILES_EXIST=true
for file in "${REQUIRED_FILES[@]}"; do
    if [ -f "$file" ]; then
        print_success "Found: $file"
    else
        print_error "Missing: $file"
        ALL_FILES_EXIST=false
    fi
done

if [ "$ALL_FILES_EXIST" = false ]; then
    print_error "Some required files are missing!"
    exit 1
fi

# Function to test Python imports
test_import() {
    local module=$1
    local description=$2
    if python3 -c "import $module; print('OK')" 2>/dev/null; then
        print_success "$description imports successfully"
        return 0
    else
        print_error "Failed to import $description"
        return 1
    fi
}

# Step 8: Test imports
echo ""
echo "Step 8: Testing application imports..."

if ! test_import "web_app" "FastAPI app"; then
    print_info "Check if all dependencies are installed"
    print_info "Run: pip install -r requirements.txt"
fi

test_import "passenger_wsgi" "WSGI adapter"

# Step 9: Create necessary directories
echo ""
echo "Step 9: Creating necessary directories..."

mkdir -p tmp
mkdir -p log
mkdir -p web/static/css
mkdir -p web/static/js
mkdir -p web/templates

print_success "Directories created"

# Step 10: Final instructions
echo ""
echo "=========================================="
echo "Setup Complete!"
echo "=========================================="
echo ""
print_success "All setup steps completed successfully"
echo ""
echo "Next steps:"
echo "  1. If not done already, configure .env with your credentials:"
echo "     nano .env"
echo ""
echo "  2. Restart the application:"
echo "     touch passenger_wsgi.py"
echo "     # OR via cPanel: Setup Python App → Restart"
echo ""
echo "  3. Visit your domain to test:"
echo "     https://your-domain.com"
echo ""
echo "  4. Check API documentation:"
echo "     https://your-domain.com/docs"
echo ""
echo "  5. Test health endpoint:"
echo "     curl https://your-domain.com/health"
echo ""
echo "For troubleshooting, see: CPANEL_DEPLOYMENT.md"
echo ""
print_info "If you encounter any issues, check the Passenger logs:"
print_info "  cat log/passenger.log"
echo ""
echo "=========================================="
