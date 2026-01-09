#!/bin/bash
# Tahlil One - Local Development Startup Script

echo "🚀 Starting Tahlil One locally..."

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install backend dependencies
echo "📦 Installing backend dependencies..."
cd backend
pip install -r requirements.txt

# Start backend server
echo "🔧 Starting backend server on http://localhost:8000..."
uvicorn server:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!

cd ..

# Install frontend dependencies
echo "📦 Installing frontend dependencies..."
cd frontend
yarn install

# Start frontend server
echo "🎨 Starting frontend server on http://localhost:3000..."
yarn start &
FRONTEND_PID=$!

cd ..

echo ""
echo "✅ Tahlil One is running!"
echo ""
echo "📍 Frontend: http://localhost:3000"
echo "📍 Backend:  http://localhost:8000"
echo "📍 API Docs: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop both servers"

# Wait for both processes
trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null" EXIT
wait
