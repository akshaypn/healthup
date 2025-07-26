# HealthUp - Personal Health Tracker

A comprehensive personal health tracking application with AI-powered insights, built as a Progressive Web App (PWA) with a modern tech stack.

## 🎯 Product Goals

- **One-stop personal health HQ** - Log weight, meals, HR-monitor traces
- **Daily / weekly / monthly insights & charts** - Visualize your health trends
- **LLM-driven coaching** - AI-powered summary, next-steps, and motivation
- **PWA** - Runs offline, zero heavy compute on device
- **Single t3.micro-class backend** - Optimized for AWS Free Tier
- **Google Gemini integration** - Free-tier models via per-user API keys

## 🏗️ Architecture

```
┌───────────┐  HTTPS  ┌────────────┐     AMQP/Redis    ┌───────────┐
│  PWA      │◀──────▶│  REST API  │◀──────────────────▶│  Worker   │
│ (React)   │         │  (FastAPI) │                   │  (Celery) │
└───────────┘         └────────────┘                   └─────┬─────┘
            Service-Worker  ▲  |  SQLAlchemy ORM                │
            Local-cache     │  |                                │
                            │  ▼                                ▼
                         ┌────────────────────────────────────────┐
                         │ PostgreSQL (RDS-Free-Tier)             │
                         └────────────────────────────────────────┘
                                         ▲
                                         │ batched prompts
                                         ▼
                                  Google Gemini API
```

## 🚀 Features

### Core Functionality
- **Weight Tracking** - Log daily weight with trend visualization
- **Food Logging** - Track meals with macro nutrients (calories, protein, fat, carbs)
- **Heart Rate Monitoring** - Bluetooth HR device integration
- **AI Insights** - Daily, weekly, and monthly health analysis
- **Real-time Coaching** - Chat with AI health coach

### Technical Features
- **Progressive Web App** - Installable, offline-capable
- **Responsive Design** - Mobile-first, works on all devices
- **Real-time Charts** - Interactive health data visualization
- **Bluetooth Integration** - Heart rate monitor support
- **Offline Support** - Service worker caching
- **JWT Authentication** - Secure user sessions

## 🛠️ Tech Stack

### Backend
- **FastAPI** - Modern Python web framework
- **SQLAlchemy** - ORM for database operations
- **PostgreSQL** - Primary database
- **Redis** - Caching and Celery broker
- **Celery** - Background task processing
- **Google Gemini API** - AI-powered insights
- **JWT** - Authentication
- **Alembic** - Database migrations

### Frontend
- **React 18** - UI framework
- **TypeScript** - Type safety
- **Vite** - Build tool
- **Recharts** - Data visualization
- **React Router** - Client-side routing
- **PWA** - Progressive Web App features
- **Google GenAI** - Client-side AI integration

## 📦 Installation & Setup

### Prerequisites
- Docker and Docker Compose
- Node.js 18+ (for development)
- Python 3.11+ (for development)
- Google Gemini API key

### Quick Start with Docker

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd healthup
   ```

2. **Set up environment variables**
   ```bash
   cp backend/env.example backend/.env
   cp frontend/env.example frontend/.env
   ```
   
   Edit the files and add your Google Gemini API key:
   ```env
   # backend/.env
   GEMINI_API_KEY=your-gemini-api-key-here
   SECRET_KEY=your-secret-key-here
   
   # frontend/.env
   VITE_GEMINI_API_KEY=your-gemini-api-key-here
   ```

3. **Start the application**
   ```bash
   ./start.sh
   ```

4. **Access the application**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Docs: http://localhost:8000/docs

### 🚀 EC2 Production Deployment

For production deployment on AWS EC2:

1. **Launch EC2 Instance**
   - Ubuntu Server 22.04 LTS
   - t3.medium or larger
   - Security Group: Allow ports 22, 80, 443, 3000, 8000

2. **Deploy Application**
   ```bash
   # Connect to EC2 instance
   ssh -i your-key.pem ubuntu@your-ec2-ip
   
   # Clone and deploy
   git clone https://github.com/your-username/healthup.git
   cd healthup
   chmod +x deploy-ec2.sh
   ./deploy-ec2.sh
   ```

3. **Access Production App**
   - Frontend: `http://your-ec2-public-ip:3000`
   - Backend: `http://your-ec2-public-ip:8000`
   - Mobile: Open the frontend URL on your phone

