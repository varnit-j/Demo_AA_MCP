#!/bin/bash

# Development script for Flight-booking with Stripe integration
# This script runs Django development server and Stripe webhook tunnel

set -e

echo "🚀 Starting Flight-booking development environment..."

# Check if .env file exists
if [ ! -f .env ]; then
    echo "⚠️  .env file not found. Please copy .env.example to .env and configure your settings."
    exit 1
fi

# Load environment variables
export $(cat .env | grep -v '^#' | xargs)

# Check if Stripe CLI is installed
if ! command -v stripe &> /dev/null; then
    echo "⚠️  Stripe CLI not found. Please install it from https://stripe.com/docs/stripe-cli"
    echo "   You can still run Django without webhook forwarding."
    STRIPE_CLI_AVAILABLE=false
else
    STRIPE_CLI_AVAILABLE=true
fi

# Function to cleanup background processes
cleanup() {
    echo "🛑 Stopping development servers..."
    jobs -p | xargs -r kill
    exit 0
}

# Set trap to cleanup on script exit
trap cleanup SIGINT SIGTERM

# Start Django development server
echo "🌐 Starting Django development server on http://127.0.0.1:8000"
python manage.py runserver 127.0.0.1:8000 &
DJANGO_PID=$!

# Start Stripe webhook forwarding if CLI is available
if [ "$STRIPE_CLI_AVAILABLE" = true ]; then
    echo "💳 Starting Stripe webhook forwarding..."
    echo "   Webhooks will be forwarded to http://127.0.0.1:8000/payments/webhook"
    stripe listen --forward-to 127.0.0.1:8000/payments/webhook &
    STRIPE_PID=$!
    
    echo ""
    echo "✅ Development environment ready!"
    echo "   Django: http://127.0.0.1:8000"
    echo "   Stripe webhooks: forwarding to /payments/webhook"
    echo ""
    echo "💡 Tips:"
    echo "   - Test payments with Stripe test cards: https://stripe.com/docs/testing"
    echo "   - Monitor webhook events in Stripe Dashboard"
    echo "   - Use 'stripe trigger payment_intent.succeeded' to test webhooks"
else
    echo ""
    echo "✅ Django development server ready!"
    echo "   Django: http://127.0.0.1:8000"
    echo "   ⚠️  Stripe webhook forwarding unavailable (Stripe CLI not installed)"
fi

echo ""
echo "Press Ctrl+C to stop all services"

# Wait for background processes
wait