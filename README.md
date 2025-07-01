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
