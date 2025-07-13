#!/bin/bash

# Stock Kafka Pipeline Setup Script
echo "🚀 Setting up Stock Kafka Pipeline..."

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "📝 Creating .env file..."
    cp .env.example .env
    echo "⚠️  Please edit .env file with your Korean Investment Securities API credentials"
fi

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p logs
mkdir -p data/duckdb
mkdir -p data/cache

# Set permissions
chmod +x scripts/setup.sh

# Start Docker services
echo "🐳 Starting Docker services..."
docker-compose up -d

# Wait for services to be ready
echo "⏳ Waiting for services to be ready..."
sleep 30

# Create Kafka topics
echo "📨 Creating Kafka topics..."
docker exec kafka kafka-topics --create --topic nasdaq-tier1-realtime --bootstrap-server localhost:9092 --partitions 3 --replication-factor 1 --if-not-exists
docker exec kafka kafka-topics --create --topic nasdaq-tier2-realtime --bootstrap-server localhost:9092 --partitions 2 --replication-factor 1 --if-not-exists
docker exec kafka kafka-topics --create --topic nasdaq-tier3-realtime --bootstrap-server localhost:9092 --partitions 1 --replication-factor 1 --if-not-exists
docker exec kafka kafka-topics --create --topic trading-signals --bootstrap-server localhost:9092 --partitions 1 --replication-factor 1 --if-not-exists
docker exec kafka kafka-topics --create --topic portfolio-updates --bootstrap-server localhost:9092 --partitions 1 --replication-factor 1 --if-not-exists

# List created topics
echo "✅ Created topics:"
docker exec kafka kafka-topics --list --bootstrap-server localhost:9092

# Install Python dependencies (if not using Docker)
if [ "$1" = "local" ]; then
    echo "🐍 Installing Python dependencies..."
    pip install -r requirements.txt
fi

echo "🎉 Setup completed successfully!"
echo ""
echo "📊 Services available at:"
echo "  - Kafka UI: http://localhost:8080"
echo "  - Streamlit Dashboard: http://localhost:8501 (when running)"
echo ""
echo "🔧 Next steps:"
echo "  1. Edit .env file with your API credentials"
echo "  2. Run 'python src/main.py' to start the pipeline"
echo "  3. Run 'streamlit run src/dashboard/app.py' to start the dashboard"
