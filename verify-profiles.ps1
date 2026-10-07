$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot

function Invoke-Compose {
    & docker compose @args
    if ($LASTEXITCODE -ne 0) { throw "Docker Compose failed: $args" }
}

Invoke-Compose build api
Invoke-Compose up -d --wait --wait-timeout 240 db
# Explicit upgrade of the existing database; never remove the persistent volume.
Invoke-Compose run --rm --no-deps api alembic upgrade head
Invoke-Compose up -d --wait --wait-timeout 240 api

$testDatabase = 'career_profile_test_' + [guid]::NewGuid().ToString('N')
$databaseCreated = $false
try {
    Invoke-Compose exec -T db psql -v ON_ERROR_STOP=1 -U career_os -d career_intelligence -c "CREATE DATABASE $testDatabase;"
    $databaseCreated = $true
    # Derive credentials inside the container so passwords never enter shell output.
    $testPrefix = @'
import os, subprocess, sys
from sqlalchemy.engine import make_url
url = make_url(os.environ['DATABASE_URL']).set(database=sys.argv[1])
env = dict(os.environ, DATABASE_URL=url.render_as_string(hide_password=False), PROFILE_TEST_DATABASE_URL=url.render_as_string(hide_password=False))
subprocess.run(sys.argv[2:], env=env, check=True)
'@
    Invoke-Compose run --rm --no-deps api python -c $testPrefix $testDatabase alembic upgrade head
    Invoke-Compose run --rm --no-deps api python -c $testPrefix $testDatabase python -m unittest tests.test_profiles -v
    Invoke-Compose run --rm --no-deps api python -c $testPrefix $testDatabase python -m tests.persistence_probe seed
    Invoke-Compose restart db api
    Invoke-Compose up -d --wait --wait-timeout 240
    Invoke-Compose run --rm --no-deps api python -c $testPrefix $testDatabase python -m tests.persistence_probe check
    $ready = Invoke-RestMethod 'http://127.0.0.1:8000/health/ready'
    if ($ready.status -ne 'ready') { throw 'API readiness failed' }
    Write-Host 'PASS: profile API, version history, owner isolation and restart persistence.'
} finally {
    # Drop only the generated, disposable test database; preserve the real database.
    if ($databaseCreated -and $testDatabase -match '^career_profile_test_[0-9a-f]{32}$') {
        & docker compose exec -T db psql -v ON_ERROR_STOP=1 -U career_os -d career_intelligence -c "DROP DATABASE $testDatabase WITH (FORCE);"
        if ($LASTEXITCODE -ne 0) { Write-Warning "Could not remove disposable database $testDatabase" }
    }
}
