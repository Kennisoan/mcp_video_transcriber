#!/bin/bash

# MCP Video Transcriber Health Check Script
# Usage: ./health-check.sh [domain]

DOMAIN=${1:-localhost:8000}
PROTOCOL=${2:-http}

echo "🔍 Checking MCP Video Transcriber health at ${PROTOCOL}://${DOMAIN}"
echo "============================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to check endpoint
check_endpoint() {
    local endpoint=$1
    local expected_status=${2:-200}
    local description=$3
    
    echo -n "📡 ${description}: "
    
    response=$(curl -s -w "%{http_code}" -o /tmp/response "${PROTOCOL}://${DOMAIN}${endpoint}")
    status=$?
    
    if [ $status -eq 0 ] && [ "$response" = "$expected_status" ]; then
        echo -e "${GREEN}✅ OK${NC}"
        return 0
    else
        echo -e "${RED}❌ FAILED (HTTP: $response)${NC}"
        return 1
    fi
}

# Function to check OAuth discovery
check_oauth_discovery() {
    echo -n "🔐 OAuth Discovery: "
    
    response=$(curl -s "${PROTOCOL}://${DOMAIN}/.well-known/oauth-authorization-server")
    
    if echo "$response" | jq -e '.issuer' > /dev/null 2>&1; then
        echo -e "${GREEN}✅ OK${NC}"
        return 0
    else
        echo -e "${RED}❌ FAILED${NC}"
        echo "Response: $response"
        return 1
    fi
}

# Main health checks
echo "🚀 Basic Health Checks"
echo "----------------------"

# Root endpoint
check_endpoint "/" 200 "Root endpoint"

# Health endpoint
check_endpoint "/health" 200 "Health endpoint"

# API docs
check_endpoint "/docs" 200 "API Documentation"

echo ""
echo "🔐 OAuth 2.1 Endpoints"
echo "----------------------"

# OAuth discovery
check_oauth_discovery

# OAuth metadata endpoints
check_endpoint "/.well-known/oauth-authorization-server" 200 "Authorization Server Metadata"
check_endpoint "/.well-known/oauth-protected-resource" 200 "Protected Resource Metadata"

echo ""
echo "📊 Container Status (Docker)"
echo "----------------------------"

if command -v docker &> /dev/null; then
    container_status=$(docker ps --filter "name=mcp-video-transcriber" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}")
    if [ -n "$container_status" ]; then
        echo "$container_status"
    else
        echo -e "${YELLOW}⚠️ Container not found${NC}"
    fi
else
    echo -e "${YELLOW}⚠️ Docker not available${NC}"
fi

echo ""
echo "💾 Database Status"
echo "------------------"

if [ -f "./data/oauth.db" ]; then
    db_size=$(ls -lh ./data/oauth.db | awk '{print $5}')
    echo -e "${GREEN}✅ Database exists (${db_size})${NC}"
    
    # Check database tables
    if command -v sqlite3 &> /dev/null; then
        table_count=$(sqlite3 ./data/oauth.db "SELECT COUNT(*) FROM sqlite_master WHERE type='table';")
        echo -e "${BLUE}📊 Tables: ${table_count}${NC}"
    fi
else
    echo -e "${YELLOW}⚠️ Database not found${NC}"
fi

echo ""
echo "📋 Recent Logs (last 10 lines)"
echo "------------------------------"

if [ -f "./logs/app.log" ]; then
    tail -10 ./logs/app.log
else
    if command -v docker &> /dev/null; then
        docker logs --tail 10 mcp-video-transcriber 2>/dev/null || echo -e "${YELLOW}⚠️ No container logs found${NC}"
    else
        echo -e "${YELLOW}⚠️ No logs found${NC}"
    fi
fi

echo ""
echo "🎯 Summary"
echo "----------"
echo "All checks completed. If any checks failed, review the configuration."
echo "For OAuth to work properly, ensure SERVER_URL matches your domain." 