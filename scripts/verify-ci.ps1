# Builds and destroys only a fresh, explicitly named CI project.
param(
    [Parameter(Mandatory = $true)]
    [ValidatePattern('^career-ci-[a-z0-9][a-z0-9-]{0,45}$')]
    [string]$ProjectName
)
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path $PSScriptRoot -Parent
$composeFile = Join-Path $projectRoot 'compose.ci.yaml'
$emptyEnv = [IO.Path]::GetTempFileName()
$started = $false
$passed = $false

function Invoke-CiCompose {
    & docker compose --env-file $emptyEnv --file $composeFile --project-name $ProjectName @args
    if ($LASTEXITCODE -ne 0) { throw "CI Compose command failed: $args" }
}

try {
    # Refuse existing resources: cleanup must never touch a previous environment.
    $containers = & docker ps -aq --filter "label=com.docker.compose.project=$ProjectName"
    if ($LASTEXITCODE -ne 0) { throw 'Docker is not available.' }
    $volumes = & docker volume ls -q --filter "label=com.docker.compose.project=$ProjectName"
    if ($LASTEXITCODE -ne 0) { throw 'Could not inspect existing volumes.' }
    if ($containers -or $volumes) { throw 'Choose a fresh CI project name; existing resources were found.' }

    Invoke-CiCompose config --quiet
    $started = $true
    Invoke-CiCompose build api
    Invoke-CiCompose up -d --wait --wait-timeout 180 db
    Invoke-CiCompose run --rm --no-deps api alembic upgrade head
    $testRunner = @"
import os, sys, unittest
from sqlalchemy.engine import make_url
url = make_url(os.environ['PROFILE_TEST_DATABASE_URL'])
assert url.get_backend_name() == 'postgresql'
assert url.database == 'career_profile_test_ci'
suite = unittest.defaultTestLoader.discover('tests', top_level_dir='.')
result = unittest.TextTestRunner(verbosity=2).run(suite)
if not result.testsRun or result.skipped:
    raise SystemExit('CI requires at least one test and no skipped PostgreSQL tests')
sys.exit(0 if result.wasSuccessful() else 1)
"@
    Invoke-CiCompose run --rm --no-deps api python -c $testRunner
    Invoke-CiCompose up -d --wait --wait-timeout 180 api

    # Discover profile probes now and job/extraction probes after the earlier PR merges.
    $probes = Get-ChildItem (Join-Path $projectRoot 'tests') -Filter '*persistence_probe.py' | Sort-Object Name
    if (-not $probes) { throw 'No persistence probes were found.' }
    foreach ($probe in $probes) {
        Invoke-CiCompose run --rm --no-deps api python -m "tests.$($probe.BaseName)" seed
    }
    Invoke-CiCompose restart db api
    Invoke-CiCompose up -d --wait --wait-timeout 180 db api
    foreach ($probe in $probes) {
        Invoke-CiCompose run --rm --no-deps api python -m "tests.$($probe.BaseName)" check
    }
    $healthCheck = @"
import json, urllib.request
from pathlib import Path
response = json.load(urllib.request.urlopen('http://localhost:8000/health/ready', timeout=15))
assert response['status'] == 'ready' and response['pgvector']
for page in ['/profiles'] + (['/jobs'] if Path('app/web/jobs.html').exists() else []):
    assert urllib.request.urlopen('http://localhost:8000' + page, timeout=15).status == 200
print('PASS: API readiness, pgvector and web pages after restart')
"@
    Invoke-CiCompose exec -T api python -c $healthCheck
    $passed = $true
    Write-Host 'PASS: isolated build, migrations, PostgreSQL tests, API and restart persistence.'
} finally {
    try {
        if ($started) {
            if (-not $passed) {
                & docker compose --env-file $emptyEnv --file $composeFile --project-name $ProjectName logs --no-color --tail 100
            }
            # This project is CI-only, was absent before this run, and has no shared volumes.
            Invoke-CiCompose down --volumes --remove-orphans
        }
    } finally {
        Remove-Item -LiteralPath $emptyEnv -ErrorAction SilentlyContinue
    }
}
