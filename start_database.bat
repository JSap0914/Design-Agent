@echo off
echo ============================================================
echo Starting Design Agent Database Services
echo ============================================================
echo.

echo [1/3] Starting PostgreSQL...
docker run --name postgres-anyon ^
  -e POSTGRES_USER=user ^
  -e POSTGRES_PASSWORD=password ^
  -e POSTGRES_DB=anyon_db ^
  -p 5432:5432 ^
  -d postgres:15

if %errorlevel% neq 0 (
    echo.
    echo Container already exists. Trying to start existing container...
    docker start postgres-anyon
)

echo.
echo [2/3] Waiting for PostgreSQL to be ready...
timeout /t 5 /nobreak >nul

echo.
echo [3/3] Starting Redis...
docker run --name redis-anyon ^
  -p 6379:6379 ^
  -d redis:7

if %errorlevel% neq 0 (
    echo.
    echo Container already exists. Trying to start existing container...
    docker start redis-anyon
)

echo.
echo ============================================================
echo Database services started!
echo ============================================================
echo.
echo PostgreSQL: localhost:5432
echo   Database: anyon_db
echo   User: user
echo   Password: password
echo.
echo Redis: localhost:6379
echo.
echo Next step: Run migrations
echo   alembic upgrade head
echo.
echo Then verify:
echo   python verify_db.py
echo.

pause
