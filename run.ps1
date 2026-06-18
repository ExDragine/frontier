if (-not $env:HF_ENDPOINT) {
    $env:HF_ENDPOINT = "https://hf-mirror.com"
}

.venv/Scripts/Activate.ps1

do {
    uv run nb run
    sleep 5
}while($true)
