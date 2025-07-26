# HealthUp – Personal Health Tracker

[![Build Status](https://img.shields.io/github/workflow/status/akshaypn/healthup/CI)](https://github.com/akshaypn/healthup/actions)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Docker](https://img.shields.io/badge/docker-ready-blue)](docker-compose.yml)
[![Coverage Status](https://img.shields.io/badge/coverage-83%25-brightgreen)](tests/README.md)

---

> **HealthUp** is a modern, AI-powered personal health tracking platform. Log your weight, meals, and heart rate, and receive actionable insights and coaching from advanced AI models. Built as a PWA for seamless, secure, and cross-device health management.

---

## 🚀 Quick Links

- [Live Demo](#demo)
- [Documentation](docs/README.md)
- [Deployment Guide](docs/EC2_DEPLOYMENT_GUIDE.md)
- [Scripts & Automation](scripts/README.md)
- [Test Suite](tests/README.md)
- [API Reference](#api-endpoints)
- [Contributing](#contributing)
- [Security Policy](#security)
- [FAQ](#faq)

---

## 📚 Table of Contents

- [Project Structure](#-project-structure)
- [Features](#-features)
- [Architecture](#-architecture)
- [Tech Stack](#-tech-stack)
- [Demo](#demo)
- [Installation & Setup](#-installation--setup)
- [Configuration](#-configuration)
- [Deployment](#-deployment)
- [API Endpoints](#api-endpoints)
- [Testing](#testing)
- [Monitoring & Analytics](#-monitoring--analytics)
- [Security](#security)
- [Contributing](#contributing)
- [Support](#support)
- [FAQ](#faq)
- [License](#license)
- [Acknowledgments](#acknowledgments)

---

## 📁 Project Structure

```
healthup/
├── backend/                 # FastAPI backend application
├── frontend/                # React PWA frontend
├── docs/                    # All documentation and guides
│   └── README.md            # Documentation index
├── scripts/                 # Deployment, setup, and utility scripts
│   └── README.md            # Scripts index
├── tests/                   # All test files and test documentation
│   └── README.md            # Test suite documentation
├── docker-compose.yml       # Docker services configuration
├── .env                     # Environment variables (not in git)
├── env.production.example   # Example environment file
└── README.md                # This file
```

- **docs/**: [Documentation, guides, and architecture/feature explanations](docs/README.md)
- **scripts/**: [Deployment, setup, and utility scripts](scripts/README.md)
- **tests/**: [Test files and test documentation](tests/README.md)

---

## 🎯 Features

- **Unified Health HQ**: Log weight, meals, and heart rate
- **AI Insights**: Daily, weekly, and monthly analysis powered by OpenAI/Gemini
- **Real-time Coaching**: Chat with an AI health coach
- **Interactive Charts**: Visualize your health trends
- **Bluetooth HR Integration**: Sync with heart rate devices
- **Progressive Web App**: Installable, offline-capable, mobile-first
- **Secure & Private**: JWT auth, encrypted credentials, rate limiting
- **Production-Ready**: Dockerized, scalable, and CI/CD friendly

---

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
                                  Google Gemini API / OpenAI
```

---

## 🛠️ Tech Stack

**Backend:** FastAPI, SQLAlchemy, PostgreSQL, Redis, Celery, OpenAI/Gemini API, JWT, Alembic

**Frontend:** React 18, TypeScript, Vite, Recharts, React Router, PWA, Google GenAI

**DevOps:** Docker, Docker Compose, AWS EC2, Tailscale, GitHub Actions

---

## 🎬 Demo

> **Try it locally:**
>
> 1. Clone the repo: `git clone https://github.com/akshaypn/healthup.git`
> 2. [Follow the Quick Start](#-installation--setup) below
> 3. Access: [http://localhost:3000](http://localhost:3000)

---

## 📦 Installation & Setup

### Prerequisites
- Docker & Docker Compose
- Node.js 18+ (for development)
- Python 3.11+ (for development)
- OpenAI or Google Gemini API key

### Quick Start (Docker)

```bash
git clone https://github.com/akshaypn/healthup.git
cd healthup
cp env.production.example .env
# Edit .env and add your API keys
./scripts/ec2-production-setup.sh
```

- For full setup, see [docs/DEPLOYMENT_SUMMARY.md](docs/DEPLOYMENT_SUMMARY.md)
- For EC2, see [docs/EC2_DEPLOYMENT_GUIDE.md](docs/EC2_DEPLOYMENT_GUIDE.md)

### Local Development

- [Backend setup](backend/README.md) (see backend folder)
- [Frontend setup](frontend/README.md) (see frontend folder)
- [Test suite](tests/README.md)

---

## 🔧 Configuration

- **Environment variables:** See [env.production.example](env.production.example)
- **Backend config:** `backend/.env` (see [backend/README.md](backend/README.md))
- **Frontend config:** `frontend/.env` (see [frontend/README.md](frontend/README.md))
- **Secrets:** Never commit `.env` files to git

---

## 🚀 Deployment

- **Production:** Use [scripts/ec2-production-setup.sh](scripts/ec2-production-setup.sh) for full EC2 setup, including health checks and auto-testing
- **Docker Compose:** `docker-compose up -d`
- **CI/CD:** See [docs/DEPLOYMENT_SUMMARY.md](docs/DEPLOYMENT_SUMMARY.md)
- **Tailscale VPN:** See [docs/TAILSCALE_DEPLOYMENT_GUIDE.md](docs/TAILSCALE_DEPLOYMENT_GUIDE.md)

---

## 📊 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST   | `/auth/register`      | User registration |
| POST   | `/auth/login`         | User login |
| POST   | `/weight`             | Log weight entry |
| POST   | `/food`               | Log food entry |
| POST   | `/hr`                 | Log heart rate session |
| GET    | `/insight/{period}`   | Get AI insights (daily/weekly/monthly) |
| GET    | `/coach/today`        | Get real-time coaching advice |

- Full OpenAPI docs: [http://localhost:8000/docs](http://localhost:8000/docs)

---

## 🧪 Testing

- **Test suite:** See [tests/README.md](tests/README.md) for all test scripts and instructions
- **Run all tests:**
  ```bash
  cd tests
  python3 test_comprehensive_ai_fixes.py
  # or run shell scripts for integration tests
  ./test-current-setup.sh
  ```
- **Coverage:** 83%+ (see [tests/README.md](tests/README.md))
- **CI:** Automated via GitHub Actions

---

## 📈 Monitoring & Analytics

- **Health checks:** Docker health checks for all services
- **Logging:** Structured logging with correlation IDs
- **Metrics:** Prometheus metrics (see [docs/DEPLOYMENT_SUMMARY.md](docs/DEPLOYMENT_SUMMARY.md))
- **Alerts:** Automated alerting for issues

---

## 🔒 Security

- **JWT Authentication** – Secure token-based auth
- **Password Hashing** – bcrypt for password security
- **CORS Protection** – Configured for production
- **Input Validation** – Pydantic models for data validation
- **Rate Limiting** – API rate limiting protection
- **Prompt Injection Protection** – AI input sanitization
- **Secrets Management** – No secrets in git, use `.env`
- **Responsible Disclosure:** Please report vulnerabilities via GitHub Security tab

---

## 🤝 Contributing

We welcome contributions from the community!

- [Contribution Guide](docs/README.md#contributing)
- [Test Suite](tests/README.md)
- [Code of Conduct](CODE_OF_CONDUCT.md) (if present)

**How to contribute:**
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add/Update tests
5. Submit a pull request

---

## 🆘 Support

- [Open an issue](https://github.com/akshaypn/healthup/issues)
- [API Docs](http://localhost:8000/docs)
- [Troubleshooting](docs/DEPLOYMENT_SUMMARY.md#troubleshooting)
- [Contact Maintainers](mailto:support@healthup.app) (replace with actual email)

---

## ❓ FAQ

**Q: Is HealthUp free to use?**
- Yes, it is open source and free for personal use.

**Q: Can I use my own OpenAI or Gemini API key?**
- Yes, set it in your `.env` file as described above.

**Q: How do I deploy to AWS EC2?**
- See [docs/EC2_DEPLOYMENT_GUIDE.md](docs/EC2_DEPLOYMENT_GUIDE.md) and use [scripts/ec2-production-setup.sh](scripts/ec2-production-setup.sh).

**Q: How do I run all tests?**
- See [tests/README.md](tests/README.md) for instructions.

**Q: Where can I find more documentation?**
- See [docs/README.md](docs/README.md) for a full index.

---

## 📄 License

This project is licensed under the MIT License – see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- [Google Gemini API](https://ai.google.dev/) for AI capabilities
- [OpenAI](https://openai.com/) for LLM integration
- [FastAPI](https://fastapi.tiangolo.com/) for the backend framework
- [React](https://react.dev/) for the frontend
- [The open-source community](https://github.com/akshaypn/healthup/graphs/contributors) for libraries and tools

---

## 🌐 Third-Party Licenses

See [docs/README.md](docs/README.md) for third-party license attributions and details.

---

## 📝 Changelog

See [Releases](https://github.com/akshaypn/healthup/releases) for version history and changelog.

---

## 🏁 Browser & Platform Support

- Chrome, Firefox, Safari, Edge (latest)
- Android, iOS (PWA installable)
- Linux, macOS, Windows (via browser)

---

## Known Issues & Troubleshooting

- See [docs/DEPLOYMENT_SUMMARY.md#troubleshooting](docs/DEPLOYMENT_SUMMARY.md#troubleshooting)
- For open issues, see [GitHub Issues](https://github.com/akshaypn/healthup/issues)

---

## 📢 Community & Updates

- [GitHub Discussions](https://github.com/akshaypn/healthup/discussions)
- [Releases & Announcements](https://github.com/akshaypn/healthup/releases)

---

