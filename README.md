<div align="center">

# 🧠 FlyMind

### AI-Powered Flight Analytics & Automation Suite

[![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)](https://streamlit.io)
[![n8n](https://img.shields.io/badge/n8n-FF6D5A?style=for-the-badge&logo=n8n&logoColor=white)](https://n8n.io)
[![Docker](https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white)](https://docker.com)

*🚀 Intelligent Flight Search • 🤖 AI Automation • ⚡ Real-Time Analytics*

[📖 API Docs](http://localhost:8001/docs) • [🎨 Live Demo](http://localhost:8501) • [🐳 Docker Hub](https://hub.docker.com)

</div>

---

## 🌍 Overview

**FlyMind** is an intelligent flight data platform that combines AI-driven search, real-time Google Flights scraping, price analytics, and automation tools for developers, travelers, and enterprises.

With **FastAPI**, **Streamlit**, and **Playwright**, FlyMind delivers the performance of an API with the interactivity of a dashboard — perfect for n8n workflows, AI chatbots, and real-time travel data pipelines.

### ✨ Key Features

<div align="center">

| 🌍 Global Coverage | ⚡ Real-time Data | 🤖 AI Integration | 💰 Price Alerts |
|:------------------:|:----------------:|:-----------------:|:---------------:|
| Search flights worldwide with intelligent city name recognition | Live Google Flights data with instant results | Perfect for n8n workflows and automation | Monitor fares and get notified of deals |

</div>

### 🎯 Perfect For

- **🤖 n8n Workflows** - HTTP Request nodes with optimized JSON responses
- **💬 Chatbots** - Natural language flight queries and booking
- **🔄 Automation** - Scheduled searches and price monitoring
- **🏢 Enterprise** - Multi-tenant APIs with comprehensive logging
- **🧪 Testing** - Professional Streamlit interface for API testing

---

## 🚀 Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/AbdirahmanNomad/flymind.git
cd flymind

# Install dependencies
pip install -r api/requirements.txt

# Install Playwright browsers
playwright install chromium
```

### Start the Services

```bash
# Terminal 1: Start the API server
cd api
uvicorn api:app --host 0.0.0.0 --port 8001 --reload

# Terminal 2: Start the Streamlit interface
streamlit run streamlit_app.py
```

### 🎉 You're Ready!

- **🌐 API Server**: http://localhost:8001
- **🎨 Streamlit App**: http://localhost:8501
- **📖 API Docs**: http://localhost:8001/docs

---

## 📚 API Reference

### Flight Search

```http
POST /search
Content-Type: application/json

{
  "origin": "New York",
  "destination": "London",
  "depart_date": "2025-12-25",
  "return_date": "2025-12-30",
  "adults": 1,
  "seat_class": "economy",
  "fetch_mode": "local"
}
```

**✨ Smart Features:**
- **City Name Support**: "New York" → JFK, "London" → LHR
- **Flexible Dates**: "weekend", "+3 days", "december"
- **Multi-city Ready**: Support for complex itineraries
- **Real-time Pricing**: Live Google Flights data

### Response Format

```json
{
  "success": true,
  "total_flights": 25,
  "flights": [
    {
      "name": "British Airways",
      "departure": "8:00 AM on Wed, Dec 25",
      "arrival": "11:30 AM on Wed, Dec 25",
      "duration": "7 hr 30 min",
      "stops": 0,
      "price": "SEK 8,450",
      "delay": null
    }
  ],
  "search_url": "https://www.google.com/travel/flights?...",
  "timestamp": "2025-11-03T20:13:02"
}
```

### Webhook Integration

```http
POST /webhooks
Content-Type: application/json

{
  "webhook_url": "https://your-n8n-webhook-url"
}
```

### AI-Powered Natural Language Search

```http
POST /ai/search
Content-Type: application/json

{
  "query": "Find me the cheapest flight from Paris to Tokyo next weekend",
  "api_key": "sk-your-openai-key" // optional, can set OPENAI_API_KEY env var
}
```

**✨ AI Features:**
- **Natural Language Processing**: Parse complex flight queries
- **Intelligent Parameter Extraction**: Origin, destination, dates, preferences
- **Smart Defaults**: Fills in missing parameters automatically
- **Real-time Search**: Executes actual flight search after parsing

**Example Queries:**
- "Find cheap flights from Paris to Tokyo next weekend"
- "Show me round-trip flights to London in December"
- "Find business class flights from NYC to LA for next month"

### Price Alerts (Enhanced)

```http
POST /alerts
Content-Type: application/json

{
  "trip_type": "round-trip",
  "origin": "New York",
  "destination": "London",
  "depart_date": "2025-12-25",
  "return_date": "2025-12-30",
  "target_price": 5000.0,
  "currency": "SEK",
  "email": "user@example.com",
  "notification_channels": ["email", "webhook"]
}
```

**✨ Enhanced Features:**
- **Trip Types**: `one-way`, `round-trip`, `multi-city`
- **Multi-Currency**: `SEK`, `USD`, `EUR`, `GBP`
- **Flexible Dates**: Return date for round-trip alerts
- **Notification Channels**: Email and webhook support

---

## 🎨 Streamlit Interface

The professional Streamlit interface provides:

- **🔍 Advanced Search**: City names, flexible dates, multiple options
- **📊 Real-time Metrics**: Flight counts, price averages, statistics
- **💰 Smart Pricing**: Color-coded price indicators
- **🔗 Direct Links**: One-click access to Google Flights
- **⚙️ API Health**: Real-time connection monitoring
- **📋 Alert Management**: Create and monitor price alerts

### Screenshots

<div align="center">

**Main Interface**
```
┌─────────────────────────────────────────────────┐
│  🧠 FlyMind                                     │
│  AI-Powered Flight Analytics & Automation Suite│
│                                                 │
│  🌍 Global Coverage    ⚡ Real-time Data        │
│  🤖 AI Integration    💰 Price Alerts          │
│                                                 │
│  From: [New York_________] To: [London________] │
│  Date: [📅 Dec 25, 2025] Class: [Economy ▼]     │
│                                                 │
│              [🔍 Search Flights]                │
│                                                 │
│  ✅ Found 25 flights!                           │
│                                                 │
│  📊 Total: 25    Average: SEK 8,450   Lowest:  │
│      SEK 6,200                                   │
└─────────────────────────────────────────────────┘
```

</div>

---

## 🔧 n8n Integration

### HTTP Request Node Setup

1. **Add HTTP Request Node** to your n8n workflow
2. **Method**: POST
3. **URL**: `http://localhost:8001/search`
4. **Body Content Type**: JSON
5. **Body**:
```json
{
  "origin": "{{ $json.origin }}",
  "destination": "{{ $json.destination }}",
  "depart_date": "{{ $json.depart_date }}",
  "adults": "{{ $json.adults || 1 }}",
  "seat_class": "economy"
}
```

### Example Workflow

```
Webhook → HTTP Request → Function → Email/Slack
    ↓           ↓           ↓         ↓
Trigger   Search API   Process    Notify
          Flights     Results
```

---

## 🐳 Docker Deployment

### Quick Start

```bash
# Build and run
docker build -t flymind-api api/
docker run -p 8001:8001 flymind-api

# Or use docker-compose
docker-compose -f api/docker-compose.yml up
```

### Production Deployment

```yaml
version: '3.8'
services:
  api:
    build: ./api
    ports:
      - "8001:8001"
    environment:
      - ENVIRONMENT=production
    restart: unless-stopped
```

---

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Streamlit     │    │     FastAPI     │    │   Google        │
│   Interface     │◄──►│     Server      │◄──►│   Flights       │
│                 │    │                 │    │                 │
│ • User Forms    │    │ • REST API      │    │ • Real-time     │
│ • Results       │    │ • Webhooks      │    │ • Data          │
│ • Analytics     │    │ • Validation    │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │
                              ▼
                       ┌─────────────────┐
                       │   Playwright    │
                       │   Browser       │
                       │   Automation    │
                       └─────────────────┘
```

### Core Components

- **🎨 Streamlit App**: Professional testing interface
- **🚀 FastAPI Server**: High-performance REST API
- **🌐 Playwright Engine**: Anti-detection browser automation
- **🤖 City Parser**: Intelligent location recognition
- **💰 Price Monitor**: Alert system for fare changes

---

## 🔧 Configuration

### Environment Variables

```bash
# API Configuration
PORT=8001
ENVIRONMENT=development
APP_NAME=FlyMind

# Browser Automation
PLAYWRIGHT_BROWSERS_PATH=/opt/playwright

# Optional: CAPTCHA Solving
CAPTCHA_API_KEY=your_2captcha_key

# Optional: Redis for caching
REDIS_URL=redis://localhost:6379

# Optional: AI API Keys
OPENAI_API_KEY=sk-your-openai-key
GOOGLE_AI_API_KEY=your-google-ai-key
DEEPSEEK_API_KEY=sk-your-deepseek-key
```

### Module Imports

If any files import from the old package names, update them:

```python
# Old imports (update these)
from flightstestgoogle import flights
from google-flights-api import search_flights

# New imports
from flymind import flights
from flymind.api import search_flights
```

### Advanced Settings

```python
# Custom browser configuration
BROWSER_CONFIG = {
    "headless": True,
    "viewport": {"width": 1920, "height": 1080},
    "user_agent": "Mozilla/5.0...",
    "locale": "en-US"
}
```

---

## 🧪 Testing & Quality

### Run Tests

```bash
# API tests
cd api && python -m pytest tests/ -v

# Integration tests
python -m pytest tests/test_integration.py

# Load testing
locust -f tests/load_test.py
```

### Code Quality

```bash
# Linting and formatting
black api/ streamlit_app.py
flake8 api/ streamlit_app.py
mypy api/

# Security scanning
bandit -r api/
safety check
```

---

## 📊 Monitoring & Analytics

### Built-in Metrics

- **🔍 Search Analytics**: Popular routes and patterns
- **⚡ Performance**: Response times and success rates
- **💰 Price Tracking**: Historical fare data
- **🌍 Geographic**: Origin/destination insights
- **📈 Usage Stats**: API call volumes and patterns

### Health Endpoints

```bash
# API Health
curl http://localhost:8001/health

# Version Info
curl http://localhost:8001/version

# Metrics (future)
curl http://localhost:8001/metrics
```

---

## 🔒 Security & Compliance

- **✅ Input Validation**: Comprehensive request sanitization
- **✅ CORS Protection**: Configurable origin restrictions
- **✅ Rate Limiting**: Built-in throttling mechanisms
- **✅ Error Handling**: Secure error responses
- **✅ Data Privacy**: No personal data storage

---

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

### Development Setup

```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Install pre-commit hooks
pre-commit install

# Run development server
make dev

# Run tests
make test
```

### Code Standards

- **Python**: PEP 8 with Black formatting
- **API**: RESTful design principles
- **Testing**: 90%+ coverage required
- **Documentation**: All public APIs documented

---

## 📄 License

**MIT License** - Open source and free to use commercially.

```text
Copyright (c) 2025 Abdirahman

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.
```

---

## 🆘 Support & Community

- **📖 Documentation**: [API Docs](http://localhost:8001/docs)
- **🐛 Bug Reports**: [GitHub Issues](https://github.com/AbdirahmanNomad/flymind/issues)
- **💬 Discussions**: [GitHub Discussions](https://github.com/AbdirahmanNomad/flymind/discussions)
- **📧 Email**: Contact via [GitHub Issues](https://github.com/AbdirahmanNomad/flymind/issues)

### Community

- **🌟 Star us** on GitHub if you find this useful!
- **🔗 Share** with fellow developers and automation enthusiasts
- **💝 Contribute** features, bug fixes, or documentation

---

## 🙏 Acknowledgments

**Built with ❤️ using:**

- **[FastAPI](https://fastapi.tiangolo.com/)** - Modern async web framework
- **[Playwright](https://playwright.dev/)** - Cross-browser automation
- **[Streamlit](https://streamlit.io/)** - Data app framework
- **[n8n](https://n8n.io/)** - Workflow automation platform
- **[Google Flights](https://www.google.com/flights)** - Flight data source

**Special thanks to the open-source community!**

---

<div align="center">

## � Ready for Takeoff!

**Start building amazing flight automation workflows today!**

[🎨 Try the Demo](http://localhost:8501) • [📖 Read the Docs](http://localhost:8001/docs) • [🐳 Deploy with Docker](https://hub.docker.com)

---

*Made with ❤️ for developers who love automation*

</div>
