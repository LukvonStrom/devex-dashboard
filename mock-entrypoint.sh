#!/bin/bash
set -e

echo "🔄 Checking MongoDB connection..."
until python -c "import mongoengine; mongoengine.connect(host='${MONGO_URI}', alias='healthcheck')" 2>/dev/null; do
  echo "📡 Waiting for MongoDB to be ready..."
  sleep 2
done

echo "✅ MongoDB is ready!"


echo "📊 Generating mock data..."
python /app/mock_data.py
echo "✅ Mock data generated successfully!"


echo "🚀 Starting Streamlit application..."
exec streamlit run /app/Developer_Experience_Dashboard.py --server.port=8501 --server.address=0.0.0.0