📖 **Full EC2 Deployment Guide**: See [EC2_DEPLOYMENT_GUIDE.md](EC2_DEPLOYMENT_GUIDE.md)

### Development Setup

1. **Backend Setup**
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   
   # Set up environment variables
   cp env.example .env
   # Edit .env with your settings
   
   # Run the backend
   uvicorn app.main:app --reload
   ```

2. **Frontend Setup**
   ```bash
   cd frontend
   npm install
   
   # Set up environment variables
   cp env.example .env
   # Edit .env with your settings
   
   # Run the frontend
   npm run dev
   ```

3. **Database Setup**
   ```bash
   # Install PostgreSQL and Redis, or use Docker
   docker run -d --name postgres -e POSTGRES_DB=healthup -e POSTGRES_USER=healthup -e POSTGRES_PASSWORD=healthup -p 5432:5432 postgres:15
   docker run -d --name redis -p 6379:6379 redis:7-alpine
   
   # Run migrations
   cd backend
   alembic upgrade head
   ```

## 📊 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/auth/register` | User registration |
| POST | `/auth/login` | User login |
| POST | `/weight` | Log weight entry |
| POST | `/food` | Log food entry |
| POST | `/hr` | Log heart rate session |
| GET | `/insight/{period}` | Get AI insights (daily/weekly/monthly) |
| GET | `/coach/today` | Get real-time coaching advice |

## 🤖 AI Integration

### Google Gemini API Usage

The application uses Google Gemini API for:
- **Daily Insights** - Quick summaries and actionable tips
- **Weekly Reports** - Trend analysis and recommendations
- **Monthly Analysis** - Deep insights and strategic planning
- **Real-time Coaching** - Interactive health advice

### Rate Limiting Strategy
- **Gemini 2.0 Flash** - 15 RPM, 1,500 RPD for quick summaries
- **Token Bucket** - Redis-based rate limiting
- **Exponential Backoff** - Automatic retry with backoff
- **Batching** - Multiple functions in single prompts

## 📱 PWA Features

- **Installable** - Add to home screen
- **Offline Support** - Service worker caching
- **Push Notifications** - Health reminders
- **Background Sync** - Data synchronization
- **Responsive Design** - Works on all devices

## 🔧 Configuration

### Environment Variables

**Backend (.env)**
```env
DATABASE_URL=postgresql://healthup:healthup@localhost/healthup
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=15
REDIS_URL=redis://localhost:6379
GEMINI_API_KEY=your-gemini-api-key-here
ENVIRONMENT=development
```

**Frontend (.env)**
```env
VITE_API_URL=http://localhost:8000
VITE_GEMINI_API_KEY=your-gemini-api-key-here
```

## 🚀 Deployment

### AWS Free Tier Deployment

1. **EC2 Setup**
   ```bash
   # Launch t3.micro instance
   # Install Docker and Docker Compose
   sudo yum update -y
   sudo yum install -y docker
   sudo service docker start
   sudo usermod -a -G docker ec2-user
   sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
   sudo chmod +x /usr/local/bin/docker-compose
   ```

2. **RDS Setup**
   - Create PostgreSQL RDS instance (db.t4g.micro)
   - Update DATABASE_URL in environment

3. **Deploy Application**
   ```bash
   git clone <repository-url>
   cd healthup_temp
   # Set up environment variables
   docker-compose up -d
   ```

