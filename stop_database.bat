@echo off
echo ============================================================
echo Stopping Design Agent Database Services
echo ============================================================
echo.

echo Stopping PostgreSQL...
docker stop postgres-anyon

echo Stopping Redis...
docker stop redis-anyon

echo.
echo ============================================================
echo Database services stopped!
echo ============================================================
echo.
echo To start again, run: start_database.bat
echo To remove completely, run:
echo   docker rm postgres-anyon redis-anyon
echo.

pause
