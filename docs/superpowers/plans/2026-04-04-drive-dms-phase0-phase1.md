# DRIVE-DMS Phase 0 + Phase 1: Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Stand up the drive-dms greenfield project with Docker infrastructure, Gateway auth, Workshop service skeleton, and a working Next.js frontend — then build Order management (CRUD + Kanban) as the first real feature.

**Architecture:** Hybrid container architecture with FastAPI microservices behind Traefik. Gateway handles auth (JWT + LDAP) and tenant routing. Workshop service owns all workshop business logic. Next.js React frontend talks to Gateway. PostgreSQL with schema-per-tenant. Redis for cache and pub/sub.

**Tech Stack:** Python 3.12, FastAPI, SQLAlchemy 2.0, Alembic, Pydantic v2, Next.js 14, React 18, TypeScript, Tailwind CSS, Zustand, React Query, PostgreSQL 16, Redis 7, Docker Compose, Traefik, Pytest, Ruff

**Spec:** `docs/superpowers/specs/2026-04-04-drive-dms-werkstatt-design.md`

---

## File Map

### New Repository: `drive-dms/`

**Root:**
- `docker-compose.yml` — Dev environment (all services, DB, Redis, Traefik)
- `docker-compose.prod.yml` — Production overrides
- `.env.example` — Environment variable template
- `.gitignore` — Python, Node, Docker ignores
- `README.md` — Project overview + quickstart
- `Makefile` — Common commands (up, down, test, migrate, logs)

**Gateway Service (`services/gateway/`):**
- `Dockerfile` — Multi-stage Python image
- `requirements.txt` — FastAPI, uvicorn, PyJWT, ldap3, redis, httpx
- `app/__init__.py` — Package init
- `app/main.py` — FastAPI app, CORS, lifespan, route mounting
- `app/config.py` — Settings via pydantic-settings (env vars)
- `app/auth/__init__.py` — Package init
- `app/auth/jwt_handler.py` — JWT create/verify, token models
- `app/auth/ldap_auth.py` — LDAP bind + user info lookup
- `app/auth/routes.py` — POST /login, POST /refresh, GET /me
- `app/auth/dependencies.py` — `get_current_user` FastAPI dependency
- `app/auth/models.py` — Pydantic: LoginRequest, TokenResponse, UserInfo
- `app/tenant/__init__.py` — Package init
- `app/tenant/middleware.py` — Extract tenant from header/subdomain, set search_path
- `app/tenant/registry.py` — Tenant lookup + config from shared schema
- `app/proxy/__init__.py` — Package init
- `app/proxy/routes.py` — Reverse proxy to workshop service
- `tests/__init__.py` — Package init
- `tests/conftest.py` — Pytest fixtures (test client, mock DB)
- `tests/test_jwt.py` — JWT create/verify tests
- `tests/test_auth_routes.py` — Login/refresh/me endpoint tests
- `tests/test_tenant.py` — Tenant middleware tests

**Workshop Service (`services/workshop/`):**
- `Dockerfile` — Multi-stage Python image
- `requirements.txt` — FastAPI, SQLAlchemy, alembic, pydantic, redis
- `alembic.ini` — Alembic config pointing to migrations/
- `app/__init__.py` — Package init
- `app/main.py` — FastAPI app, lifespan, route mounting
- `app/config.py` — Settings via pydantic-settings
- `app/database.py` — SQLAlchemy engine, session factory, tenant schema routing
- `app/models/__init__.py` — Import all models for Alembic
- `app/models/base.py` — DeclarativeBase, common mixins (UUID pk, timestamps)
- `app/models/resource.py` — Resource model (MECHANIC, LIFT)
- `app/models/order.py` — WorkshopOrder model
- `app/models/position.py` — Position model
- `app/models/enums.py` — All enums (OrderStatus, PositionType, ResourceType, etc.)
- `app/schemas/__init__.py` — Package init
- `app/schemas/resource.py` — Resource Pydantic schemas (create, update, response)
- `app/schemas/order.py` — Order Pydantic schemas
- `app/schemas/position.py` — Position Pydantic schemas
- `app/schemas/common.py` — Pagination, error responses
- `app/api/__init__.py` — Package init
- `app/api/resources.py` — Resource CRUD endpoints
- `app/api/orders.py` — Order CRUD + status transitions
- `app/api/positions.py` — Position CRUD (nested under orders)
- `app/services/__init__.py` — Package init
- `app/services/order_service.py` — Order business logic (status machine, validation)
- `app/services/resource_service.py` — Resource business logic
- `app/dependencies.py` — get_db session dependency, get_tenant_id
- `migrations/env.py` — Alembic env with tenant-aware schema
- `migrations/versions/` — Auto-generated migration files
- `tests/__init__.py` — Package init
- `tests/conftest.py` — Pytest fixtures (test DB, session, client)
- `tests/test_models.py` — Model creation + constraint tests
- `tests/test_order_service.py` — Order business logic tests
- `tests/test_orders_api.py` — Order endpoint integration tests
- `tests/test_resources_api.py` — Resource endpoint tests
- `tests/test_positions_api.py` — Position endpoint tests

**Frontend (`frontend/`):**
- `Dockerfile` — Multi-stage Node image
- `package.json` — Dependencies
- `tsconfig.json` — TypeScript config
- `tailwind.config.ts` — Tailwind config with custom theme
- `next.config.ts` — Next.js config (API proxy to gateway)
- `.env.local.example` — Frontend env vars
- `src/app/layout.tsx` — Root layout (providers, fonts)
- `src/app/page.tsx` — Redirect to /dashboard or /login
- `src/app/login/page.tsx` — Login page
- `src/app/(authenticated)/layout.tsx` — Authenticated layout (sidebar + header)
- `src/app/(authenticated)/dashboard/page.tsx` — Dashboard (placeholder)
- `src/app/(authenticated)/orders/page.tsx` — Order list page
- `src/app/(authenticated)/orders/new/page.tsx` — Create order form
- `src/app/(authenticated)/orders/[id]/page.tsx` — Order detail page
- `src/app/(authenticated)/orders/kanban/page.tsx` — Kanban board
- `src/app/(authenticated)/resources/page.tsx` — Resource management
- `src/components/shared/sidebar.tsx` — Navigation sidebar
- `src/components/shared/header.tsx` — Top header with user info
- `src/components/shared/data-table.tsx` — Reusable sortable/filterable table
- `src/components/shared/status-badge.tsx` — Order/position status badge
- `src/components/shared/loading.tsx` — Loading spinner/skeleton
- `src/components/orders/order-card.tsx` — Order card for Kanban
- `src/components/orders/order-form.tsx` — Create/edit order form
- `src/components/orders/position-list.tsx` — Position list within order detail
- `src/components/orders/kanban-board.tsx` — Kanban board component
- `src/lib/api-client.ts` — Fetch wrapper with JWT, base URL, error handling
- `src/lib/auth.ts` — Auth helpers (login, logout, token storage, refresh)
- `src/hooks/use-auth.ts` — Auth hook (current user, login/logout)
- `src/hooks/use-orders.ts` — React Query hooks for orders API
- `src/hooks/use-resources.ts` — React Query hooks for resources API
- `src/stores/auth-store.ts` — Zustand auth store (user, token, tenant)
- `src/types/order.ts` — TypeScript types for orders, positions
- `src/types/resource.ts` — TypeScript types for resources
- `src/types/auth.ts` — TypeScript types for auth (user, token, login)

**Database (`database/`):**
- `init/01-init.sql` — Create tenant registry schema, greiner tenant, greiner schema
- `seeds/dev-seeds.sql` — Test data: resources, sample orders

**Infrastructure:**
- `.github/workflows/ci.yml` — Lint + test on push
- `.github/workflows/deploy-dev.yml` — Deploy to Hetzner on develop push

---

## PHASE 0: FUNDAMENT

---

### Task 1: Repository + Docker Compose

**Files:**
- Create: `drive-dms/.gitignore`
- Create: `drive-dms/.env.example`
- Create: `drive-dms/docker-compose.yml`
- Create: `drive-dms/Makefile`

- [ ] **Step 1: Create repository and .gitignore**

```bash
mkdir -p /opt/drive-dms
cd /opt/drive-dms
git init
```

Write `/opt/drive-dms/.gitignore`:

```gitignore
# Python
__pycache__/
*.py[cod]
*.egg-info/
.eggs/
dist/
build/
.venv/
venv/

# Node
node_modules/
.next/
out/

# Environment
.env
.env.local
.env.production

# IDE
.vscode/
.idea/

# Docker
docker-compose.override.yml

# OS
.DS_Store
Thumbs.db

# Test
.coverage
htmlcov/
.pytest_cache/
```

- [ ] **Step 2: Create .env.example**

Write `/opt/drive-dms/.env.example`:

```env
# Database
POSTGRES_USER=dms_user
POSTGRES_PASSWORD=DmsDevPassword2026
POSTGRES_DB=drive_dms
DATABASE_URL=postgresql+asyncpg://dms_user:DmsDevPassword2026@db:5432/drive_dms

# Redis
REDIS_URL=redis://redis:6379/0

# Auth
JWT_SECRET=change-me-in-production-use-openssl-rand-hex-32
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=480

# LDAP (Greiner AD)
LDAP_SERVER=ldaps://10.80.80.5:636
LDAP_BASE_DN=DC=greiner,DC=local
LDAP_BIND_DN=CN=svc-portal,OU=ServiceAccounts,DC=greiner,DC=local
LDAP_BIND_PASSWORD=change-me
LDAP_USE_SSL=true

# Tenant
DEFAULT_TENANT=greiner

# Services
GATEWAY_PORT=8000
WORKSHOP_PORT=8001
FRONTEND_PORT=3000

# DRIVE Bridge (read-only access to existing DRIVE PostgreSQL)
DRIVE_DB_HOST=10.80.80.20
DRIVE_DB_PORT=5432
DRIVE_DB_NAME=drive_portal
DRIVE_DB_USER=drive_user
DRIVE_DB_PASSWORD=DrivePortal2024
```

- [ ] **Step 3: Create docker-compose.yml**

Write `/opt/drive-dms/docker-compose.yml`:

```yaml
services:
  traefik:
    image: traefik:v3.1
    command:
      - "--api.insecure=true"
      - "--providers.docker=true"
      - "--providers.docker.exposedbydefault=false"
      - "--entrypoints.web.address=:80"
    ports:
      - "80:80"
      - "8080:8080"  # Traefik dashboard (dev only)
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock:ro
    networks:
      - dms

  db:
    image: postgres:16-alpine
    environment:
      POSTGRES_USER: ${POSTGRES_USER:-dms_user}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-DmsDevPassword2026}
      POSTGRES_DB: ${POSTGRES_DB:-drive_dms}
    ports:
      - "5433:5432"  # 5433 to avoid conflict with host PostgreSQL
    volumes:
      - pgdata:/var/lib/postgresql/data
      - ./database/init:/docker-entrypoint-initdb.d
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER:-dms_user}"]
      interval: 5s
      timeout: 3s
      retries: 5
    networks:
      - dms

  redis:
    image: redis:7-alpine
    ports:
      - "6380:6379"  # 6380 to avoid conflict with host Redis
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 3s
      retries: 5
    networks:
      - dms

  gateway:
    build:
      context: ./services/gateway
      dockerfile: Dockerfile
    env_file: .env
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.gateway.rule=PathPrefix(`/api`)"
      - "traefik.http.routers.gateway.entrypoints=web"
      - "traefik.http.services.gateway.loadbalancer.server.port=8000"
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_healthy
    volumes:
      - ./services/gateway/app:/app/app  # Hot reload
    networks:
      - dms

  workshop:
    build:
      context: ./services/workshop
      dockerfile: Dockerfile
    env_file: .env
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_healthy
    volumes:
      - ./services/workshop/app:/app/app  # Hot reload
    networks:
      - dms

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.frontend.rule=PathPrefix(`/`)"
      - "traefik.http.routers.frontend.entrypoints=web"
      - "traefik.http.routers.frontend.priority=1"
      - "traefik.http.services.frontend.loadbalancer.server.port=3000"
    volumes:
      - ./frontend/src:/app/src  # Hot reload
    networks:
      - dms

volumes:
  pgdata:

networks:
  dms:
    driver: bridge
```

- [ ] **Step 4: Create Makefile**

Write `/opt/drive-dms/Makefile`:

```makefile
.PHONY: up down build logs test migrate seed shell-gateway shell-workshop

up:
	docker compose up -d

down:
	docker compose down

build:
	docker compose build

logs:
	docker compose logs -f

logs-gateway:
	docker compose logs -f gateway

logs-workshop:
	docker compose logs -f workshop

logs-frontend:
	docker compose logs -f frontend

test-gateway:
	docker compose exec gateway pytest tests/ -v

test-workshop:
	docker compose exec workshop pytest tests/ -v

test: test-gateway test-workshop

migrate:
	docker compose exec workshop alembic upgrade head

seed:
	docker compose exec db psql -U $${POSTGRES_USER:-dms_user} -d $${POSTGRES_DB:-drive_dms} -f /docker-entrypoint-initdb.d/01-init.sql

shell-gateway:
	docker compose exec gateway bash

shell-workshop:
	docker compose exec workshop bash

shell-db:
	docker compose exec db psql -U $${POSTGRES_USER:-dms_user} -d $${POSTGRES_DB:-drive_dms}

clean:
	docker compose down -v
```

- [ ] **Step 5: Create database init script**

Create directory and write `/opt/drive-dms/database/init/01-init.sql`:

```sql
-- Shared schema for tenant registry
CREATE SCHEMA IF NOT EXISTS shared;

CREATE TABLE IF NOT EXISTS shared.tenants (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    slug VARCHAR(63) NOT NULL UNIQUE,  -- used as schema name
    name VARCHAR(255) NOT NULL,
    active BOOLEAN NOT NULL DEFAULT true,
    config JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Insert Greiner as first tenant
INSERT INTO shared.tenants (slug, name, config) VALUES (
    'greiner',
    'Autohaus Greiner',
    '{
        "locations": [
            {"id": "deg-opel", "name": "Deggendorf Opel"},
            {"id": "deg-hyundai", "name": "Deggendorf Hyundai"},
            {"id": "landau", "name": "Landau"}
        ],
        "ldap": {
            "enabled": true,
            "server": "ldaps://10.80.80.5:636"
        }
    }'
) ON CONFLICT (slug) DO NOTHING;

-- Create greiner tenant schema
CREATE SCHEMA IF NOT EXISTS greiner;
```

- [ ] **Step 6: Commit**

```bash
cd /opt/drive-dms
cp .env.example .env
git add .
git commit -m "chore: initialize drive-dms repo with Docker Compose, PostgreSQL, Redis, Traefik"
```

---

### Task 2: Gateway Service — Project Structure + Health Check

**Files:**
- Create: `services/gateway/Dockerfile`
- Create: `services/gateway/requirements.txt`
- Create: `services/gateway/app/__init__.py`
- Create: `services/gateway/app/config.py`
- Create: `services/gateway/app/main.py`
- Create: `services/gateway/tests/__init__.py`
- Create: `services/gateway/tests/conftest.py`
- Create: `services/gateway/tests/test_health.py`

- [ ] **Step 1: Write the health check test**

Write `services/gateway/tests/__init__.py` (empty file).

Write `services/gateway/tests/conftest.py`:

```python
import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c
```

Write `services/gateway/tests/test_health.py`:

```python
import pytest


@pytest.mark.anyio
async def test_health_returns_ok(client):
    resp = await client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert data["service"] == "gateway"
```