### Production Considerations
- Use HTTPS with Let's Encrypt
- Set up proper logging and monitoring
- Configure backup strategies
- Implement rate limiting
- Set up CI/CD pipeline

## 📈 Monitoring & Analytics

- **Health Checks** - Docker health checks for all services
- **Logging** - Structured logging with correlation IDs
- **Metrics** - Prometheus metrics for monitoring
- **Alerts** - Automated alerting for issues

## 🔒 Security

- **JWT Authentication** - Secure token-based auth
- **Password Hashing** - bcrypt for password security
- **CORS Protection** - Configured for production
- **Input Validation** - Pydantic models for data validation
- **Rate Limiting** - API rate limiting protection

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For support and questions:
- Create an issue in the repository
- Check the API documentation at `/docs`
- Review the troubleshooting guide

## 🎉 Acknowledgments

- Google Gemini API for AI capabilities
- FastAPI for the excellent web framework
- React team for the amazing frontend framework
- The open-source community for various libraries and tools


### Gemini AI API Cheatsheet

## Free-tier rate-limit lookup table (Gemini & related models)

| Model (version)                                | Typical sweet-spot use-case                                                     | Max context (tokens)                                             | Free-tier RPM                                                                                                | Free-tier RPD                                               | Free-tier TPM†                          | Notes / standout strengths                                                                                   |
| ---------------------------------------------- | ------------------------------------------------------------------------------- | ---------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------ | ----------------------------------------------------------- | --------------------------------------- | ------------------------------------------------------------------------------------------------------------ |
| **Gemini 2.5 Pro (Code Assist / CLI preview)** | Large-context coding, multi-step reasoning, exploratory chat                    | **1 M** tokens window 🔥 ([indiatimes.com][1], [blog.google][2]) | **60** ([indiatimes.com][1])                                                                                 | **1 000** ([blog.google][2])                                | n/s (not disclosed)                     | Highest free RPM/RPD today; works only via Gemini CLI or Code Assist licence. Great for code & long reports. |
| **Gemini 1.5 Flash (GA)**                      | Real-time chat, rapid summarisation, long-doc Q\&A                              | 1 M tokens                                                       | 15 ([googlecloudcommunity.com][3], [uctoday.com][4])                                                         | 1 500 ([googlecloudcommunity.com][3], [uctoday.com][4])     | 1 M ([uctoday.com][4], [zapier.com][5]) | Cheapest, fastest multimodal model; batch work to exploit high TPM.                                          |
| **Gemini 1.5 Pro (GA)**                        | Precise reasoning, tool-calling, dense coding tasks where Flash is too light    | 1 M tokens                                                       | **2** ([googlecloudcommunity.com][3], [techtarget.com][6])                                                   | **50** ([googlecloudcommunity.com][3], [techtarget.com][6]) | \~32 k ([neuroflash.com][7])            | Excellent quality but severe quotas—use only for “needle-in-haystack” problems.                              |
| **Gemini 1.0 Pro (text / image)**              | Stable baseline for production chatbots & RAG; better availability than 1.5 Pro | 32 k tokens                                                      | 15 (60 RPM in AI Studio) ([zapier.com][5], [reddit.com][8])                                                  | 1 500 (RPD) ([zapier.com][5])                               | 1 M ([zapier.com][5])                   | Good fallback when 1.5-series is over-quota; vision input supported.                                         |
| **Gemini Pro Vision (1.0)**                    | Image + text reasoning (alt-text, diagrams, OCR extraction)                     | 32 k tokens                                                      | 60 RPM (AI Studio only) ([reddit.com][8])                                                                    | n/s (typ. 1 500/day like Pro)                               | n/s                                     | Use in AI Studio for free visual tasks; API key currently text-only.                                         |
| **Text Embedding 004**                         | High-dimensional embeddings for search / clustering                             | 20 k tokens / request; 250 texts                                 | Quota varies by region (Vertex AI) – \~1 000 RPM project-wide ([cloud.google.com][9], [cloud.google.com][9]) | –                                                           | –                                       | Each request can batch 250 texts—use batching to stay inside quotas.                                         |
| **Gemini 2.5 Flash TTS (preview)**             | Budget speech synthesis                                                         | 128 k prompt                                                     | 15 RPM (preview) ([ai.google.dev][10])                                                                       | 500 RPD (shared) ([ai.google.dev][10])                      | –                                       | Audio output free but quota tight; great for small voice prototypes.                                         |

