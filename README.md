# pet-sitting-booking-service

Booking microservice for the pet-sitting platform. Manages bookings,
status history and time slots. Publishes `BookingCompleted` /
`BookingCancelled` events to Azure Service Bus.

## Stack
- FastAPI + Uvicorn
- SQLAlchemy + pyodbc (Azure SQL Database)
- Pydantic v2
- Azure Service Bus (publisher)
- Logging via stdlib `logging`

## Local run

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8003
```

OpenAPI: <http://localhost:8003/docs>

## Configuration

`.env` (committed for the student project):

```
DB_USERNAME=pasinozavr
DB_PASSWORD=61YcGTqd
DB_SERVER=tcp:cloud2026.database.windows.net
DB_DATABASE=pr2
ODBC_DRIVER=ODBC Driver 17 for SQL Server

SERVICE_BUS_QUEUE_NAME=vladislavstepanenko
SERVICE_BUS_SEND_CONNECTION_STRING=Endpoint=sb://...
LOG_LEVEL=INFO
```

## Endpoints
- `GET /health`
- `POST /init-db` — create `booking` schema and tables
- `POST /seed` — insert stub data
- `GET /bookings`, `GET /bookings/{id}`, `POST /bookings`
- `POST /bookings/{id}/status` — change status, publishes Service Bus event on `completed` / `cancelled`
- `GET /booking-status-history`

## Tests

```bash
pip install pytest flake8
flake8 app tests --max-line-length=120
pytest tests -v
```

## CI

`.github/workflows/ci.yml` runs `flake8` (static analysis) and `pytest`
(unit tests) on every push and pull request.

## Docker

```bash
docker build -t booking-service .
docker run --rm -p 8003:8000 --env-file .env booking-service
```