- [ ] **Step 2: Write requirements.txt**

Write `services/gateway/requirements.txt`:

```
fastapi==0.115.0
uvicorn[standard]==0.30.0
pydantic-settings==2.5.0
PyJWT==2.9.0
ldap3==2.9.1
redis==5.1.0
httpx==0.27.0
python-multipart==0.0.9

# Dev/Test
pytest==8.3.0
anyio==4.5.0
pytest-anyio==0.0.0
ruff==0.6.0
```

- [ ] **Step 3: Write config and main app**

Write `services/gateway/app/__init__.py` (empty file).

Write `services/gateway/app/config.py`:

```python
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Database
    database_url: str = "postgresql+asyncpg://dms_user:DmsDevPassword2026@db:5432/drive_dms"

    # Redis
    redis_url: str = "redis://redis:6379/0"

    # JWT
    jwt_secret: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 480

    # LDAP
    ldap_server: str = "ldaps://10.80.80.5:636"
    ldap_base_dn: str = "DC=greiner,DC=local"
    ldap_bind_dn: str = ""
    ldap_bind_password: str = ""
    ldap_use_ssl: bool = True

    # Tenant
    default_tenant: str = "greiner"

    # Services
    workshop_url: str = "http://workshop:8001"

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
```

Write `services/gateway/app/main.py`:

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="DRIVE DMS Gateway", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health():
    return {"status": "ok", "service": "gateway"}
```

- [ ] **Step 4: Write Dockerfile**

Write `services/gateway/Dockerfile`:

```dockerfile
FROM python:3.12-slim AS base

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
```

- [ ] **Step 5: Run test to verify it passes**

```bash
cd /opt/drive-dms/services/gateway
pip install -r requirements.txt
pytest tests/test_health.py -v
```

Expected: PASS — `test_health_returns_ok` passes.

- [ ] **Step 6: Commit**

```bash
cd /opt/drive-dms
git add services/gateway/
git commit -m "feat(gateway): FastAPI gateway service with health endpoint"
```

---

### Task 3: Gateway Service — JWT Authentication

**Files:**
- Create: `services/gateway/app/auth/__init__.py`
- Create: `services/gateway/app/auth/models.py`
- Create: `services/gateway/app/auth/jwt_handler.py`
- Create: `services/gateway/app/auth/dependencies.py`
- Create: `services/gateway/tests/test_jwt.py`

- [ ] **Step 1: Write JWT tests**

Write `services/gateway/tests/test_jwt.py`:

```python
import pytest
from datetime import timedelta

from app.auth.jwt_handler import create_access_token, verify_token
from app.auth.models import UserInfo


def _sample_user() -> UserInfo:
    return UserInfo(
        username="mueller",
        tenant="greiner",
        location="deg-opel",
        roles=["mechanic"],
        permissions=["workshop.view", "workshop.clock"],
        display_name="Max Mueller",
    )


def test_create_and_verify_token():
    user = _sample_user()
    token = create_access_token(user)
    assert isinstance(token, str)
    assert len(token) > 50

    decoded = verify_token(token)
    assert decoded.username == "mueller"
    assert decoded.tenant == "greiner"
    assert decoded.location == "deg-opel"
    assert "mechanic" in decoded.roles
    assert "workshop.view" in decoded.permissions


def test_expired_token_raises():
    user = _sample_user()
    token = create_access_token(user, expires_delta=timedelta(seconds=-1))
    with pytest.raises(ValueError, match="Token expired"):
        verify_token(token)


def test_invalid_token_raises():
    with pytest.raises(ValueError, match="Invalid token"):
        verify_token("not-a-real-token")
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd /opt/drive-dms/services/gateway
pytest tests/test_jwt.py -v
```

Expected: FAIL — `ModuleNotFoundError: No module named 'app.auth'`

- [ ] **Step 3: Implement auth models**

Write `services/gateway/app/auth/__init__.py` (empty file).

Write `services/gateway/app/auth/models.py`:

```python
from pydantic import BaseModel


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class UserInfo(BaseModel):
    username: str
    tenant: str
    location: str
    roles: list[str]
    permissions: list[str]
    display_name: str = ""
```

- [ ] **Step 4: Implement JWT handler**

Write `services/gateway/app/auth/jwt_handler.py`:

```python
from datetime import datetime, timedelta, timezone

import jwt

from app.config import settings
from app.auth.models import UserInfo


def create_access_token(
    user: UserInfo,
    expires_delta: timedelta | None = None,
) -> str:
    if expires_delta is None:
        expires_delta = timedelta(minutes=settings.jwt_expire_minutes)

    now = datetime.now(timezone.utc)
    payload = {
        "sub": user.username,
        "tenant": user.tenant,
        "location": user.location,
        "roles": user.roles,
        "permissions": user.permissions,
        "display_name": user.display_name,
        "iat": now,
        "exp": now + expires_delta,
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def verify_token(token: str) -> UserInfo:
    try:
        payload = jwt.decode(
            token, settings.jwt_secret, algorithms=[settings.jwt_algorithm]
        )
    except jwt.ExpiredSignatureError:
        raise ValueError("Token expired")
    except jwt.InvalidTokenError:
        raise ValueError("Invalid token")

    return UserInfo(
        username=payload["sub"],
        tenant=payload["tenant"],
        location=payload["location"],
        roles=payload["roles"],
        permissions=payload["permissions"],
        display_name=payload.get("display_name", ""),
    )
```

- [ ] **Step 5: Implement auth dependency**

Write `services/gateway/app/auth/dependencies.py`:

```python
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.auth.jwt_handler import verify_token
from app.auth.models import UserInfo

security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> UserInfo:
    try:
        return verify_token(credentials.credentials)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )


def require_role(*roles: str):
    async def checker(user: UserInfo = Depends(get_current_user)) -> UserInfo:
        if not any(r in user.roles for r in roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Requires one of roles: {roles}",
            )
        return user

    return checker
```

- [ ] **Step 6: Run tests**

```bash
cd /opt/drive-dms/services/gateway
pytest tests/test_jwt.py -v
```

Expected: All 3 tests PASS.

- [ ] **Step 7: Commit**

```bash
cd /opt/drive-dms
git add services/gateway/app/auth/ services/gateway/tests/test_jwt.py
git commit -m "feat(gateway): JWT authentication — create, verify, dependencies"
```

---

### Task 4: Gateway Service — Auth Routes (Login + Me)

**Files:**
- Create: `services/gateway/app/auth/ldap_auth.py`
- Create: `services/gateway/app/auth/routes.py`
- Create: `services/gateway/tests/test_auth_routes.py`
- Modify: `services/gateway/app/main.py` — mount auth router

- [ ] **Step 1: Write auth route tests**

Write `services/gateway/tests/test_auth_routes.py`:

```python
import pytest
from unittest.mock import patch, MagicMock

from app.auth.models import UserInfo


@pytest.mark.anyio
async def test_login_with_valid_credentials(client):
    mock_user = UserInfo(
        username="mueller",
        tenant="greiner",
        location="deg-opel",
        roles=["mechanic"],
        permissions=["workshop.view", "workshop.clock"],
        display_name="Max Mueller",
    )

    with patch("app.auth.routes.authenticate_user", return_value=mock_user):
        resp = await client.post(
            "/api/v1/auth/login",
            json={"username": "mueller", "password": "test123"},
        )

    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.anyio
async def test_login_with_invalid_credentials(client):
    with patch("app.auth.routes.authenticate_user", return_value=None):
        resp = await client.post(
            "/api/v1/auth/login",
            json={"username": "invalid", "password": "wrong"},
        )

    assert resp.status_code == 401
    assert "Invalid credentials" in resp.json()["detail"]


@pytest.mark.anyio
async def test_me_with_valid_token(client):
    mock_user = UserInfo(
        username="mueller",
        tenant="greiner",
        location="deg-opel",
        roles=["mechanic"],
        permissions=["workshop.view", "workshop.clock"],
        display_name="Max Mueller",
    )

    with patch("app.auth.routes.authenticate_user", return_value=mock_user):
        login_resp = await client.post(
            "/api/v1/auth/login",
            json={"username": "mueller", "password": "test123"},
        )
    token = login_resp.json()["access_token"]

    resp = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert resp.status_code == 200
    data = resp.json()
    assert data["username"] == "mueller"
    assert data["tenant"] == "greiner"


@pytest.mark.anyio
async def test_me_without_token(client):
    resp = await client.get("/api/v1/auth/me")
    assert resp.status_code == 403
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_auth_routes.py -v
```

Expected: FAIL — routes not registered yet.

- [ ] **Step 3: Implement LDAP auth (with dev bypass)**

Write `services/gateway/app/auth/ldap_auth.py`:

```python
import logging

from ldap3 import Server, Connection, ALL, SUBTREE
from ldap3.core.exceptions import LDAPException

from app.config import settings
from app.auth.models import UserInfo

logger = logging.getLogger(__name__)

# Role mapping: AD OU -> DMS roles + permissions
OU_ROLE_MAP = {
    "Werkstatt": {
        "roles": ["mechanic"],
        "permissions": ["workshop.view", "workshop.clock"],
    },
    "Serviceberatung": {
        "roles": ["service_advisor"],
        "permissions": [
            "workshop.view",
            "workshop.edit",
            "workshop.clock",
            "workshop.checkin",
            "planner.view",
        ],
    },
    "Werkstattleitung": {
        "roles": ["workshop_lead"],
        "permissions": [
            "workshop.view",
            "workshop.edit",
            "workshop.clock",
            "workshop.checkin",
            "planner.view",
            "planner.edit",
            "reports.view",
        ],
    },
    "Geschaeftsleitung": {
        "roles": ["tenant_admin"],
        "permissions": ["*"],
    },
}

# Dev-mode users (when LDAP is unavailable)
DEV_USERS = {
    "dev-admin": UserInfo(
        username="dev-admin",
        tenant="greiner",
        location="deg-opel",
        roles=["tenant_admin"],
        permissions=["*"],
        display_name="Dev Admin",
    ),
    "dev-mechanic": UserInfo(
        username="dev-mechanic",
        tenant="greiner",
        location="deg-opel",
        roles=["mechanic"],
        permissions=["workshop.view", "workshop.clock"],
        display_name="Dev Mechaniker",
    ),
    "dev-advisor": UserInfo(
        username="dev-advisor",
        tenant="greiner",
        location="deg-opel",
        roles=["service_advisor"],
        permissions=[
            "workshop.view",
            "workshop.edit",
            "workshop.clock",
            "workshop.checkin",
            "planner.view",
        ],
        display_name="Dev Serviceberater",
    ),
}


def authenticate_user(username: str, password: str) -> UserInfo | None:
    # Dev mode: accept dev-* users with any password
    if username.startswith("dev-") and username in DEV_USERS:
        return DEV_USERS[username]

    # LDAP authentication
    if not settings.ldap_bind_dn:
        logger.warning("LDAP not configured, only dev users available")
        return None

    try:
        return _ldap_authenticate(username, password)
    except LDAPException as e:
        logger.error(f"LDAP error for user {username}: {e}")
        return None


def _ldap_authenticate(username: str, password: str) -> UserInfo | None:
    server = Server(settings.ldap_server, get_info=ALL, use_ssl=settings.ldap_use_ssl)

    # First bind with service account to find user
    conn = Connection(server, settings.ldap_bind_dn, settings.ldap_bind_password)
    if not conn.bind():
        logger.error("LDAP service account bind failed")
        return None

    # Search for user
    conn.search(
        settings.ldap_base_dn,
        f"(sAMAccountName={username})",
        search_scope=SUBTREE,
        attributes=["cn", "memberOf", "distinguishedName", "department"],
    )

    if not conn.entries:
        conn.unbind()
        return None

    user_entry = conn.entries[0]
    user_dn = str(user_entry.distinguishedName)
    display_name = str(user_entry.cn)
    conn.unbind()

    # Verify user's own password
    user_conn = Connection(server, user_dn, password)
    if not user_conn.bind():
        return None
    user_conn.unbind()

    # Map OU to roles
    roles, permissions = _map_ou_to_roles(user_dn)

    return UserInfo(
        username=username,
        tenant="greiner",  # Hardcoded for Phase 1, configurable later
        location="deg-opel",  # TODO: derive from AD department
        roles=roles,
        permissions=permissions,
        display_name=display_name,
    )


def _map_ou_to_roles(dn: str) -> tuple[list[str], list[str]]:
    for ou_name, mapping in OU_ROLE_MAP.items():
        if f"OU={ou_name}" in dn:
            return mapping["roles"], mapping["permissions"]

    # Default: read-only access
    return ["viewer"], ["workshop.view"]
```

- [ ] **Step 4: Implement auth routes**

Write `services/gateway/app/auth/routes.py`:

```python
from fastapi import APIRouter, Depends, HTTPException, status

from app.auth.ldap_auth import authenticate_user
from app.auth.jwt_handler import create_access_token
from app.auth.dependencies import get_current_user
from app.auth.models import LoginRequest, TokenResponse, UserInfo
from app.config import settings

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
async def login(request: LoginRequest):
    user = authenticate_user(request.username, request.password)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )

    token = create_access_token(user)
    return TokenResponse(
        access_token=token,
        expires_in=settings.jwt_expire_minutes * 60,
    )


@router.get("/me", response_model=UserInfo)
async def me(user: UserInfo = Depends(get_current_user)):
    return user
```

- [ ] **Step 5: Mount auth router in main.py**

Replace `services/gateway/app/main.py`:

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.auth.routes import router as auth_router

app = FastAPI(title="DRIVE DMS Gateway", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)


@app.get("/health")
async def health():
    return {"status": "ok", "service": "gateway"}
```

- [ ] **Step 6: Run all gateway tests**

```bash
cd /opt/drive-dms/services/gateway
pytest tests/ -v
```

Expected: All tests PASS (health + JWT + auth routes).

- [ ] **Step 7: Commit**

```bash
cd /opt/drive-dms
git add services/gateway/
git commit -m "feat(gateway): login + /me endpoints with LDAP auth and dev-mode bypass"
```

---

### Task 5: Gateway Service — Tenant Middleware + Workshop Proxy

**Files:**
- Create: `services/gateway/app/tenant/__init__.py`
- Create: `services/gateway/app/tenant/middleware.py`
- Create: `services/gateway/app/proxy/__init__.py`
- Create: `services/gateway/app/proxy/routes.py`
- Modify: `services/gateway/app/main.py` — add middleware + proxy
- Create: `services/gateway/tests/test_tenant.py`

- [ ] **Step 1: Write tenant middleware test**

Write `services/gateway/tests/test_tenant.py`:

```python
import pytest
from unittest.mock import patch

from app.auth.jwt_handler import create_access_token
from app.auth.models import UserInfo


def _token_for(tenant: str = "greiner") -> str:
    user = UserInfo(
        username="test",
        tenant=tenant,
        location="deg-opel",
        roles=["tenant_admin"],
        permissions=["*"],
        display_name="Test User",
    )
    return create_access_token(user)


@pytest.mark.anyio
async def test_tenant_header_set_from_jwt(client):
    token = _token_for("greiner")
    resp = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    assert resp.json()["tenant"] == "greiner"
```

- [ ] **Step 2: Implement tenant middleware**

Write `services/gateway/app/tenant/__init__.py` (empty file).

Write `services/gateway/app/tenant/middleware.py`:

```python
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request


class TenantMiddleware(BaseHTTPMiddleware):
    """Extract tenant from JWT and inject into request state."""

    async def dispatch(self, request: Request, call_next):
        # Tenant is extracted from JWT in auth dependency.
        # This middleware adds a X-Tenant-ID header for downstream services.
        # For now it's a pass-through; tenant is always in the JWT.
        response = await call_next(request)
        return response
```

