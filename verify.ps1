$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot

function Invoke-Compose {
    & docker compose @args
    if ($LASTEXITCODE -ne 0) { throw "Docker Compose failed: $args" }
}

if (-not (Test-Path -LiteralPath '.env')) {
    throw 'Create .env from .env.example with a random hexadecimal password.'
}
Invoke-Compose up -d --build --wait --wait-timeout 240
$before = Invoke-RestMethod 'http://127.0.0.1:8000/health/ready'
$probeId = [guid]::NewGuid().ToString()
Invoke-Compose exec -T db psql -v ON_ERROR_STOP=1 -U career_os -d career_intelligence -c "INSERT INTO infrastructure.persistence_probe(id) VALUES ('$probeId');"
Invoke-Compose restart db api
Invoke-Compose up -d --wait --wait-timeout 240
$after = Invoke-RestMethod 'http://127.0.0.1:8000/health/ready'
$stored = Invoke-Compose exec -T db psql -v ON_ERROR_STOP=1 -U career_os -d career_intelligence -tAc "SELECT id FROM infrastructure.persistence_probe WHERE id='$probeId';"
if (($stored | Out-String).Trim() -ne $probeId) { throw 'Persistence verification failed.' }
$result = [ordered]@{
    verified_at = (Get-Date).ToString('o')
    before_restart = $before
    after_restart = $after
    persisted_probe_id = $probeId
    persistence_passed = $true
}
$result | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath verification.json -Encoding UTF8
Invoke-Compose ps
Write-Host 'PASS: API, PostgreSQL, pgvector and persistence after restart.'