† **TPM = input tokens per minute** that the backend will actually count against your project.

---

## How to choose the right free model

### 1. Prioritise **rate-limit headroom**

* If you expect spiky usage, **Gemini 2.5 Pro via the free Code Assist licence** is the only option that rivals paid-tier headroom (60 RPM / 1 000 RPD). ([indiatimes.com][1], [blog.google][2])
* For always-on bots, **Gemini 1.5 Flash** offers the best sustained quota (15 RPM, 1 500 RPD) while still supporting the full 1 M-token context window. ([googlecloudcommunity.com][3], [uctoday.com][4])

### 2. Match **latency vs quality**

* **Flash** is “good enough” for summarisation, support chat, or rapid multi-modal extraction, and its responses arrive 2-3× faster than Pro. ([uctoday.com][4])
* **Pro (1.5 / 2.5)** shines in complex planning, chain-of-thought, or tricky code bases where Flash may hallucinate. Be prepared to throttle calls aggressively. ([techtarget.com][6])

### 3. Exploit **batching & streaming**

* Free tokens-per-minute allowances are huge (Flash offers 1 M TPM), so bundle multiple tasks into one request instead of separate calls. ([zapier.com][5])
* Stream responses to the client to start processing while the model is still finishing—this keeps perceived latency low without extra quota cost.

### 4. Use **AI Studio** for vision & prototyping

* AI Studio ignores some API-key limits (e.g., 60 RPM for Pro Vision) and costs nothing; build your prototype there, then migrate to API once flow stabilises. ([reddit.com][8])

### 5. Plan for **inevitable quota hits**

Even with the most generous free limits, you will eventually hit ceilings if your project scales:

* **Caching** common system prompts locally—free tier doesn’t include server-side context caching ([zapier.com][5])
* **Rotate** among multiple Google Cloud projects (within ToS) to sandbox experiments from production usage.
* **Trigger back-off** (exponential retry) rather than blind retries—Google throttles harder after repeated breaches.



## Code examples

# normal inference
```python 

from google import genai
from google.genai import types

client = genai.Client()

response = client.models.generate_content(
    model="gemini-2.5-flash",
    contents=["Explain how AI works"],
    config=types.GenerateContentConfig(
        temperature=0.1
    )
)
print(response.text)

```
#structure output 

```python

from google import genai
from pydantic import BaseModel

class Recipe(BaseModel):
    recipe_name: str
    ingredients: list[str]

client = genai.Client()
response = client.models.generate_content(
    model="gemini-2.5-flash",
    contents="List a few popular cookie recipes, and include the amounts of ingredients.",
    config={
        "response_mime_type": "application/json",
        "response_schema": list[Recipe],
    },
)
# Use the response as a JSON string.
print(response.text)

# Use instantiated objects.
my_recipes: list[Recipe] = response.parsed

```

# Google search grounding

```python
from google import genai
from google.genai import types

# Configure the client
client = genai.Client()

# Define the grounding tool
grounding_tool = types.Tool(
    google_search=types.GoogleSearch()
)

# Configure generation settings
config = types.GenerateContentConfig(
    tools=[grounding_tool]
)

# Make the request
response = client.models.generate_content(
    model="gemini-2.5-flash",
    contents="Who won the euro 2024?",
    config=config,
)

# Print the grounded response
print(response.text)

```

