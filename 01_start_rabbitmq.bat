@echo off
cd /d "%~dp0"
echo.
echo =====================================
echo   Starting RabbitMQ via Docker
echo =====================================
echo.
echo Make sure Docker Desktop is running...
echo.
echo [Press CTRL+C to stop RabbitMQ manually when done.]
echo.
REM Add timestamp
echo [%date% %time%] Launching RabbitMQ...
docker run -it --rm --name rabbitmq -p 5672:5672 -p 15672:15672 rabbitmq:3-management
