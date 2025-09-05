@echo off
echo "=== Starting Build Process ==="

:: Step 1: Activate virtual environment
call venv\Scripts\activate

:: Step 2: Upgrade pip and install dependencies
python -m pip install --upgrade pip || echo pip upgrade skipped
pip install -r requirement.txt

:: Step 3: Force SQLite for local build
set USE_SQLITE=1

:: Step 3: Apply database migrations
python manage.py makemigrations
python manage.py migrate

echo "=== Build Completed Successfully ==="

:: Step 4: Run application
python manage.py runserver

pause