- [ ] **Step 3: Implement proxy routes to workshop service**

Write `services/gateway/app/proxy/__init__.py` (empty file).

Write `services/gateway/app/proxy/routes.py`:

```python
from fastapi import APIRouter, Depends, Request, Response
import httpx

from app.auth.dependencies import get_current_user
from app.auth.models import UserInfo
from app.config import settings

router = APIRouter(prefix="/api/v1/workshop", tags=["workshop-proxy"])

_http_client: httpx.AsyncClient | None = None


def _get_client() -> httpx.AsyncClient:
    global _http_client
    if _http_client is None:
        _http_client = httpx.AsyncClient(base_url=settings.workshop_url, timeout=30.0)
    return _http_client


@router.api_route(
    "/{path:path}",
    methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
)
async def proxy_to_workshop(
    path: str,
    request: Request,
    user: UserInfo = Depends(get_current_user),
):
    client = _get_client()

    # Forward request with tenant + user info in headers
    headers = {
        "X-Tenant-ID": user.tenant,
        "X-User-ID": user.username,
        "X-User-Roles": ",".join(user.roles),
        "X-User-Permissions": ",".join(user.permissions),
        "X-Location-ID": user.location,
    }

    body = await request.body()

    resp = await client.request(
        method=request.method,
        url=f"/{path}",
        headers=headers,
        params=dict(request.query_params),
        content=body if body else None,
    )

    return Response(
        content=resp.content,
        status_code=resp.status_code,
        headers=dict(resp.headers),
    )
```

- [ ] **Step 4: Update main.py with middleware + proxy**

Replace `services/gateway/app/main.py`:

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.auth.routes import router as auth_router
from app.proxy.routes import router as proxy_router
from app.tenant.middleware import TenantMiddleware

app = FastAPI(title="DRIVE DMS Gateway", version="0.1.0")

