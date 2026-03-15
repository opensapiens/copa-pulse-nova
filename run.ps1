# CopaPulse - PowerShell launcher for Windows
# Starts both the FastAPI backend and React frontend

Write-Host ""
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "  CopaPulse Nova - Starting Services    " -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host ""

# Check if .env exists
if (-not (Test-Path ".env")) {
    Write-Host "❌ No .env file found!" -ForegroundColor Red
    Write-Host "📝 Please copy .env.example to .env and configure your credentials:" -ForegroundColor Yellow
    Write-Host "   - AWS_ACCESS_KEY_ID" -ForegroundColor Yellow
    Write-Host "   - AWS_SECRET_ACCESS_KEY" -ForegroundColor Yellow
    Write-Host "   - AWS_DEFAULT_REGION" -ForegroundColor Yellow
    Write-Host "   - REDDIT_CLIENT_ID (optional)" -ForegroundColor Yellow
    Write-Host "   - REDDIT_CLIENT_SECRET (optional)" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Run: Copy-Item .env.example .env" -ForegroundColor Green
    Write-Host ""
    exit 1
}

# Check if virtual environment is activated
if (-not $env:VIRTUAL_ENV) {
    Write-Host "⚠️  Virtual environment not activated!" -ForegroundColor Yellow
    Write-Host "Run: .\.venv\Scripts\Activate.ps1" -ForegroundColor Green
    Write-Host ""
    exit 1
}

Write-Host "🚀 Starting FastAPI Backend (Port 8000)..." -ForegroundColor Green
$backend = Start-Process -FilePath "python" -ArgumentList "-m", "uvicorn", "api:app", "--reload", "--port", "8000" -PassThru -WindowStyle Normal

Start-Sleep -Seconds 2

Write-Host "🚀 Starting React Frontend (Port 5173)..." -ForegroundColor Green
$frontend = Start-Process -FilePath "powershell" -ArgumentList "-NoExit", "-Command", "cd frontend; npm run dev" -PassThru -WindowStyle Normal

Write-Host ""
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "✅ Both servers are running!" -ForegroundColor Green
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "▶️  Backend API:  " -NoNewline -ForegroundColor White
Write-Host "http://localhost:8000" -ForegroundColor Blue
Write-Host "▶️  API Docs:     " -NoNewline -ForegroundColor White
Write-Host "http://localhost:8000/docs" -ForegroundColor Blue
Write-Host "▶️  Frontend UI:  " -NoNewline -ForegroundColor White
Write-Host "http://localhost:5173" -ForegroundColor Blue
Write-Host ""
Write-Host "Press Ctrl+C to stop this script (servers will keep running)" -ForegroundColor Yellow
Write-Host "To stop servers, close their terminal windows manually" -ForegroundColor Yellow
Write-Host ""

# Keep script running
try {
    while ($true) {
        Start-Sleep -Seconds 1
    }
} finally {
    Write-Host ""
    Write-Host "Script stopped. Servers are still running in separate windows." -ForegroundColor Yellow
}
