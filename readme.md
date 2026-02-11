# 🕵️ Smart Resume Hunter

## 🎯 Project Overview

The main goal of this project is to create a **Fullstack service** for automated job searching and resume analysis. Instead of a simple monolithic script, the system implements a **Microservices Architecture** utilizing **Asynchronous Task Queues** to handle heavy computations (AI Analysis) without blocking the user interface.

It serves as a demonstration of advanced backend skills: **FastAPI**, **Celery**, **RabbitMQ**, **PostgreSQL**, and **Docker orchestration**.

---

## ⚡ Core Architecture: "Non-blocking & Scalable"

- **Asynchronous Task Queue**: Integrates RabbitMQ (Broker) and Celery (Worker) to handle long-running tasks (AI analysis) in the background.

- **Microservices Approach**: The application is split into isolated containers: Web Server, Worker, Frontend, Database, Broker, and Cache.

- **Smart Polling UI**: The Frontend (Streamlit) implements a polling mechanism to check task status in real-time, providing immediate feedback to the user while the backend processes data.

- **Reliable Data Storage**: PostgreSQL with SQLAlchemy (Async) ensures data persistence and relational integrity (Users <-> Resumes <-> Vacancies).

- **Result Caching**: Redis is used as a backend for Celery to store and retrieve analysis results instantly.

---

## ✨ Features

- **REST API**: Complete backend API built with FastAPI (AsyncIO).
- **External API Integration**: Asynchronous parser for HH.ru using httpx.
- **Auth System**: User registration and authentication with password hashing (Bcrypt).
- **Background Processing**: "Fire-and-forget" task dispatching using Celery.
- **Interactive Frontend**: User-friendly interface built with Streamlit.
- **Containerization**: Fully Dockerized environment with docker-compose.
- **AI Simulation Mode**: Currently, the system uses a mock algorithm (simulated delay + randomization) to demonstrate the asynchronous architecture without incurring API costs. The architecture is designed to be easily switched to OpenAI/DeepSeek API by replacing the worker logic.

---

## 🚀 Quick Start / Installation

### Prerequisites

- Docker
- Docker Desktop (running)

### Method: Using Docker (Recommended) 🐳

#### 1. Clone Repository

```bash
git clone https://github.com/yourusername/smart-hunter.git
cd smart-hunter
```

#### 2. Configure Environment

Create a `.env` file in the root directory (passwords can be arbitrary for local docker setup):

```env
DB_USER=postgres
DB_PASS=mysecretpassword
DB_HOST=db
DB_PORT=5432
DB_NAME=smarthunter
```

#### 3. Build and Run

This command builds the images and starts the entire orchestration (Backend, Frontend, DB, Rabbit, Redis, Worker).

```bash
docker-compose up --build
```

#### 4. Access the App

- 🖥️ **Frontend**: Open http://localhost:8501 in your browser.
- ⚙️ **Swagger UI**: Open http://localhost:8000/docs to test the API directly.
- 🐇 **RabbitMQ UI**: Open http://localhost:15672 (login: guest/guest).

---

## 📂 Project Structure

```
smart-hunter/
├── main.py                # FastAPI Application (Producer)
├── frontend.py            # Streamlit UI (Client)
├── tasks.py               # Celery Tasks (Consumer logic)
├── celery_app.py          # Celery Configuration
├── models.py              # SQLAlchemy Database Models
├── schemas.py             # Pydantic Data Schemas
├── hh_client.py           # Async parser for HH.ru
├── docker-compose.yml     # Infrastructure orchestration
├── Dockerfile             # Backend & Worker image
├── Dockerfile.frontend    # Frontend image
├── .env                   # Secrets (Excluded from Git)
└── requirements.txt       # Python dependencies
```

---

## 🐳 Docker Configuration

### Docker Compose Services

```yaml
services:
  backend:       # FastAPI (Port 8000)
  frontend:      # Streamlit (Port 8501)
  db:            # PostgreSQL (Port 5433 -> 5432)
  rabbitmq:      # Message Broker (Port 5672)
  redis:         # Result Store (Port 6379)
  celery_worker: # Background Task Processor
```

### Dockerfile (Backend/Worker)

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

---

## 🔌 API & Async Workflow

### Synchronous Operations (FastAPI)

- `POST /register` & `POST /login` — User management.
- `GET /vacancies` — Search and save vacancies from HH.ru.
- `POST /vacancies/{id}/fill` — Download full description.

### Asynchronous Operations (Celery)

1. `POST /match` — Initiates the analysis.
2. Backend sends a task to RabbitMQ.
3. Returns a `task_id` immediately to the client.
4. Celery Worker picks up the task and processes it (simulating heavy AI load).
5. Result is saved to Redis.
6. `GET /tasks/{task_id}` — Frontend polls this endpoint to check if the result is ready in Redis.

---

## 📊 Data Pipeline

1. **Extract**: User searches for a keyword (e.g., "Python Junior"). System scrapes HH.ru API.
2. **Transform**: Data is cleaned (HTML tags removed), validated via Pydantic, and deduplicated.
3. **Load**: Clean data is stored in PostgreSQL (vacancies table).
4. **Analysis**: Resume and Vacancy texts are sent to the Worker.
5. **Result**: Compatibility score (0-100%) is delivered to the user via polling.

---

## 🔒 Security & Best Practices

- **Environment Variables**: All secrets (DB passwords, Hosts) are managed via `.env`.
- **Docker Isolation**: Services communicate via an internal Docker network; only necessary ports are exposed.
- **Password Hashing**: Passwords are never stored in plain text (managed by passlib).
- **`.dockerignore`**: Prevents leaking of `.env` files or `__pycache__` into the container image.

---

## 🛠 Useful Commands

```bash
# Start all services
docker-compose up --build

# Stop all services
docker-compose down

# ⚠️ Reset Database (Delete all data)
docker-compose down -v

# View logs of the worker (to see background tasks)
docker logs smarthunter_worker
```