app.add_middleware(TenantMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(proxy_router)


@app.get("/health")
async def health():
    return {"status": "ok", "service": "gateway"}
```

- [ ] **Step 5: Run all gateway tests**

```bash
cd /opt/drive-dms/services/gateway
pytest tests/ -v
```

Expected: All tests PASS.

- [ ] **Step 6: Commit**

```bash
cd /opt/drive-dms
git add services/gateway/
git commit -m "feat(gateway): tenant middleware + reverse proxy to workshop service"
```

---

### Task 6: Workshop Service — Project Structure + Database

**Files:**
- Create: `services/workshop/Dockerfile`
- Create: `services/workshop/requirements.txt`
- Create: `services/workshop/app/__init__.py`
- Create: `services/workshop/app/config.py`
- Create: `services/workshop/app/main.py`
- Create: `services/workshop/app/database.py`
- Create: `services/workshop/app/dependencies.py`
- Create: `services/workshop/app/models/__init__.py`
- Create: `services/workshop/app/models/base.py`
- Create: `services/workshop/app/models/enums.py`
- Create: `services/workshop/tests/__init__.py`
- Create: `services/workshop/tests/conftest.py`
- Create: `services/workshop/tests/test_health.py`

- [ ] **Step 1: Write health check test**

Write `services/workshop/tests/__init__.py` (empty file).

Write `services/workshop/tests/conftest.py`:

```python
import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from app.main import app
from app.database import Base
from app.dependencies import get_db

# Use SQLite for tests (in-memory)
TEST_DATABASE_URL = "sqlite+aiosqlite:///./test.db"

engine = create_async_engine(TEST_DATABASE_URL, echo=False)
TestSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


@pytest.fixture(autouse=True)
async def setup_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
async def db_session():
    async with TestSessionLocal() as session:
        yield session


@pytest.fixture
async def client(db_session):
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c

    app.dependency_overrides.clear()
```

Write `services/workshop/tests/test_health.py`:

```python
import pytest


@pytest.mark.anyio
async def test_health_returns_ok(client):
    resp = await client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert data["service"] == "workshop"
```

- [ ] **Step 2: Write requirements.txt and Dockerfile**

Write `services/workshop/requirements.txt`:

```
fastapi==0.115.0
uvicorn[standard]==0.30.0
pydantic-settings==2.5.0
sqlalchemy[asyncio]==2.0.35
asyncpg==0.29.0
alembic==1.13.0
redis==5.1.0

# Dev/Test
pytest==8.3.0
anyio==4.5.0
pytest-anyio==0.0.0
aiosqlite==0.20.0
ruff==0.6.0
```

Write `services/workshop/Dockerfile`:

```dockerfile
FROM python:3.12-slim AS base

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001", "--reload"]
```

- [ ] **Step 3: Write config, database, and dependencies**

Write `services/workshop/app/__init__.py` (empty file).

Write `services/workshop/app/config.py`:

```python
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://dms_user:DmsDevPassword2026@db:5432/drive_dms"
    redis_url: str = "redis://redis:6379/0"

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
```

Write `services/workshop/app/database.py`:

```python
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase

from app.config import settings

engine = create_async_engine(settings.database_url, echo=False)

SessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class Base(DeclarativeBase):
    pass
```

Write `services/workshop/app/dependencies.py`:

```python
from collections.abc import AsyncGenerator
from fastapi import Header, HTTPException

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.database import SessionLocal


async def get_db(
    x_tenant_id: str = Header(default="greiner"),
) -> AsyncGenerator[AsyncSession, None]:
    async with SessionLocal() as session:
        # Set search_path to tenant schema
        await session.execute(text(f"SET search_path TO {x_tenant_id}, shared, public"))
        yield session


async def get_tenant_id(x_tenant_id: str = Header(default="greiner")) -> str:
    return x_tenant_id


async def get_user_id(x_user_id: str = Header(default="system")) -> str:
    return x_user_id
```

- [ ] **Step 4: Write model base and enums**

Write `services/workshop/app/models/__init__.py`:

```python
from app.models.base import TimestampMixin  # noqa: F401
from app.models.enums import OrderStatus, PositionType, PositionStatus, ResourceType, CheckinType  # noqa: F401
```

Write `services/workshop/app/models/base.py`:

```python
import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, func
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID as PG_UUID


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


def new_uuid() -> uuid.UUID:
    return uuid.uuid4()
```

Write `services/workshop/app/models/enums.py`:

```python
import enum


class OrderStatus(str, enum.Enum):
    APPOINTMENT = "appointment"
    PREPARED = "prepared"
    DISPATCHED = "dispatched"
    CHECKED_IN = "checked_in"
    IN_PROGRESS = "in_progress"
    QA = "qa"
    COMPLETED = "completed"
    PICKED_UP = "picked_up"


class PositionType(str, enum.Enum):
    LABOR = "labor"
    PARTS = "parts"
    SUBLET = "sublet"


class PositionStatus(str, enum.Enum):
    PLANNED = "planned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


class ResourceType(str, enum.Enum):
    MECHANIC = "mechanic"
    LIFT = "lift"


class CheckinType(str, enum.Enum):
    SERVICE_ADVISOR = "service_advisor"
    SELF_SERVICE = "self_service"
```

- [ ] **Step 5: Write main.py**

Write `services/workshop/app/main.py`:

```python
from fastapi import FastAPI

app = FastAPI(title="DRIVE DMS Workshop Service", version="0.1.0")


@app.get("/health")
async def health():
    return {"status": "ok", "service": "workshop"}
```

- [ ] **Step 6: Run test**

```bash
cd /opt/drive-dms/services/workshop
pip install -r requirements.txt
pytest tests/test_health.py -v
```

Expected: PASS.

- [ ] **Step 7: Commit**

```bash
cd /opt/drive-dms
git add services/workshop/
git commit -m "feat(workshop): service skeleton with database, models base, enums"
```

---

### Task 7: Workshop Service — Resource Model + CRUD API

**Files:**
- Create: `services/workshop/app/models/resource.py`
- Create: `services/workshop/app/schemas/__init__.py`
- Create: `services/workshop/app/schemas/common.py`
- Create: `services/workshop/app/schemas/resource.py`
- Create: `services/workshop/app/api/__init__.py`
- Create: `services/workshop/app/api/resources.py`
- Modify: `services/workshop/app/models/__init__.py` — add Resource import
- Modify: `services/workshop/app/main.py` — mount resources router
- Create: `services/workshop/tests/test_resources_api.py`

- [ ] **Step 1: Write resource API tests**

Write `services/workshop/tests/test_resources_api.py`:

```python
import pytest


MECHANIC_DATA = {
    "name": "Max Mueller",
    "type": "mechanic",
    "location_id": "deg-opel",
    "qualifications": ["HV-Schein", "Klima"],
    "working_hours": {"mon": "07:00-16:00", "tue": "07:00-16:00", "wed": "07:00-16:00", "thu": "07:00-16:00", "fri": "07:00-14:00"},
    "color": "#3B82F6",
}

LIFT_DATA = {
    "name": "Buehne 1",
    "type": "lift",
    "location_id": "deg-opel",
    "qualifications": [],
    "working_hours": {"mon": "06:00-20:00", "tue": "06:00-20:00", "wed": "06:00-20:00", "thu": "06:00-20:00", "fri": "06:00-18:00"},
    "color": "#10B981",
}


@pytest.mark.anyio
async def test_create_mechanic(client):
    resp = await client.post("/resources", json=MECHANIC_DATA)
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "Max Mueller"
    assert data["type"] == "mechanic"
    assert "id" in data


@pytest.mark.anyio
async def test_create_lift(client):
    resp = await client.post("/resources", json=LIFT_DATA)
    assert resp.status_code == 201
    assert resp.json()["type"] == "lift"


@pytest.mark.anyio
async def test_list_resources(client):
    await client.post("/resources", json=MECHANIC_DATA)
    await client.post("/resources", json=LIFT_DATA)

    resp = await client.get("/resources")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 2


@pytest.mark.anyio
async def test_list_resources_filter_by_type(client):
    await client.post("/resources", json=MECHANIC_DATA)
    await client.post("/resources", json=LIFT_DATA)

    resp = await client.get("/resources?type=mechanic")
    assert resp.status_code == 200
    assert len(resp.json()) == 1
    assert resp.json()[0]["type"] == "mechanic"


@pytest.mark.anyio
async def test_get_resource_by_id(client):
    create_resp = await client.post("/resources", json=MECHANIC_DATA)
    resource_id = create_resp.json()["id"]

    resp = await client.get(f"/resources/{resource_id}")
    assert resp.status_code == 200
    assert resp.json()["name"] == "Max Mueller"


@pytest.mark.anyio
async def test_update_resource(client):
    create_resp = await client.post("/resources", json=MECHANIC_DATA)
    resource_id = create_resp.json()["id"]

    resp = await client.patch(
        f"/resources/{resource_id}",
        json={"name": "Max Mueller-Schmidt", "qualifications": ["HV-Schein", "Klima", "Getriebe"]},
    )
    assert resp.status_code == 200
    assert resp.json()["name"] == "Max Mueller-Schmidt"
    assert "Getriebe" in resp.json()["qualifications"]


@pytest.mark.anyio
async def test_delete_resource(client):
    create_resp = await client.post("/resources", json=MECHANIC_DATA)
    resource_id = create_resp.json()["id"]

    resp = await client.delete(f"/resources/{resource_id}")
    assert resp.status_code == 204

    resp = await client.get(f"/resources/{resource_id}")
    assert resp.status_code == 404
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd /opt/drive-dms/services/workshop
pytest tests/test_resources_api.py -v
```

Expected: FAIL — no `/resources` route.

- [ ] **Step 3: Implement Resource model**

Write `services/workshop/app/models/resource.py`:

```python
import uuid

from sqlalchemy import String, Boolean, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, JSONB, ARRAY

from app.database import Base
from app.models.base import TimestampMixin, new_uuid
from app.models.enums import ResourceType


class Resource(Base, TimestampMixin):
    __tablename__ = "resources"

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=new_uuid)
    tenant_id: Mapped[str] = mapped_column(String(63), nullable=False, default="greiner")
    type: Mapped[ResourceType] = mapped_column(SAEnum(ResourceType, name="resource_type"), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    qualifications: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    location_id: Mapped[str] = mapped_column(String(63), nullable=False)
    working_hours: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    color: Mapped[str] = mapped_column(String(7), nullable=False, default="#6B7280")
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
```

Update `services/workshop/app/models/__init__.py`:

```python
from app.models.base import TimestampMixin  # noqa: F401
from app.models.enums import OrderStatus, PositionType, PositionStatus, ResourceType, CheckinType  # noqa: F401
from app.models.resource import Resource  # noqa: F401
```

- [ ] **Step 4: Implement Resource schemas**

Write `services/workshop/app/schemas/__init__.py` (empty file).

Write `services/workshop/app/schemas/common.py`:

```python
from pydantic import BaseModel


class ErrorResponse(BaseModel):
    detail: str
```

Write `services/workshop/app/schemas/resource.py`:

```python
import uuid
from datetime import datetime

from pydantic import BaseModel

from app.models.enums import ResourceType


class ResourceCreate(BaseModel):
    name: str
    type: ResourceType
    location_id: str
    qualifications: list[str] = []
    working_hours: dict = {}
    color: str = "#6B7280"


class ResourceUpdate(BaseModel):
    name: str | None = None
    qualifications: list[str] | None = None
    working_hours: dict | None = None
    color: str | None = None
    active: bool | None = None


class ResourceResponse(BaseModel):
    id: uuid.UUID
    name: str
    type: ResourceType
    location_id: str
    qualifications: list[str]
    working_hours: dict
    color: str
    active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
```

- [ ] **Step 5: Implement Resource API endpoints**

Write `services/workshop/app/api/__init__.py` (empty file).

Write `services/workshop/app/api/resources.py`:

```python
import uuid

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db
from app.models.resource import Resource
from app.models.enums import ResourceType
from app.schemas.resource import ResourceCreate, ResourceUpdate, ResourceResponse

router = APIRouter(prefix="/resources", tags=["resources"])


@router.post("", status_code=status.HTTP_201_CREATED, response_model=ResourceResponse)
async def create_resource(
    data: ResourceCreate,
    db: AsyncSession = Depends(get_db),
):
    resource = Resource(
        name=data.name,
        type=data.type,
        location_id=data.location_id,
        qualifications=data.qualifications,
        working_hours=data.working_hours,
        color=data.color,
    )
    db.add(resource)
    await db.commit()
    await db.refresh(resource)
    return resource


@router.get("", response_model=list[ResourceResponse])
async def list_resources(
    type: ResourceType | None = Query(None),
    location_id: str | None = Query(None),
    active: bool = Query(True),
    db: AsyncSession = Depends(get_db),
):
    query = select(Resource).where(Resource.active == active)
    if type:
        query = query.where(Resource.type == type)
    if location_id:
        query = query.where(Resource.location_id == location_id)
    query = query.order_by(Resource.name)

    result = await db.execute(query)
    return result.scalars().all()


@router.get("/{resource_id}", response_model=ResourceResponse)
async def get_resource(
    resource_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    resource = await db.get(Resource, resource_id)
    if not resource:
        raise HTTPException(status_code=404, detail="Resource not found")
    return resource


@router.patch("/{resource_id}", response_model=ResourceResponse)
async def update_resource(
    resource_id: uuid.UUID,
    data: ResourceUpdate,
    db: AsyncSession = Depends(get_db),
):
    resource = await db.get(Resource, resource_id)
    if not resource:
        raise HTTPException(status_code=404, detail="Resource not found")

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(resource, field, value)

    await db.commit()
    await db.refresh(resource)
    return resource


@router.delete("/{resource_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_resource(
    resource_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    resource = await db.get(Resource, resource_id)
    if not resource:
        raise HTTPException(status_code=404, detail="Resource not found")

    await db.delete(resource)
    await db.commit()
```

- [ ] **Step 6: Mount resources router in main.py**

Replace `services/workshop/app/main.py`:

```python
from fastapi import FastAPI

from app.api.resources import router as resources_router

app = FastAPI(title="DRIVE DMS Workshop Service", version="0.1.0")

app.include_router(resources_router)


@app.get("/health")
async def health():
    return {"status": "ok", "service": "workshop"}
```

- [ ] **Step 7: Run tests**

```bash
cd /opt/drive-dms/services/workshop
pytest tests/test_resources_api.py -v
```

Expected: All 7 tests PASS.

- [ ] **Step 8: Commit**

```bash
cd /opt/drive-dms
git add services/workshop/
git commit -m "feat(workshop): Resource model + full CRUD API (mechanics and lifts)"
```

---

### Task 8: Workshop Service — Alembic Migrations Setup

**Files:**
- Create: `services/workshop/alembic.ini`
- Create: `services/workshop/migrations/env.py`
- Create: `services/workshop/migrations/script.py.mako`
- Create: `services/workshop/migrations/versions/.gitkeep`

- [ ] **Step 1: Create alembic.ini**

Write `services/workshop/alembic.ini`:

```ini
[alembic]
script_location = migrations
sqlalchemy.url = postgresql+asyncpg://dms_user:DmsDevPassword2026@db:5432/drive_dms

[loggers]
keys = root,sqlalchemy,alembic

[handlers]
keys = console

[formatters]
keys = generic

[logger_root]
level = WARN
handlers = console

[logger_sqlalchemy]
level = WARN
handlers =
qualname = sqlalchemy.engine

[logger_alembic]
level = INFO
handlers =
qualname = alembic

[handler_console]
class = StreamHandler
args = (sys.stderr,)
level = NOTSET
formatter = generic

[formatter_generic]
format = %(levelname)-5.5s [%(name)s] %(message)s
datefmt = %H:%M:%S
```

- [ ] **Step 2: Create migrations/env.py**

Write `services/workshop/migrations/env.py`:

```python
import asyncio
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.ext.asyncio import async_engine_from_config
from alembic import context

from app.database import Base
from app.models import Resource  # noqa: F401 — ensure models are registered

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


def run_migrations_online() -> None:
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
```

- [ ] **Step 3: Create migration template**

Write `services/workshop/migrations/script.py.mako`:

```mako
"""${message}

Revision ID: ${up_revision}
Revises: ${down_revision | comma,n}
Create Date: ${create_date}

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
${imports if imports else ""}

# revision identifiers, used by Alembic.
revision: str = ${repr(up_revision)}
down_revision: Union[str, None] = ${repr(down_revision)}
branch_labels: Union[str, Sequence[str], None] = ${repr(branch_labels)}
depends_on: Union[str, Sequence[str], None] = ${repr(depends_on)}


def upgrade() -> None:
    ${upgrades if upgrades else "pass"}


def downgrade() -> None:
    ${downgrades if downgrades else "pass"}
```

Create `services/workshop/migrations/versions/.gitkeep` (empty file).

- [ ] **Step 4: Commit**

```bash
cd /opt/drive-dms
git add services/workshop/alembic.ini services/workshop/migrations/
git commit -m "chore(workshop): Alembic migration setup for async PostgreSQL"
```

---

### Task 9: Frontend — Next.js Skeleton + Auth

**Files:**
- Create: `frontend/package.json`
- Create: `frontend/tsconfig.json`
- Create: `frontend/next.config.ts`
- Create: `frontend/tailwind.config.ts`
- Create: `frontend/postcss.config.js`
- Create: `frontend/Dockerfile`
- Create: `frontend/src/app/layout.tsx`
- Create: `frontend/src/app/page.tsx`
- Create: `frontend/src/app/globals.css`
- Create: `frontend/src/app/login/page.tsx`
- Create: `frontend/src/lib/api-client.ts`
- Create: `frontend/src/lib/auth.ts`
- Create: `frontend/src/stores/auth-store.ts`
- Create: `frontend/src/types/auth.ts`
- Create: `frontend/src/hooks/use-auth.ts`

- [ ] **Step 1: Create package.json**

Write `frontend/package.json`:

```json
{
  "name": "drive-dms-frontend",
  "version": "0.1.0",
  "private": true,
  "scripts": {
    "dev": "next dev --port 3000",
    "build": "next build",
    "start": "next start --port 3000",
    "lint": "next lint"
  },
  "dependencies": {
    "next": "^14.2.0",
    "react": "^18.3.0",
    "react-dom": "^18.3.0",
    "zustand": "^4.5.0",
    "@tanstack/react-query": "^5.50.0",
    "lucide-react": "^0.400.0",
    "clsx": "^2.1.0"
  },
  "devDependencies": {
    "typescript": "^5.5.0",
    "@types/node": "^20.14.0",
    "@types/react": "^18.3.0",
    "@types/react-dom": "^18.3.0",
    "tailwindcss": "^3.4.0",
    "postcss": "^8.4.0",
    "autoprefixer": "^10.4.0",
    "eslint": "^8.57.0",
    "eslint-config-next": "^14.2.0"
  }
}
```

- [ ] **Step 2: Create config files**

Write `frontend/tsconfig.json`:

```json
{
  "compilerOptions": {
    "target": "es5",
    "lib": ["dom", "dom.iterable", "esnext"],
    "allowJs": true,
    "skipLibCheck": true,
    "strict": true,
    "noEmit": true,
    "esModuleInterop": true,
    "module": "esnext",
    "moduleResolution": "bundler",
    "resolveJsonModule": true,
    "isolatedModules": true,
    "jsx": "preserve",
    "incremental": true,
    "plugins": [{ "name": "next" }],
    "paths": { "@/*": ["./src/*"] }
  },
  "include": ["next-env.d.ts", "**/*.ts", "**/*.tsx", ".next/types/**/*.ts"],
  "exclude": ["node_modules"]
}
```

Write `frontend/next.config.ts`:

```typescript
import type { NextConfig } from 'next'

const nextConfig: NextConfig = {
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: 'http://gateway:8000/api/:path*',
      },
    ]
  },
}

export default nextConfig
```

Write `frontend/tailwind.config.ts`:

```typescript
import type { Config } from 'tailwindcss'

const config: Config = {
  content: ['./src/**/*.{js,ts,jsx,tsx,mdx}'],
  theme: {
    extend: {
      colors: {
        brand: {
          50: '#eff6ff',
          500: '#3b82f6',
          600: '#2563eb',
          700: '#1d4ed8',
        },
      },
    },
  },
  plugins: [],
}

export default config
```

Write `frontend/postcss.config.js`:

```javascript
module.exports = {
  plugins: {
    tailwindcss: {},
    autoprefixer: {},
  },
}
```

- [ ] **Step 3: Create Dockerfile**

Write `frontend/Dockerfile`:

```dockerfile
FROM node:20-alpine

WORKDIR /app

COPY package.json package-lock.json* ./
RUN npm install

COPY . .

CMD ["npm", "run", "dev"]
```

- [ ] **Step 4: Create types and API client**

Write `frontend/src/types/auth.ts`:

```typescript
export interface UserInfo {
  username: string
  tenant: string
  location: string
  roles: string[]
  permissions: string[]
  display_name: string
}

export interface LoginRequest {
  username: string
  password: string
}

export interface TokenResponse {
  access_token: string
  token_type: string
  expires_in: number
}
```

Write `frontend/src/lib/api-client.ts`:

```typescript
const API_BASE = '/api/v1'

class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message)
    this.name = 'ApiError'
  }
}

async function request<T>(
  path: string,
  options: RequestInit = {}
): Promise<T> {
  const token = localStorage.getItem('access_token')

  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(options.headers as Record<string, string>),
  }

  if (token) {
    headers['Authorization'] = `Bearer ${token}`
  }

  const res = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers,
  })

  if (res.status === 401) {
    localStorage.removeItem('access_token')
    window.location.href = '/login'
    throw new ApiError(401, 'Unauthorized')
  }

  if (!res.ok) {
    const body = await res.json().catch(() => ({ detail: 'Unknown error' }))
    throw new ApiError(res.status, body.detail || 'Request failed')
  }

  if (res.status === 204) {
    return undefined as T
  }

  return res.json()
}

export const api = {
  get: <T>(path: string) => request<T>(path),

  post: <T>(path: string, body: unknown) =>
    request<T>(path, { method: 'POST', body: JSON.stringify(body) }),

  patch: <T>(path: string, body: unknown) =>
    request<T>(path, { method: 'PATCH', body: JSON.stringify(body) }),

  delete: <T>(path: string) =>
    request<T>(path, { method: 'DELETE' }),
}
```

Write `frontend/src/lib/auth.ts`:

```typescript
import type { LoginRequest, TokenResponse, UserInfo } from '@/types/auth'
import { api } from './api-client'

export async function login(credentials: LoginRequest): Promise<TokenResponse> {
  const data = await api.post<TokenResponse>('/auth/login', credentials)
  localStorage.setItem('access_token', data.access_token)
  return data
}

export async function fetchCurrentUser(): Promise<UserInfo> {
  return api.get<UserInfo>('/auth/me')
}

export function logout(): void {
  localStorage.removeItem('access_token')
  window.location.href = '/login'
}

export function isAuthenticated(): boolean {
  return !!localStorage.getItem('access_token')
}
```

- [ ] **Step 5: Create auth store**

Write `frontend/src/stores/auth-store.ts`:

```typescript
import { create } from 'zustand'
import type { UserInfo } from '@/types/auth'

interface AuthState {
  user: UserInfo | null
  isLoading: boolean
  setUser: (user: UserInfo | null) => void
  setLoading: (loading: boolean) => void
  hasPermission: (permission: string) => boolean
  hasRole: (role: string) => boolean
}

export const useAuthStore = create<AuthState>((set, get) => ({
  user: null,
  isLoading: true,

  setUser: (user) => set({ user, isLoading: false }),
  setLoading: (isLoading) => set({ isLoading }),

  hasPermission: (permission) => {
    const { user } = get()
    if (!user) return false
    return user.permissions.includes('*') || user.permissions.includes(permission)
  },

  hasRole: (role) => {
    const { user } = get()
    if (!user) return false
    return user.roles.includes(role)
  },
}))
```

- [ ] **Step 6: Create useAuth hook**

Write `frontend/src/hooks/use-auth.ts`:

```typescript
'use client'

import { useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { useAuthStore } from '@/stores/auth-store'
import { fetchCurrentUser, isAuthenticated } from '@/lib/auth'

export function useAuth({ required = true } = {}) {
  const router = useRouter()
  const { user, isLoading, setUser } = useAuthStore()

  useEffect(() => {
    if (user) return

    if (!isAuthenticated()) {
      if (required) router.push('/login')
      setUser(null)
      return
    }

    fetchCurrentUser()
      .then(setUser)
      .catch(() => {
        setUser(null)
        if (required) router.push('/login')
      })
  }, [user, required, router, setUser])

  return { user, isLoading }
}
```

- [ ] **Step 7: Create app layout and pages**

Write `frontend/src/app/globals.css`:

```css
@tailwind base;
@tailwind components;
@tailwind utilities;
```

Write `frontend/src/app/layout.tsx`:

```tsx
import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'DRIVE DMS',
  description: 'Dealer Management System',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="de">
      <body className="bg-gray-50 text-gray-900 antialiased">
        {children}
      </body>
    </html>
  )
}
```

Write `frontend/src/app/page.tsx`:

```tsx
import { redirect } from 'next/navigation'

export default function Home() {
  redirect('/login')
}
```

Write `frontend/src/app/login/page.tsx`:

```tsx
'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { login, fetchCurrentUser } from '@/lib/auth'
import { useAuthStore } from '@/stores/auth-store'

export default function LoginPage() {
  const router = useRouter()
  const setUser = useAuthStore((s) => s.setUser)
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setError('')
    setLoading(true)

    try {
      await login({ username, password })
      const user = await fetchCurrentUser()
      setUser(user)
      router.push('/dashboard')
    } catch {
      setError('Benutzername oder Passwort falsch')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center">
      <div className="w-full max-w-sm rounded-xl bg-white p-8 shadow-lg">
        <h1 className="mb-2 text-2xl font-bold">DRIVE DMS</h1>
        <p className="mb-6 text-sm text-gray-500">Werkstatt-Management</p>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="mb-1 block text-sm font-medium">Benutzer</label>
            <input
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              className="w-full rounded-lg border px-3 py-2 focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500"
              autoFocus
              required
            />
          </div>

          <div>
            <label className="mb-1 block text-sm font-medium">Passwort</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full rounded-lg border px-3 py-2 focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500"
              required
            />
          </div>

          {error && (
            <p className="text-sm text-red-600">{error}</p>
          )}

          <button
            type="submit"
            disabled={loading}
            className="w-full rounded-lg bg-brand-600 px-4 py-2 text-white hover:bg-brand-700 disabled:opacity-50"
          >
            {loading ? 'Anmelden...' : 'Anmelden'}
          </button>
        </form>
      </div>
    </div>
  )
}
```

- [ ] **Step 8: Commit**

```bash
cd /opt/drive-dms
git add frontend/
git commit -m "feat(frontend): Next.js skeleton with login page, auth store, API client"
```

---

### Task 10: Frontend — Authenticated Layout (Sidebar + Header)

**Files:**
- Create: `frontend/src/app/(authenticated)/layout.tsx`
- Create: `frontend/src/app/(authenticated)/dashboard/page.tsx`
- Create: `frontend/src/components/shared/sidebar.tsx`
- Create: `frontend/src/components/shared/header.tsx`

- [ ] **Step 1: Create sidebar component**

Write `frontend/src/components/shared/sidebar.tsx`:

```tsx
'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { clsx } from 'clsx'
import {
  LayoutDashboard,
  ClipboardList,
  Columns3,
  Calendar,
  Users,
  Wrench,
} from 'lucide-react'

const NAV_ITEMS = [
  { href: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { href: '/orders', label: 'Auftraege', icon: ClipboardList },
  { href: '/orders/kanban', label: 'Kanban', icon: Columns3 },
  { href: '/planner', label: 'Planer', icon: Calendar },
  { href: '/resources', label: 'Ressourcen', icon: Users },
]

export function Sidebar() {
  const pathname = usePathname()

  return (
    <aside className="flex h-screen w-56 flex-col border-r bg-white">
      <div className="flex h-14 items-center gap-2 border-b px-4">
        <Wrench className="h-5 w-5 text-brand-600" />
        <span className="text-lg font-bold">DRIVE DMS</span>
      </div>

      <nav className="flex-1 space-y-1 p-3">
        {NAV_ITEMS.map(({ href, label, icon: Icon }) => (
          <Link
            key={href}
            href={href}
            className={clsx(
              'flex items-center gap-3 rounded-lg px-3 py-2 text-sm transition-colors',
              pathname === href || pathname.startsWith(href + '/')
                ? 'bg-brand-50 text-brand-700 font-medium'
                : 'text-gray-600 hover:bg-gray-100'
            )}
          >
            <Icon className="h-4 w-4" />
            {label}
          </Link>
        ))}
      </nav>
    </aside>
  )
}
```

- [ ] **Step 2: Create header component**

Write `frontend/src/components/shared/header.tsx`:

```tsx
'use client'

import { LogOut, User } from 'lucide-react'
import { useAuthStore } from '@/stores/auth-store'
import { logout } from '@/lib/auth'

export function Header() {
  const user = useAuthStore((s) => s.user)

  return (
    <header className="flex h-14 items-center justify-between border-b bg-white px-6">
      <div />

      <div className="flex items-center gap-4">
        <div className="flex items-center gap-2 text-sm">
          <User className="h-4 w-4 text-gray-400" />
          <span className="font-medium">{user?.display_name || user?.username}</span>
          <span className="text-gray-400">|</span>
          <span className="text-gray-500">{user?.location}</span>
        </div>

        <button
          onClick={logout}
          className="rounded-lg p-2 text-gray-400 hover:bg-gray-100 hover:text-gray-600"
          title="Abmelden"
        >
          <LogOut className="h-4 w-4" />
        </button>
      </div>
    </header>
  )
}
```

- [ ] **Step 3: Create authenticated layout**

Write `frontend/src/app/(authenticated)/layout.tsx`:

```tsx
'use client'

import { useAuth } from '@/hooks/use-auth'
import { Sidebar } from '@/components/shared/sidebar'
import { Header } from '@/components/shared/header'

export default function AuthenticatedLayout({
  children,
}: {
  children: React.ReactNode
}) {
  const { user, isLoading } = useAuth({ required: true })

  if (isLoading || !user) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-brand-500 border-t-transparent" />
      </div>
    )
  }

  return (
    <div className="flex h-screen">
      <Sidebar />
      <div className="flex flex-1 flex-col overflow-hidden">
        <Header />
        <main className="flex-1 overflow-auto bg-gray-50 p-6">
          {children}
        </main>
      </div>
    </div>
  )
}
```

- [ ] **Step 4: Create dashboard page**

Write `frontend/src/app/(authenticated)/dashboard/page.tsx`:

```tsx
export default function DashboardPage() {
  return (
    <div>
      <h1 className="text-2xl font-bold">Dashboard</h1>
      <p className="mt-2 text-gray-500">Werkstatt-Uebersicht kommt hier hin.</p>
    </div>
  )
}
```

- [ ] **Step 5: Commit**

```bash
cd /opt/drive-dms
git add frontend/
git commit -m "feat(frontend): authenticated layout with sidebar navigation and header"
```

---

### Task 11: Docker Compose — Full Stack Smoke Test

- [ ] **Step 1: Copy .env and start everything**

```bash
cd /opt/drive-dms
cp .env.example .env
docker compose build
docker compose up -d
```

- [ ] **Step 2: Verify all containers are running**

```bash
docker compose ps
```

Expected: All 6 services running (traefik, db, redis, gateway, workshop, frontend).

- [ ] **Step 3: Test health endpoints**

```bash
curl http://localhost/api/health
# Expected: {"status":"ok","service":"gateway"}

curl http://localhost:8001/health  # direct workshop access via docker network
# This won't work from host — test via gateway proxy or docker exec
docker compose exec gateway curl http://workshop:8001/health
# Expected: {"status":"ok","service":"workshop"}
```

- [ ] **Step 4: Test login flow**

```bash
curl -X POST http://localhost/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "dev-admin", "password": "any"}'
# Expected: {"access_token":"eyJ...","token_type":"bearer","expires_in":28800}
```

- [ ] **Step 5: Test authenticated endpoint**

```bash
TOKEN=$(curl -s -X POST http://localhost/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "dev-admin", "password": "any"}' | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")

curl http://localhost/api/v1/auth/me \
  -H "Authorization: Bearer $TOKEN"
# Expected: {"username":"dev-admin","tenant":"greiner","location":"deg-opel",...}
```

- [ ] **Step 6: Commit (if any fixes needed)**

```bash
cd /opt/drive-dms
git add -A
git commit -m "chore: docker compose smoke test fixes"
```

---

## PHASE 1: AUFTRAGSMANAGEMENT

---

### Task 12: Workshop Service — Order + Position Models

**Files:**
- Create: `services/workshop/app/models/order.py`
- Create: `services/workshop/app/models/position.py`
- Modify: `services/workshop/app/models/__init__.py` — add Order, Position imports
- Create: `services/workshop/tests/test_models.py`

- [ ] **Step 1: Write model tests**

Write `services/workshop/tests/test_models.py`:

```python
import pytest
import uuid

from app.models.order import WorkshopOrder
from app.models.position import Position
from app.models.enums import OrderStatus, PositionType, PositionStatus


@pytest.mark.anyio
async def test_create_order(db_session):
    order = WorkshopOrder(
        tenant_id="greiner",
        order_number="WA-2026-0001",
        status=OrderStatus.APPOINTMENT,
        customer_id=uuid.uuid4(),
        vehicle_id=uuid.uuid4(),
        scheduled_date="2026-04-10",
        advisor_id="huber",
        location_id="deg-opel",
    )
    db_session.add(order)
    await db_session.commit()
    await db_session.refresh(order)

    assert order.id is not None
    assert order.order_number == "WA-2026-0001"
    assert order.status == OrderStatus.APPOINTMENT


@pytest.mark.anyio
async def test_create_position(db_session):
    order = WorkshopOrder(
        tenant_id="greiner",
        order_number="WA-2026-0002",
        status=OrderStatus.APPOINTMENT,
        location_id="deg-opel",
    )
    db_session.add(order)
    await db_session.commit()
    await db_session.refresh(order)

    position = Position(
        order_id=order.id,
        type=PositionType.LABOR,
        description="Inspektion 40.000km",
        target_minutes=120,
        status=PositionStatus.PLANNED,
    )
    db_session.add(position)
    await db_session.commit()
    await db_session.refresh(position)

    assert position.id is not None
    assert position.order_id == order.id
    assert position.target_minutes == 120


@pytest.mark.anyio
async def test_order_positions_relationship(db_session):
    order = WorkshopOrder(
        tenant_id="greiner",
        order_number="WA-2026-0003",
        status=OrderStatus.PREPARED,
        location_id="deg-opel",
    )
    db_session.add(order)
    await db_session.commit()

    p1 = Position(order_id=order.id, type=PositionType.LABOR, description="Bremse vorne", target_minutes=60, status=PositionStatus.PLANNED)
    p2 = Position(order_id=order.id, type=PositionType.PARTS, description="Bremsscheiben 2x", target_minutes=0, status=PositionStatus.PLANNED)
    db_session.add_all([p1, p2])
    await db_session.commit()

    await db_session.refresh(order)
    # Verify via query since lazy loading doesn't work with async
    from sqlalchemy import select
    result = await db_session.execute(select(Position).where(Position.order_id == order.id))
    positions = result.scalars().all()
    assert len(positions) == 2
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd /opt/drive-dms/services/workshop
pytest tests/test_models.py -v
```

Expected: FAIL — `ModuleNotFoundError: No module named 'app.models.order'`

- [ ] **Step 3: Implement Order model**

Write `services/workshop/app/models/order.py`:

```python
import uuid
from datetime import date, time

from sqlalchemy import String, Date, Time, Text, Enum as SAEnum, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, JSONB, ARRAY

from app.database import Base
from app.models.base import TimestampMixin, new_uuid
from app.models.enums import OrderStatus, CheckinType


class WorkshopOrder(Base, TimestampMixin):
    __tablename__ = "workshop_orders"

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=new_uuid)
    tenant_id: Mapped[str] = mapped_column(String(63), nullable=False, default="greiner")
    order_number: Mapped[str] = mapped_column(String(20), nullable=False, unique=True)
    status: Mapped[OrderStatus] = mapped_column(SAEnum(OrderStatus, name="order_status"), nullable=False, default=OrderStatus.APPOINTMENT)

    # Customer & Vehicle (UUIDs referencing bridge/master data)
    customer_id: Mapped[uuid.UUID | None] = mapped_column(PG_UUID(as_uuid=True), nullable=True)
    vehicle_id: Mapped[uuid.UUID | None] = mapped_column(PG_UUID(as_uuid=True), nullable=True)

    # Scheduling
    scheduled_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    scheduled_time: Mapped[time | None] = mapped_column(Time, nullable=True)

    # Assignment
    advisor_id: Mapped[str | None] = mapped_column(String(63), nullable=True)
    location_id: Mapped[str] = mapped_column(String(63), nullable=False)

    # Check-in
    checkin_type: Mapped[CheckinType | None] = mapped_column(SAEnum(CheckinType, name="checkin_type"), nullable=True)
    checkin_signature: Mapped[str | None] = mapped_column(Text, nullable=True)
    checkin_photos: Mapped[list | None] = mapped_column(JSONB, nullable=True, default=list)

    # Notes
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    priority: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # Relationships
    positions = relationship("Position", back_populates="order", cascade="all, delete-orphan", lazy="selectin")
```

- [ ] **Step 4: Implement Position model**

Write `services/workshop/app/models/position.py`:

```python
import uuid
from datetime import datetime

from sqlalchemy import String, Integer, Boolean, Text, ForeignKey, Enum as SAEnum, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID as PG_UUID

from app.database import Base
from app.models.base import TimestampMixin, new_uuid
from app.models.enums import PositionType, PositionStatus


class Position(Base, TimestampMixin):
    __tablename__ = "positions"

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=new_uuid)
    order_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("workshop_orders.id", ondelete="CASCADE"), nullable=False)

    type: Mapped[PositionType] = mapped_column(SAEnum(PositionType, name="position_type"), nullable=False)
    description: Mapped[str] = mapped_column(String(500), nullable=False)
    target_minutes: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # Assignment
    assigned_resource_id: Mapped[uuid.UUID | None] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("resources.id"), nullable=True)
    assigned_lift_id: Mapped[uuid.UUID | None] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("resources.id"), nullable=True)

    # Scheduling
    scheduled_start: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    scheduled_end: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Status
    status: Mapped[PositionStatus] = mapped_column(SAEnum(PositionStatus, name="position_status"), nullable=False, default=PositionStatus.PLANNED)

    # Upsell
    is_upsell: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    upsell_approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    upsell_approved_by: Mapped[str | None] = mapped_column(String(63), nullable=True)

    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # Relationships
    order = relationship("WorkshopOrder", back_populates="positions")
```

- [ ] **Step 5: Update models __init__.py**

Replace `services/workshop/app/models/__init__.py`:

```python
from app.models.base import TimestampMixin  # noqa: F401
from app.models.enums import OrderStatus, PositionType, PositionStatus, ResourceType, CheckinType  # noqa: F401
from app.models.resource import Resource  # noqa: F401
from app.models.order import WorkshopOrder  # noqa: F401
from app.models.position import Position  # noqa: F401
```

- [ ] **Step 6: Run tests**

```bash
cd /opt/drive-dms/services/workshop
pytest tests/test_models.py -v
```

Expected: All 3 tests PASS.

- [ ] **Step 7: Commit**

```bash
cd /opt/drive-dms
git add services/workshop/
git commit -m "feat(workshop): WorkshopOrder + Position models with relationships"
```

---

### Task 13: Workshop Service — Order Service (Business Logic)

**Files:**
- Create: `services/workshop/app/services/__init__.py`
- Create: `services/workshop/app/services/order_service.py`
- Create: `services/workshop/tests/test_order_service.py`

- [ ] **Step 1: Write order service tests**

Write `services/workshop/tests/test_order_service.py`:

```python
import pytest
from datetime import date

from app.models.enums import OrderStatus
from app.services.order_service import OrderService


@pytest.mark.anyio
async def test_create_order(db_session):
    svc = OrderService(db_session)
    order = await svc.create_order(
        tenant_id="greiner",
        location_id="deg-opel",
        scheduled_date=date(2026, 4, 10),
        advisor_id="huber",
        notes="Inspektion + Klimaservice",
    )

    assert order.id is not None
    assert order.order_number.startswith("WA-2026-")
    assert order.status == OrderStatus.APPOINTMENT
    assert order.location_id == "deg-opel"


@pytest.mark.anyio
async def test_order_number_auto_increments(db_session):
    svc = OrderService(db_session)
    o1 = await svc.create_order(tenant_id="greiner", location_id="deg-opel")
    o2 = await svc.create_order(tenant_id="greiner", location_id="deg-opel")

    n1 = int(o1.order_number.split("-")[-1])
    n2 = int(o2.order_number.split("-")[-1])
    assert n2 == n1 + 1


@pytest.mark.anyio
async def test_valid_status_transition(db_session):
    svc = OrderService(db_session)
    order = await svc.create_order(tenant_id="greiner", location_id="deg-opel")
    assert order.status == OrderStatus.APPOINTMENT

    updated = await svc.transition_status(order.id, OrderStatus.PREPARED)
    assert updated.status == OrderStatus.PREPARED

    updated = await svc.transition_status(order.id, OrderStatus.DISPATCHED)
    assert updated.status == OrderStatus.DISPATCHED


@pytest.mark.anyio
async def test_invalid_status_transition_raises(db_session):
    svc = OrderService(db_session)
    order = await svc.create_order(tenant_id="greiner", location_id="deg-opel")

    with pytest.raises(ValueError, match="Invalid status transition"):
        await svc.transition_status(order.id, OrderStatus.COMPLETED)


@pytest.mark.anyio
async def test_list_orders_by_location(db_session):
    svc = OrderService(db_session)
    await svc.create_order(tenant_id="greiner", location_id="deg-opel")
    await svc.create_order(tenant_id="greiner", location_id="deg-opel")
    await svc.create_order(tenant_id="greiner", location_id="landau")

    orders = await svc.list_orders(location_id="deg-opel")
    assert len(orders) == 2

    orders = await svc.list_orders(location_id="landau")
    assert len(orders) == 1
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_order_service.py -v
```

Expected: FAIL — `ModuleNotFoundError: No module named 'app.services.order_service'`

- [ ] **Step 3: Implement OrderService**

Write `services/workshop/app/services/__init__.py` (empty file).

Write `services/workshop/app/services/order_service.py`:

```python
import uuid
from datetime import date, time

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.order import WorkshopOrder
from app.models.enums import OrderStatus

# Valid status transitions: from -> [to, ...]
VALID_TRANSITIONS: dict[OrderStatus, list[OrderStatus]] = {
    OrderStatus.APPOINTMENT: [OrderStatus.PREPARED, OrderStatus.DISPATCHED, OrderStatus.CHECKED_IN],
    OrderStatus.PREPARED: [OrderStatus.DISPATCHED, OrderStatus.CHECKED_IN],
    OrderStatus.DISPATCHED: [OrderStatus.CHECKED_IN],
    OrderStatus.CHECKED_IN: [OrderStatus.IN_PROGRESS],
    OrderStatus.IN_PROGRESS: [OrderStatus.QA, OrderStatus.COMPLETED],
    OrderStatus.QA: [OrderStatus.IN_PROGRESS, OrderStatus.COMPLETED],
    OrderStatus.COMPLETED: [OrderStatus.PICKED_UP],
    OrderStatus.PICKED_UP: [],
}


class OrderService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_order(
        self,
        tenant_id: str,
        location_id: str,
        scheduled_date: date | None = None,
        scheduled_time: time | None = None,
        customer_id: uuid.UUID | None = None,
        vehicle_id: uuid.UUID | None = None,
        advisor_id: str | None = None,
        notes: str | None = None,
    ) -> WorkshopOrder:
        order_number = await self._next_order_number()

        order = WorkshopOrder(
            tenant_id=tenant_id,
            order_number=order_number,
            status=OrderStatus.APPOINTMENT,
            location_id=location_id,
            scheduled_date=scheduled_date,
            scheduled_time=scheduled_time,
            customer_id=customer_id,
            vehicle_id=vehicle_id,
            advisor_id=advisor_id,
            notes=notes,
        )

        self.db.add(order)
        await self.db.commit()
        await self.db.refresh(order)
        return order

    async def get_order(self, order_id: uuid.UUID) -> WorkshopOrder | None:
        return await self.db.get(WorkshopOrder, order_id)

    async def list_orders(
        self,
        location_id: str | None = None,
        status: OrderStatus | None = None,
        scheduled_date: date | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[WorkshopOrder]:
        query = select(WorkshopOrder)

        if location_id:
            query = query.where(WorkshopOrder.location_id == location_id)
        if status:
            query = query.where(WorkshopOrder.status == status)
        if scheduled_date:
            query = query.where(WorkshopOrder.scheduled_date == scheduled_date)

        query = query.order_by(WorkshopOrder.created_at.desc()).limit(limit).offset(offset)

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def transition_status(
        self, order_id: uuid.UUID, new_status: OrderStatus
    ) -> WorkshopOrder:
        order = await self.db.get(WorkshopOrder, order_id)
        if not order:
            raise ValueError(f"Order {order_id} not found")

        allowed = VALID_TRANSITIONS.get(order.status, [])
        if new_status not in allowed:
            raise ValueError(
                f"Invalid status transition: {order.status.value} -> {new_status.value}. "
                f"Allowed: {[s.value for s in allowed]}"
            )

        order.status = new_status
        await self.db.commit()
        await self.db.refresh(order)
        return order

    async def update_order(
        self, order_id: uuid.UUID, **fields
    ) -> WorkshopOrder:
        order = await self.db.get(WorkshopOrder, order_id)
        if not order:
            raise ValueError(f"Order {order_id} not found")

        for field, value in fields.items():
            if hasattr(order, field) and field not in ("id", "tenant_id", "order_number"):
                setattr(order, field, value)

        await self.db.commit()
        await self.db.refresh(order)
        return order

    async def _next_order_number(self) -> str:
        from datetime import datetime

        year = datetime.now().year

        result = await self.db.execute(
            select(func.count()).where(
                WorkshopOrder.order_number.like(f"WA-{year}-%")
            )
        )
        count = result.scalar_one()
        return f"WA-{year}-{count + 1:04d}"
```

- [ ] **Step 4: Run tests**

```bash
pytest tests/test_order_service.py -v
```

Expected: All 5 tests PASS.

- [ ] **Step 5: Commit**

```bash
cd /opt/drive-dms
git add services/workshop/
git commit -m "feat(workshop): OrderService with status machine, auto-numbering, CRUD"
```

---

### Task 14: Workshop Service — Orders API Endpoints

**Files:**
- Create: `services/workshop/app/schemas/order.py`
- Create: `services/workshop/app/schemas/position.py`
- Create: `services/workshop/app/api/orders.py`
- Create: `services/workshop/app/api/positions.py`
- Modify: `services/workshop/app/main.py` — mount order + position routers
- Create: `services/workshop/tests/test_orders_api.py`
- Create: `services/workshop/tests/test_positions_api.py`

- [ ] **Step 1: Write order API tests**

Write `services/workshop/tests/test_orders_api.py`:

```python
import pytest


ORDER_DATA = {
    "location_id": "deg-opel",
    "scheduled_date": "2026-04-10",
    "advisor_id": "huber",
    "notes": "Inspektion 40.000km",
}


@pytest.mark.anyio
async def test_create_order(client):
    resp = await client.post("/orders", json=ORDER_DATA)
    assert resp.status_code == 201
    data = resp.json()
    assert data["order_number"].startswith("WA-")
    assert data["status"] == "appointment"
    assert data["location_id"] == "deg-opel"


@pytest.mark.anyio
async def test_get_order(client):
    create_resp = await client.post("/orders", json=ORDER_DATA)
    order_id = create_resp.json()["id"]

    resp = await client.get(f"/orders/{order_id}")
    assert resp.status_code == 200
    assert resp.json()["id"] == order_id
    assert "positions" in resp.json()


@pytest.mark.anyio
async def test_list_orders(client):
    await client.post("/orders", json=ORDER_DATA)
    await client.post("/orders", json={**ORDER_DATA, "location_id": "landau"})

    resp = await client.get("/orders")
    assert resp.status_code == 200
    assert len(resp.json()) == 2

    resp = await client.get("/orders?location_id=deg-opel")
    assert len(resp.json()) == 1


@pytest.mark.anyio
async def test_update_order_status(client):
    create_resp = await client.post("/orders", json=ORDER_DATA)
    order_id = create_resp.json()["id"]

    resp = await client.patch(
        f"/orders/{order_id}",
        json={"status": "prepared"},
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "prepared"


@pytest.mark.anyio
async def test_invalid_status_transition(client):
    create_resp = await client.post("/orders", json=ORDER_DATA)
    order_id = create_resp.json()["id"]

    resp = await client.patch(
        f"/orders/{order_id}",
        json={"status": "completed"},
    )
    assert resp.status_code == 409


@pytest.mark.anyio
async def test_update_order_fields(client):
    create_resp = await client.post("/orders", json=ORDER_DATA)
    order_id = create_resp.json()["id"]

    resp = await client.patch(
        f"/orders/{order_id}",
        json={"notes": "Updated notes", "priority": 2},
    )
    assert resp.status_code == 200
    assert resp.json()["notes"] == "Updated notes"
    assert resp.json()["priority"] == 2
```

- [ ] **Step 2: Write position API tests**

Write `services/workshop/tests/test_positions_api.py`:

```python
import pytest


@pytest.fixture
async def order_id(client):
    resp = await client.post("/orders", json={"location_id": "deg-opel"})
    return resp.json()["id"]


POSITION_DATA = {
    "type": "labor",
    "description": "Inspektion 40.000km",
    "target_minutes": 120,
}


@pytest.mark.anyio
async def test_add_position(client, order_id):
    resp = await client.post(f"/orders/{order_id}/positions", json=POSITION_DATA)
    assert resp.status_code == 201
    data = resp.json()
    assert data["description"] == "Inspektion 40.000km"
    assert data["target_minutes"] == 120
    assert data["status"] == "planned"


@pytest.mark.anyio
async def test_list_positions(client, order_id):
    await client.post(f"/orders/{order_id}/positions", json=POSITION_DATA)
    await client.post(f"/orders/{order_id}/positions", json={**POSITION_DATA, "description": "Oelwechsel"})

    resp = await client.get(f"/orders/{order_id}")
    assert len(resp.json()["positions"]) == 2


@pytest.mark.anyio
async def test_update_position(client, order_id):
    create_resp = await client.post(f"/orders/{order_id}/positions", json=POSITION_DATA)
    pos_id = create_resp.json()["id"]

    resp = await client.patch(
        f"/orders/{order_id}/positions/{pos_id}",
        json={"target_minutes": 150, "description": "Grosse Inspektion"},
    )
    assert resp.status_code == 200
    assert resp.json()["target_minutes"] == 150


@pytest.mark.anyio
async def test_delete_position(client, order_id):
    create_resp = await client.post(f"/orders/{order_id}/positions", json=POSITION_DATA)
    pos_id = create_resp.json()["id"]

    resp = await client.delete(f"/orders/{order_id}/positions/{pos_id}")
    assert resp.status_code == 204

    resp = await client.get(f"/orders/{order_id}")
    assert len(resp.json()["positions"]) == 0
```

- [ ] **Step 3: Run tests to verify they fail**

```bash
pytest tests/test_orders_api.py tests/test_positions_api.py -v
```

Expected: FAIL — no routes.

- [ ] **Step 4: Implement Order schemas**

Write `services/workshop/app/schemas/order.py`:

```python
import uuid
from datetime import date, time, datetime

from pydantic import BaseModel

from app.models.enums import OrderStatus, CheckinType
from app.schemas.position import PositionResponse


class OrderCreate(BaseModel):
    location_id: str
    scheduled_date: date | None = None
    scheduled_time: time | None = None
    customer_id: uuid.UUID | None = None
    vehicle_id: uuid.UUID | None = None
    advisor_id: str | None = None
    notes: str | None = None
    priority: int = 0


class OrderUpdate(BaseModel):
    status: OrderStatus | None = None
    scheduled_date: date | None = None
    scheduled_time: time | None = None
    customer_id: uuid.UUID | None = None
    vehicle_id: uuid.UUID | None = None
    advisor_id: str | None = None
    notes: str | None = None
    priority: int | None = None


class OrderResponse(BaseModel):
    id: uuid.UUID
    order_number: str
    status: OrderStatus
    location_id: str
    scheduled_date: date | None
    scheduled_time: time | None
    customer_id: uuid.UUID | None
    vehicle_id: uuid.UUID | None
    advisor_id: str | None
    notes: str | None
    priority: int
    positions: list[PositionResponse] = []
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class OrderListResponse(BaseModel):
    id: uuid.UUID
    order_number: str
    status: OrderStatus
    location_id: str
    scheduled_date: date | None
    advisor_id: str | None
    priority: int
    position_count: int = 0
    created_at: datetime

    model_config = {"from_attributes": True}
```

Write `services/workshop/app/schemas/position.py`:

```python
import uuid
from datetime import datetime

from pydantic import BaseModel

from app.models.enums import PositionType, PositionStatus


class PositionCreate(BaseModel):
    type: PositionType
    description: str
    target_minutes: int = 0
    assigned_resource_id: uuid.UUID | None = None
    assigned_lift_id: uuid.UUID | None = None
    is_upsell: bool = False
    sort_order: int = 0


class PositionUpdate(BaseModel):
    description: str | None = None
    target_minutes: int | None = None
    assigned_resource_id: uuid.UUID | None = None
    assigned_lift_id: uuid.UUID | None = None
    status: PositionStatus | None = None
    sort_order: int | None = None


class PositionResponse(BaseModel):
    id: uuid.UUID
    order_id: uuid.UUID
    type: PositionType
    description: str
    target_minutes: int
    assigned_resource_id: uuid.UUID | None
    assigned_lift_id: uuid.UUID | None
    scheduled_start: datetime | None
    scheduled_end: datetime | None
    status: PositionStatus
    is_upsell: bool
    sort_order: int
    created_at: datetime

    model_config = {"from_attributes": True}
```

- [ ] **Step 5: Implement Orders API**

Write `services/workshop/app/api/orders.py`:

```python
import uuid

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db, get_tenant_id
from app.services.order_service import OrderService
from app.models.enums import OrderStatus
from app.schemas.order import OrderCreate, OrderUpdate, OrderResponse

router = APIRouter(prefix="/orders", tags=["orders"])


@router.post("", status_code=status.HTTP_201_CREATED, response_model=OrderResponse)
async def create_order(
    data: OrderCreate,
    tenant_id: str = Depends(get_tenant_id),
    db: AsyncSession = Depends(get_db),
):
    svc = OrderService(db)
    order = await svc.create_order(
        tenant_id=tenant_id,
        location_id=data.location_id,
        scheduled_date=data.scheduled_date,
        scheduled_time=data.scheduled_time,
        customer_id=data.customer_id,
        vehicle_id=data.vehicle_id,
        advisor_id=data.advisor_id,
        notes=data.notes,
    )
    return order


@router.get("", response_model=list[OrderResponse])
async def list_orders(
    location_id: str | None = Query(None),
    status_filter: OrderStatus | None = Query(None, alias="status"),
    db: AsyncSession = Depends(get_db),
):
    svc = OrderService(db)
    return await svc.list_orders(location_id=location_id, status=status_filter)


@router.get("/{order_id}", response_model=OrderResponse)
async def get_order(
    order_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    svc = OrderService(db)
    order = await svc.get_order(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order


@router.patch("/{order_id}", response_model=OrderResponse)
async def update_order(
    order_id: uuid.UUID,
    data: OrderUpdate,
    db: AsyncSession = Depends(get_db),
):
    svc = OrderService(db)
    fields = data.model_dump(exclude_unset=True)

    # Handle status transition separately
    if "status" in fields:
        new_status = fields.pop("status")
        try:
            order = await svc.transition_status(order_id, new_status)
        except ValueError as e:
            raise HTTPException(status_code=409, detail=str(e))
    else:
        order = await svc.get_order(order_id)
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")

    # Update remaining fields
    if fields:
        try:
            order = await svc.update_order(order_id, **fields)
        except ValueError as e:
            raise HTTPException(status_code=404, detail=str(e))

    return order
```

- [ ] **Step 6: Implement Positions API**

Write `services/workshop/app/api/positions.py`:

```python
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db
from app.models.position import Position
from app.models.order import WorkshopOrder
from app.schemas.position import PositionCreate, PositionUpdate, PositionResponse

router = APIRouter(prefix="/orders/{order_id}/positions", tags=["positions"])


async def _get_order_or_404(order_id: uuid.UUID, db: AsyncSession) -> WorkshopOrder:
    order = await db.get(WorkshopOrder, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order


@router.post("", status_code=status.HTTP_201_CREATED, response_model=PositionResponse)
async def add_position(
    order_id: uuid.UUID,
    data: PositionCreate,
    db: AsyncSession = Depends(get_db),
):
    await _get_order_or_404(order_id, db)

    position = Position(
        order_id=order_id,
        type=data.type,
        description=data.description,
        target_minutes=data.target_minutes,
        assigned_resource_id=data.assigned_resource_id,
        assigned_lift_id=data.assigned_lift_id,
        is_upsell=data.is_upsell,
        sort_order=data.sort_order,
    )
    db.add(position)
    await db.commit()
    await db.refresh(position)
    return position


@router.patch("/{position_id}", response_model=PositionResponse)
async def update_position(
    order_id: uuid.UUID,
    position_id: uuid.UUID,
    data: PositionUpdate,
    db: AsyncSession = Depends(get_db),
):
    await _get_order_or_404(order_id, db)

    position = await db.get(Position, position_id)
    if not position or position.order_id != order_id:
        raise HTTPException(status_code=404, detail="Position not found")

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(position, field, value)

    await db.commit()
    await db.refresh(position)
    return position


@router.delete("/{position_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_position(
    order_id: uuid.UUID,
    position_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    await _get_order_or_404(order_id, db)

    position = await db.get(Position, position_id)
    if not position or position.order_id != order_id:
        raise HTTPException(status_code=404, detail="Position not found")

    await db.delete(position)
    await db.commit()
```

- [ ] **Step 7: Mount routers in main.py**

Replace `services/workshop/app/main.py`:

```python
from fastapi import FastAPI

from app.api.resources import router as resources_router
from app.api.orders import router as orders_router
from app.api.positions import router as positions_router

app = FastAPI(title="DRIVE DMS Workshop Service", version="0.1.0")

app.include_router(resources_router)
app.include_router(orders_router)
app.include_router(positions_router)


@app.get("/health")
async def health():
    return {"status": "ok", "service": "workshop"}
```

- [ ] **Step 8: Run all workshop tests**

```bash
cd /opt/drive-dms/services/workshop
pytest tests/ -v
```

Expected: All tests PASS (health + models + resources + order service + orders API + positions API).

- [ ] **Step 9: Commit**

```bash
cd /opt/drive-dms
git add services/workshop/
git commit -m "feat(workshop): Orders + Positions CRUD API with status machine"
```

---

### Task 15: Frontend — Order Types + API Hooks

**Files:**
- Create: `frontend/src/types/order.ts`
- Create: `frontend/src/types/resource.ts`
- Create: `frontend/src/hooks/use-orders.ts`
- Create: `frontend/src/hooks/use-resources.ts`
- Modify: `frontend/src/app/layout.tsx` — add React Query provider

- [ ] **Step 1: Create TypeScript types**

Write `frontend/src/types/order.ts`:

```typescript
export type OrderStatus =
  | 'appointment'
  | 'prepared'
  | 'dispatched'
  | 'checked_in'
  | 'in_progress'
  | 'qa'
  | 'completed'
  | 'picked_up'

export type PositionType = 'labor' | 'parts' | 'sublet'
export type PositionStatus = 'planned' | 'in_progress' | 'completed'

export interface Position {
  id: string
  order_id: string
  type: PositionType
  description: string
  target_minutes: number
  assigned_resource_id: string | null
  assigned_lift_id: string | null
  scheduled_start: string | null
  scheduled_end: string | null
  status: PositionStatus
  is_upsell: boolean
  sort_order: number
  created_at: string
}

export interface Order {
  id: string
  order_number: string
  status: OrderStatus
  location_id: string
  scheduled_date: string | null
  scheduled_time: string | null
  customer_id: string | null
  vehicle_id: string | null
  advisor_id: string | null
  notes: string | null
  priority: number
  positions: Position[]
  created_at: string
  updated_at: string
}

export interface OrderCreate {
  location_id: string
  scheduled_date?: string
  scheduled_time?: string
  advisor_id?: string
  notes?: string
  priority?: number
}

export interface OrderUpdate {
  status?: OrderStatus
  scheduled_date?: string
  notes?: string
  priority?: number
  advisor_id?: string
}

export interface PositionCreate {
  type: PositionType
  description: string
  target_minutes?: number
}

export const ORDER_STATUS_LABELS: Record<OrderStatus, string> = {
  appointment: 'Termin',
  prepared: 'Vorbereitet',
  dispatched: 'Disponiert',
  checked_in: 'Angenommen',
  in_progress: 'In Arbeit',
  qa: 'QS',
  completed: 'Fertig',
  picked_up: 'Abgeholt',
}

export const ORDER_STATUS_COLORS: Record<OrderStatus, string> = {
  appointment: 'bg-gray-100 text-gray-700',
  prepared: 'bg-blue-100 text-blue-700',
  dispatched: 'bg-indigo-100 text-indigo-700',
  checked_in: 'bg-yellow-100 text-yellow-700',
  in_progress: 'bg-orange-100 text-orange-700',
  qa: 'bg-purple-100 text-purple-700',
  completed: 'bg-green-100 text-green-700',
  picked_up: 'bg-gray-100 text-gray-500',
}
```

Write `frontend/src/types/resource.ts`:

```typescript
export type ResourceType = 'mechanic' | 'lift'

export interface Resource {
  id: string
  name: string
  type: ResourceType
  location_id: string
  qualifications: string[]
  working_hours: Record<string, string>
  color: string
  active: boolean
  created_at: string
  updated_at: string
}
```

- [ ] **Step 2: Create API hooks**

Write `frontend/src/hooks/use-orders.ts`:

```typescript
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { api } from '@/lib/api-client'
import type { Order, OrderCreate, OrderUpdate, PositionCreate } from '@/types/order'

export function useOrders(params?: { location_id?: string; status?: string }) {
  const searchParams = new URLSearchParams()
  if (params?.location_id) searchParams.set('location_id', params.location_id)
  if (params?.status) searchParams.set('status', params.status)
  const query = searchParams.toString()

  return useQuery({
    queryKey: ['orders', params],
    queryFn: () => api.get<Order[]>(`/workshop/orders${query ? `?${query}` : ''}`),
  })
}

export function useOrder(id: string) {
  return useQuery({
    queryKey: ['orders', id],
    queryFn: () => api.get<Order>(`/workshop/orders/${id}`),
    enabled: !!id,
  })
}

export function useCreateOrder() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (data: OrderCreate) => api.post<Order>('/workshop/orders', data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['orders'] }),
  })
}

export function useUpdateOrder() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ id, ...data }: OrderUpdate & { id: string }) =>
      api.patch<Order>(`/workshop/orders/${id}`, data),
    onSuccess: (_, vars) => {
      qc.invalidateQueries({ queryKey: ['orders'] })
      qc.invalidateQueries({ queryKey: ['orders', vars.id] })
    },
  })
}

export function useAddPosition() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ orderId, ...data }: PositionCreate & { orderId: string }) =>
      api.post(`/workshop/orders/${orderId}/positions`, data),
    onSuccess: (_, vars) => {
      qc.invalidateQueries({ queryKey: ['orders', vars.orderId] })
    },
  })
}

export function useDeletePosition() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ orderId, positionId }: { orderId: string; positionId: string }) =>
      api.delete(`/workshop/orders/${orderId}/positions/${positionId}`),
    onSuccess: (_, vars) => {
      qc.invalidateQueries({ queryKey: ['orders', vars.orderId] })
    },
  })
}
```

Write `frontend/src/hooks/use-resources.ts`:

```typescript
import { useQuery } from '@tanstack/react-query'
import { api } from '@/lib/api-client'
import type { Resource, ResourceType } from '@/types/resource'

export function useResources(params?: { type?: ResourceType }) {
  const searchParams = new URLSearchParams()
  if (params?.type) searchParams.set('type', params.type)
  const query = searchParams.toString()

  return useQuery({
    queryKey: ['resources', params],
    queryFn: () => api.get<Resource[]>(`/workshop/resources${query ? `?${query}` : ''}`),
  })
}
```

- [ ] **Step 3: Add React Query provider to layout**

Replace `frontend/src/app/layout.tsx`:

```tsx
import type { Metadata } from 'next'
import { Providers } from './providers'
import './globals.css'

export const metadata: Metadata = {
  title: 'DRIVE DMS',
  description: 'Dealer Management System',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="de">
      <body className="bg-gray-50 text-gray-900 antialiased">
        <Providers>{children}</Providers>
      </body>
    </html>
  )
}
```

Write `frontend/src/app/providers.tsx`:

```tsx
'use client'

import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { useState } from 'react'

export function Providers({ children }: { children: React.ReactNode }) {
  const [queryClient] = useState(
    () =>
      new QueryClient({
        defaultOptions: {
          queries: { staleTime: 30_000, retry: 1 },
        },
      })
  )

  return (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  )
}
```

- [ ] **Step 4: Commit**

```bash
cd /opt/drive-dms
git add frontend/
git commit -m "feat(frontend): TypeScript types, React Query hooks for orders + resources"
```

---

### Task 16: Frontend — Order List + Create + Detail Pages

**Files:**
- Create: `frontend/src/components/shared/status-badge.tsx`
- Create: `frontend/src/components/orders/order-form.tsx`
- Create: `frontend/src/components/orders/position-list.tsx`
- Create: `frontend/src/app/(authenticated)/orders/page.tsx`
- Create: `frontend/src/app/(authenticated)/orders/new/page.tsx`
- Create: `frontend/src/app/(authenticated)/orders/[id]/page.tsx`

- [ ] **Step 1: Create status badge component**

Write `frontend/src/components/shared/status-badge.tsx`:

```tsx
import { clsx } from 'clsx'
import { ORDER_STATUS_LABELS, ORDER_STATUS_COLORS, type OrderStatus } from '@/types/order'

export function StatusBadge({ status }: { status: OrderStatus }) {
  return (
    <span
      className={clsx(
        'inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium',
        ORDER_STATUS_COLORS[status]
      )}
    >
      {ORDER_STATUS_LABELS[status]}
    </span>
  )
}
```

- [ ] **Step 2: Create order form component**

Write `frontend/src/components/orders/order-form.tsx`:

```tsx
'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { useCreateOrder } from '@/hooks/use-orders'
import type { OrderCreate } from '@/types/order'

export function OrderForm() {
  const router = useRouter()
  const createOrder = useCreateOrder()

  const [form, setForm] = useState<OrderCreate>({
    location_id: 'deg-opel',
    scheduled_date: '',
    advisor_id: '',
    notes: '',
    priority: 0,
  })

  function update(field: keyof OrderCreate, value: string | number) {
    setForm((prev) => ({ ...prev, [field]: value }))
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    const data: OrderCreate = {
      ...form,
      scheduled_date: form.scheduled_date || undefined,
      advisor_id: form.advisor_id || undefined,
    }
    const order = await createOrder.mutateAsync(data)
    router.push(`/orders/${order.id}`)
  }

  return (
    <form onSubmit={handleSubmit} className="max-w-lg space-y-4">
      <div>
        <label className="mb-1 block text-sm font-medium">Standort</label>
        <select
          value={form.location_id}
          onChange={(e) => update('location_id', e.target.value)}
          className="w-full rounded-lg border px-3 py-2"
        >
          <option value="deg-opel">Deggendorf Opel</option>
          <option value="deg-hyundai">Deggendorf Hyundai</option>
          <option value="landau">Landau</option>
        </select>
      </div>

      <div>
        <label className="mb-1 block text-sm font-medium">Termin</label>
        <input
          type="date"
          value={form.scheduled_date}
          onChange={(e) => update('scheduled_date', e.target.value)}
          className="w-full rounded-lg border px-3 py-2"
        />
      </div>

      <div>
        <label className="mb-1 block text-sm font-medium">Serviceberater</label>
        <input
          type="text"
          value={form.advisor_id}
          onChange={(e) => update('advisor_id', e.target.value)}
          className="w-full rounded-lg border px-3 py-2"
          placeholder="z.B. huber"
        />
      </div>

      <div>
        <label className="mb-1 block text-sm font-medium">Notizen</label>
        <textarea
          value={form.notes}
          onChange={(e) => update('notes', e.target.value)}
          className="w-full rounded-lg border px-3 py-2"
          rows={3}
          placeholder="Anliegen des Kunden..."
        />
      </div>

      <div className="flex gap-3">
        <button
          type="submit"
          disabled={createOrder.isPending}
          className="rounded-lg bg-brand-600 px-4 py-2 text-white hover:bg-brand-700 disabled:opacity-50"
        >
          {createOrder.isPending ? 'Wird angelegt...' : 'Auftrag anlegen'}
        </button>
        <button
          type="button"
          onClick={() => router.back()}
          className="rounded-lg border px-4 py-2 hover:bg-gray-50"
        >
          Abbrechen
        </button>
      </div>
    </form>
  )
}
```

- [ ] **Step 3: Create position list component**

Write `frontend/src/components/orders/position-list.tsx`:

```tsx
'use client'

import { useState } from 'react'
import { Trash2, Plus } from 'lucide-react'
import { useAddPosition, useDeletePosition } from '@/hooks/use-orders'
import type { Position, PositionCreate } from '@/types/order'

interface Props {
  orderId: string
  positions: Position[]
}

export function PositionList({ orderId, positions }: Props) {
  const addPosition = useAddPosition()
  const deletePosition = useDeletePosition()
  const [showForm, setShowForm] = useState(false)
  const [desc, setDesc] = useState('')
  const [minutes, setMinutes] = useState(60)

  async function handleAdd(e: React.FormEvent) {
    e.preventDefault()
    await addPosition.mutateAsync({
      orderId,
      type: 'labor',
      description: desc,
      target_minutes: minutes,
    })
    setDesc('')
    setMinutes(60)
    setShowForm(false)
  }

  return (
    <div>
      <div className="mb-3 flex items-center justify-between">
        <h3 className="text-sm font-semibold uppercase text-gray-500">
          Positionen ({positions.length})
        </h3>
        <button
          onClick={() => setShowForm(!showForm)}
          className="flex items-center gap-1 text-sm text-brand-600 hover:text-brand-700"
        >
          <Plus className="h-4 w-4" /> Hinzufuegen
        </button>
      </div>

      {showForm && (
        <form onSubmit={handleAdd} className="mb-4 flex gap-2">
          <input
            type="text"
            value={desc}
            onChange={(e) => setDesc(e.target.value)}
            placeholder="Beschreibung"
            className="flex-1 rounded-lg border px-3 py-1.5 text-sm"
            required
            autoFocus
          />
          <input
            type="number"
            value={minutes}
            onChange={(e) => setMinutes(Number(e.target.value))}
            className="w-20 rounded-lg border px-3 py-1.5 text-sm"
            min={0}
            step={15}
          />
          <span className="self-center text-xs text-gray-400">min</span>
          <button
            type="submit"
            className="rounded-lg bg-brand-600 px-3 py-1.5 text-sm text-white"
          >
            +
          </button>
        </form>
      )}

      {positions.length === 0 ? (
        <p className="text-sm text-gray-400">Noch keine Positionen.</p>
      ) : (
        <div className="divide-y rounded-lg border bg-white">
          {positions.map((pos) => (
            <div key={pos.id} className="flex items-center justify-between px-4 py-3">
              <div>
                <span className="text-sm font-medium">{pos.description}</span>
                <span className="ml-2 text-xs text-gray-400">
                  {pos.target_minutes} min | {pos.type}
                </span>
              </div>
              <button
                onClick={() =>
                  deletePosition.mutate({ orderId, positionId: pos.id })
                }
                className="rounded p-1 text-gray-300 hover:bg-red-50 hover:text-red-500"
              >
                <Trash2 className="h-4 w-4" />
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
```

- [ ] **Step 4: Create order list page**

Write `frontend/src/app/(authenticated)/orders/page.tsx`:

```tsx
'use client'

import Link from 'next/link'
import { Plus } from 'lucide-react'
import { useOrders } from '@/hooks/use-orders'
import { StatusBadge } from '@/components/shared/status-badge'

export default function OrdersPage() {
  const { data: orders, isLoading } = useOrders()

  return (
    <div>
      <div className="mb-6 flex items-center justify-between">
        <h1 className="text-2xl font-bold">Auftraege</h1>
        <Link
          href="/orders/new"
          className="flex items-center gap-2 rounded-lg bg-brand-600 px-4 py-2 text-sm text-white hover:bg-brand-700"
        >
          <Plus className="h-4 w-4" /> Neuer Auftrag
        </Link>
      </div>

      {isLoading ? (
        <p className="text-gray-400">Laden...</p>
      ) : !orders?.length ? (
        <p className="text-gray-400">Keine Auftraege vorhanden.</p>
      ) : (
        <div className="overflow-hidden rounded-lg border bg-white">
          <table className="w-full text-left text-sm">
            <thead className="border-b bg-gray-50 text-xs uppercase text-gray-500">
              <tr>
                <th className="px-4 py-3">Nr.</th>
                <th className="px-4 py-3">Status</th>
                <th className="px-4 py-3">Standort</th>
                <th className="px-4 py-3">Termin</th>
                <th className="px-4 py-3">Berater</th>
                <th className="px-4 py-3">Positionen</th>
              </tr>
            </thead>
            <tbody className="divide-y">
              {orders.map((order) => (
                <tr key={order.id} className="hover:bg-gray-50">
                  <td className="px-4 py-3">
                    <Link
                      href={`/orders/${order.id}`}
                      className="font-medium text-brand-600 hover:underline"
                    >
                      {order.order_number}
                    </Link>
                  </td>
                  <td className="px-4 py-3">
                    <StatusBadge status={order.status} />
                  </td>
                  <td className="px-4 py-3">{order.location_id}</td>
                  <td className="px-4 py-3">{order.scheduled_date || '-'}</td>
                  <td className="px-4 py-3">{order.advisor_id || '-'}</td>
                  <td className="px-4 py-3">{order.positions?.length || 0}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
```

- [ ] **Step 5: Create new order page**

Write `frontend/src/app/(authenticated)/orders/new/page.tsx`:

```tsx
import { OrderForm } from '@/components/orders/order-form'

export default function NewOrderPage() {
  return (
    <div>
      <h1 className="mb-6 text-2xl font-bold">Neuer Auftrag</h1>
      <OrderForm />
    </div>
  )
}
```

- [ ] **Step 6: Create order detail page**

Write `frontend/src/app/(authenticated)/orders/[id]/page.tsx`:

```tsx
'use client'

import { useParams, useRouter } from 'next/navigation'
import { ArrowLeft } from 'lucide-react'
import { useOrder, useUpdateOrder } from '@/hooks/use-orders'
import { StatusBadge } from '@/components/shared/status-badge'
import { PositionList } from '@/components/orders/position-list'
import type { OrderStatus } from '@/types/order'

const NEXT_STATUS: Partial<Record<OrderStatus, OrderStatus>> = {
  appointment: 'prepared',
  prepared: 'dispatched',
  dispatched: 'checked_in',
  checked_in: 'in_progress',
  in_progress: 'completed',
  qa: 'completed',
  completed: 'picked_up',
}

export default function OrderDetailPage() {
  const { id } = useParams<{ id: string }>()
  const router = useRouter()
  const { data: order, isLoading } = useOrder(id)
  const updateOrder = useUpdateOrder()

  if (isLoading) return <p className="text-gray-400">Laden...</p>
  if (!order) return <p className="text-red-500">Auftrag nicht gefunden.</p>

  const nextStatus = NEXT_STATUS[order.status]

  function advanceStatus() {
    if (!nextStatus) return
    updateOrder.mutate({ id: order.id, status: nextStatus })
  }

  return (
    <div className="max-w-3xl">
      <button
        onClick={() => router.push('/orders')}
        className="mb-4 flex items-center gap-1 text-sm text-gray-500 hover:text-gray-700"
      >
        <ArrowLeft className="h-4 w-4" /> Zurueck
      </button>

      <div className="mb-6 flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-bold">{order.order_number}</h1>
          <p className="mt-1 text-sm text-gray-500">
            {order.location_id} | {order.scheduled_date || 'Kein Termin'} | Berater: {order.advisor_id || '-'}
          </p>
        </div>
        <div className="flex items-center gap-3">
          <StatusBadge status={order.status} />
          {nextStatus && (
            <button
              onClick={advanceStatus}
              disabled={updateOrder.isPending}
              className="rounded-lg bg-brand-600 px-3 py-1.5 text-sm text-white hover:bg-brand-700 disabled:opacity-50"
            >
              → {nextStatus.replace('_', ' ')}
            </button>
          )}
        </div>
      </div>

      {order.notes && (
        <div className="mb-6 rounded-lg border bg-white p-4">
          <h3 className="mb-1 text-sm font-semibold text-gray-500">Notizen</h3>
          <p className="text-sm">{order.notes}</p>
        </div>
      )}

      <PositionList orderId={order.id} positions={order.positions} />
    </div>
  )
}
```

- [ ] **Step 7: Commit**

```bash
cd /opt/drive-dms
git add frontend/
git commit -m "feat(frontend): order list, create, detail pages with position management"
```

---

### Task 17: Frontend — Kanban Board

**Files:**
- Create: `frontend/src/components/orders/order-card.tsx`
- Create: `frontend/src/components/orders/kanban-board.tsx`
- Create: `frontend/src/app/(authenticated)/orders/kanban/page.tsx`

- [ ] **Step 1: Create order card component**

Write `frontend/src/components/orders/order-card.tsx`:

```tsx
import Link from 'next/link'
import type { Order } from '@/types/order'

export function OrderCard({ order }: { order: Order }) {
  const totalMinutes = order.positions.reduce((sum, p) => sum + p.target_minutes, 0)
  const hours = Math.floor(totalMinutes / 60)
  const mins = totalMinutes % 60

  return (
    <Link
      href={`/orders/${order.id}`}
      className="block rounded-lg border bg-white p-3 shadow-sm transition-shadow hover:shadow-md"
    >
      <div className="mb-1 flex items-center justify-between">
        <span className="text-sm font-semibold">{order.order_number}</span>
        {order.priority > 0 && (
          <span className="rounded bg-red-100 px-1.5 py-0.5 text-xs text-red-600">
            Prio {order.priority}
          </span>
        )}
      </div>

      <p className="text-xs text-gray-500">
        {order.scheduled_date || 'Kein Termin'}
      </p>

      {order.positions.length > 0 && (
        <div className="mt-2 space-y-1">
          {order.positions.slice(0, 3).map((pos) => (
            <p key={pos.id} className="truncate text-xs text-gray-600">
              {pos.description}
            </p>
          ))}
          {order.positions.length > 3 && (
            <p className="text-xs text-gray-400">
              +{order.positions.length - 3} weitere
            </p>
          )}
        </div>
      )}

      <div className="mt-2 flex items-center justify-between text-xs text-gray-400">
        <span>{order.advisor_id || '-'}</span>
        <span>
          {hours > 0 && `${hours}h `}{mins > 0 && `${mins}m`}
        </span>
      </div>
    </Link>
  )
}
```

- [ ] **Step 2: Create kanban board component**

Write `frontend/src/components/orders/kanban-board.tsx`:

```tsx
'use client'

import { useOrders } from '@/hooks/use-orders'
import { OrderCard } from './order-card'
import { ORDER_STATUS_LABELS, type OrderStatus } from '@/types/order'

const KANBAN_COLUMNS: OrderStatus[] = [
  'appointment',
  'prepared',
  'dispatched',
  'checked_in',
  'in_progress',
  'qa',
  'completed',
]

const COLUMN_COLORS: Record<string, string> = {
  appointment: 'border-t-gray-400',
  prepared: 'border-t-blue-400',
  dispatched: 'border-t-indigo-400',
  checked_in: 'border-t-yellow-400',
  in_progress: 'border-t-orange-400',
  qa: 'border-t-purple-400',
  completed: 'border-t-green-400',
}

export function KanbanBoard() {
  const { data: orders, isLoading } = useOrders()

  if (isLoading) return <p className="text-gray-400">Laden...</p>

  const grouped = KANBAN_COLUMNS.reduce(
    (acc, status) => {
      acc[status] = orders?.filter((o) => o.status === status) || []
      return acc
    },
    {} as Record<OrderStatus, typeof orders>
  )

  return (
    <div className="flex gap-4 overflow-x-auto pb-4">
      {KANBAN_COLUMNS.map((status) => (
        <div
          key={status}
          className={`w-64 flex-shrink-0 rounded-lg border-t-4 bg-gray-50 ${COLUMN_COLORS[status]}`}
        >
          <div className="flex items-center justify-between px-3 py-2">
            <h3 className="text-sm font-semibold">{ORDER_STATUS_LABELS[status]}</h3>
            <span className="rounded-full bg-gray-200 px-2 py-0.5 text-xs font-medium">
              {grouped[status]?.length || 0}
            </span>
          </div>

          <div className="space-y-2 p-2">
            {grouped[status]?.map((order) => (
              <OrderCard key={order!.id} order={order!} />
            ))}
          </div>
        </div>
      ))}
    </div>
  )
}
```

- [ ] **Step 3: Create kanban page**

Write `frontend/src/app/(authenticated)/orders/kanban/page.tsx`:

```tsx
import { KanbanBoard } from '@/components/orders/kanban-board'

export default function KanbanPage() {
  return (
    <div>
      <h1 className="mb-6 text-2xl font-bold">Kanban</h1>
      <KanbanBoard />
    </div>
  )
}
```

- [ ] **Step 4: Commit**

```bash
cd /opt/drive-dms
git add frontend/
git commit -m "feat(frontend): Kanban board with status columns and order cards"
```

---

### Task 18: Frontend — Resource Management Page

**Files:**
- Create: `frontend/src/app/(authenticated)/resources/page.tsx`

- [ ] **Step 1: Create resource management page**

Write `frontend/src/app/(authenticated)/resources/page.tsx`:

```tsx
'use client'

import { useState } from 'react'
import { Plus, Wrench, ArrowUpDown } from 'lucide-react'
import { useResources } from '@/hooks/use-resources'
import { api } from '@/lib/api-client'
import { useQueryClient } from '@tanstack/react-query'
import type { Resource, ResourceType } from '@/types/resource'

export default function ResourcesPage() {
  const { data: resources, isLoading } = useResources()
  const qc = useQueryClient()
  const [showForm, setShowForm] = useState(false)
  const [name, setName] = useState('')
  const [type, setType] = useState<ResourceType>('mechanic')

  const mechanics = resources?.filter((r) => r.type === 'mechanic') || []
  const lifts = resources?.filter((r) => r.type === 'lift') || []

  async function handleAdd(e: React.FormEvent) {
    e.preventDefault()
    await api.post('/workshop/resources', {
      name,
      type,
      location_id: 'deg-opel',
      qualifications: [],
      working_hours: {
        mon: '07:00-16:00',
        tue: '07:00-16:00',
        wed: '07:00-16:00',
        thu: '07:00-16:00',
        fri: '07:00-14:00',
      },
    })
    qc.invalidateQueries({ queryKey: ['resources'] })
    setName('')
    setShowForm(false)
  }

  if (isLoading) return <p className="text-gray-400">Laden...</p>

  return (
    <div>
      <div className="mb-6 flex items-center justify-between">
        <h1 className="text-2xl font-bold">Ressourcen</h1>
        <button
          onClick={() => setShowForm(!showForm)}
          className="flex items-center gap-2 rounded-lg bg-brand-600 px-4 py-2 text-sm text-white hover:bg-brand-700"
        >
          <Plus className="h-4 w-4" /> Hinzufuegen
        </button>
      </div>

      {showForm && (
        <form onSubmit={handleAdd} className="mb-6 flex gap-3 rounded-lg border bg-white p-4">
          <input
            type="text"
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="Name"
            className="flex-1 rounded-lg border px-3 py-2 text-sm"
            required
            autoFocus
          />
          <select
            value={type}
            onChange={(e) => setType(e.target.value as ResourceType)}
            className="rounded-lg border px-3 py-2 text-sm"
          >
            <option value="mechanic">Monteur</option>
            <option value="lift">Hebebuehne</option>
          </select>
          <button type="submit" className="rounded-lg bg-brand-600 px-4 py-2 text-sm text-white">
            Anlegen
          </button>
        </form>
      )}

      <div className="grid grid-cols-2 gap-6">
        <div>
          <h2 className="mb-3 flex items-center gap-2 text-lg font-semibold">
            <Wrench className="h-5 w-5" /> Monteure ({mechanics.length})
          </h2>
          <div className="space-y-2">
            {mechanics.map((r) => (
              <ResourceCard key={r.id} resource={r} />
            ))}
          </div>
        </div>

        <div>
          <h2 className="mb-3 flex items-center gap-2 text-lg font-semibold">
            <ArrowUpDown className="h-5 w-5" /> Hebebuehnen ({lifts.length})
          </h2>
          <div className="space-y-2">
            {lifts.map((r) => (
              <ResourceCard key={r.id} resource={r} />
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}

function ResourceCard({ resource }: { resource: Resource }) {
  return (
    <div className="flex items-center gap-3 rounded-lg border bg-white p-3">
      <div
        className="h-3 w-3 rounded-full"
        style={{ backgroundColor: resource.color }}
      />
      <div className="flex-1">
        <p className="text-sm font-medium">{resource.name}</p>
        {resource.qualifications.length > 0 && (
          <p className="text-xs text-gray-400">
            {resource.qualifications.join(', ')}
          </p>
        )}
      </div>
      <span className="text-xs text-gray-400">{resource.location_id}</span>
    </div>
  )
}
```

- [ ] **Step 2: Commit**

```bash
cd /opt/drive-dms
git add frontend/
git commit -m "feat(frontend): resource management page (mechanics + lifts)"
```

---

### Task 19: CI/CD — GitHub Actions Workflow

**Files:**
- Create: `.github/workflows/ci.yml`

- [ ] **Step 1: Create CI workflow**

Write `/opt/drive-dms/.github/workflows/ci.yml`:

```yaml
name: CI

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  gateway-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      - name: Install dependencies
        working-directory: services/gateway
        run: pip install -r requirements.txt
      - name: Lint
        working-directory: services/gateway
        run: ruff check app/ tests/
      - name: Test
        working-directory: services/gateway
        run: pytest tests/ -v

  workshop-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      - name: Install dependencies
        working-directory: services/workshop
        run: pip install -r requirements.txt
      - name: Lint
        working-directory: services/workshop
        run: ruff check app/ tests/
      - name: Test
        working-directory: services/workshop
        run: pytest tests/ -v

  frontend-lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '20'
      - name: Install dependencies
        working-directory: frontend
        run: npm install
      - name: Lint
        working-directory: frontend
        run: npm run lint
      - name: Type check
        working-directory: frontend
        run: npx tsc --noEmit

  docker-build:
    runs-on: ubuntu-latest
    needs: [gateway-tests, workshop-tests, frontend-lint]
    steps:
      - uses: actions/checkout@v4
      - name: Build all images
        run: docker compose build
```

- [ ] **Step 2: Commit**

```bash
cd /opt/drive-dms
git add .github/
git commit -m "ci: GitHub Actions workflow for gateway, workshop, frontend"
```

---

### Task 20: Full-Stack Integration Test

- [ ] **Step 1: Rebuild and start all services**

```bash
cd /opt/drive-dms
docker compose down -v
docker compose build
docker compose up -d
```

- [ ] **Step 2: Wait for services and run smoke tests**

```bash
# Wait for health
sleep 10

# Gateway health
curl -s http://localhost/api/health | python3 -m json.tool

# Login
TOKEN=$(curl -s -X POST http://localhost/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "dev-admin", "password": "test"}' | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")
echo "Token: ${TOKEN:0:20}..."

# Create a resource
curl -s -X POST http://localhost/api/v1/workshop/resources \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name": "Max Mueller", "type": "mechanic", "location_id": "deg-opel", "qualifications": ["HV-Schein"], "working_hours": {"mon": "07:00-16:00"}, "color": "#3B82F6"}' | python3 -m json.tool

# Create an order
curl -s -X POST http://localhost/api/v1/workshop/orders \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"location_id": "deg-opel", "scheduled_date": "2026-04-10", "advisor_id": "huber", "notes": "Inspektion 40.000km"}' | python3 -m json.tool

# List orders
curl -s http://localhost/api/v1/workshop/orders \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool
```

Expected: All requests return valid JSON with correct data.

- [ ] **Step 3: Open frontend in browser**

Navigate to `http://<hetzner-ip>` — should see the login page. Login with `dev-admin` / `any password`. Should see the dashboard with sidebar navigation.

- [ ] **Step 4: Final commit**

```bash
cd /opt/drive-dms
git add -A
git commit -m "chore: Phase 0 + Phase 1 complete — gateway, workshop service, React frontend"
```

---

## Summary

**Phase 0 (Tasks 1-11):** Repository, Docker Compose, Gateway (JWT + LDAP auth + proxy), Workshop service skeleton, Frontend (Next.js + login + layout), database init.

**Phase 1 (Tasks 12-20):** Order + Position + Resource models, OrderService with status machine, full CRUD APIs, React pages (order list, detail, create, Kanban, resource management), CI/CD pipeline, full-stack integration test.

**Total: 20 tasks, ~95 steps.**

**What's ready after this plan:**
- Login works (dev users + LDAP)
- Serviceberater can create orders, add positions, advance status
- Kanban board shows all orders grouped by status
- Resources (mechanics + lifts) can be managed
- All APIs are tested
- Docker Compose runs the full stack
- CI pipeline validates on every push

**What comes next (Phase 2):** Werkstattplaner timeline with @dnd-kit, drag&drop scheduling, WebSocket live updates.
