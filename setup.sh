#!/bin/bash

# ElderCare System - Quick Setup Script
# This script automates the initial setup of the ElderCare monitoring system

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Functions
print_header() {
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

check_command() {
    if command -v $1 &> /dev/null; then
        print_success "$1 is installed"
        return 0
    else
        print_error "$1 is NOT installed"
        return 1
    fi
}

# Main Script
print_header "ElderCare System - Initial Setup"

# Check prerequisites
print_header "Checking Prerequisites"

MISSING_TOOLS=()

if ! check_command docker; then
    MISSING_TOOLS+=("docker")
fi

if ! check_command docker-compose; then
    MISSING_TOOLS+=("docker-compose")
fi

if ! check_command git; then
    MISSING_TOOLS+=("git")
fi

if ! check_command python3; then
    MISSING_TOOLS+=("python3")
fi

if ! check_command node; then
    MISSING_TOOLS+=("node")
fi

if ! check_command npm; then
    MISSING_TOOLS+=("npm")
fi

if [ ${#MISSING_TOOLS[@]} -gt 0 ]; then
    print_error "The following tools are missing: ${MISSING_TOOLS[*]}"
    echo "Please install them before continuing."
    exit 1
fi

print_success "All prerequisites are installed!"

# Check if in project directory
if [ ! -f "docker-compose.yml" ]; then
    print_error "docker-compose.yml not found!"
    print_warning "Please run this script from the project root directory"
    exit 1
fi

# Environment setup
print_header "Setting Up Environment"

if [ ! -f ".env" ]; then
    if [ -f ".env.example" ]; then
        cp .env.example .env
        print_success "Created .env from .env.example"
        print_warning "IMPORTANT: Edit .env with your credentials"
        print_warning "Required variables:"
        echo "  - SUPABASE_URL"
        echo "  - SUPABASE_KEY"
        echo "  - OPENAI_API_KEY"
        echo "  - WHATSAPP_API_TOKEN"
        echo "  - JWT_SECRET"
        
        read -p "Press Enter once you've edited .env... "
    else
        print_error "Neither .env nor .env.example found"
        exit 1
    fi
else
    print_success ".env already exists"
fi

# Build Docker images
print_header "Building Docker Images"

print_warning "This may take several minutes..."

if docker-compose build; then
    print_success "Docker images built successfully"
else
    print_error "Failed to build Docker images"
    exit 1
fi

# Start containers
print_header "Starting Containers"

if docker-compose up -d; then
    print_success "Containers started successfully"
    sleep 5
else
    print_error "Failed to start containers"
    exit 1
fi

# Check container status
print_header "Container Status"

docker-compose ps

# Wait for services to be ready
print_header "Waiting for Services to Be Ready"

echo "Checking API health..."
RETRY_COUNT=0
MAX_RETRIES=30

while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    if curl -s http://localhost:8000/health > /dev/null; then
        print_success "Backend API is ready!"
        break
    fi
    
    RETRY_COUNT=$((RETRY_COUNT + 1))
    echo "Attempt $RETRY_COUNT/$MAX_RETRIES... waiting for backend..."
    sleep 2
done

if [ $RETRY_COUNT -eq $MAX_RETRIES ]; then
    print_warning "Backend is taking longer than expected to start"
    echo "Check logs with: docker-compose logs backend"
else
    sleep 3
fi

# Verify services
print_header "Service Verification"

echo "Backend API: http://localhost:8000"
if curl -s http://localhost:8000/health | grep -q "\"status\":\"healthy\""; then
    print_success "Backend API is healthy"
else
    print_warning "Could not verify backend health"
fi

echo "API Documentation: http://localhost:8000/docs"
echo "Frontend: http://localhost:3000"
echo "Database: Configured in .env"

# Run initial tests
print_header "Running Initial Tests"

read -p "Do you want to run tests now? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    docker-compose exec -T backend pytest tests/ -v --tb=short || true
else
    print_warning "Skipped tests. Run manually with: docker-compose exec backend pytest"
fi

# Summary
print_header "Setup Complete! ✓"

echo ""
echo "Next steps:"
echo "1. Access the API: http://localhost:8000"
echo "2. View API docs: http://localhost:8000/docs"
echo "3. Access frontend: http://localhost:3000"
echo "4. Check logs: docker-compose logs -f"
echo "5. Run tests: docker-compose exec backend pytest"
echo "6. Stop services: docker-compose down"
echo ""
echo "For detailed documentation, see:"
echo "- README.md - Project overview"
echo "- docs/DEPLOYMENT.md - Deployment guide"
echo "- docs/API.md - API reference"
echo "- README.md - Start here"
echo ""

print_success "System is running and ready for development!"
