# Isolated regression checks: all Docker and HTTP calls are replaced with mocks.
$ErrorActionPreference = 'Stop'
$source = Join-Path (Split-Path $PSScriptRoot -Parent) 'verify.ps1'
$originalLocation = Get-Location
$sandbox = Join-Path ([IO.Path]::GetTempPath()) ('career-verify-test-' + [guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Path $sandbox | Out-Null
$global:careerVerifyTestState = @{ scenario = $null; dockerCalls = 0; probeId = $null }
try {
    Copy-Item -LiteralPath $source -Destination (Join-Path $sandbox 'verify.ps1')
    function docker {
        $global:careerVerifyTestState.dockerCalls++
        $global:LASTEXITCODE = 0
        if ($global:careerVerifyTestState.scenario -eq 'compose-failure' -or
            ($global:careerVerifyTestState.scenario -eq 'ps-failure' -and $args[-1] -eq 'ps')) {
            $global:LASTEXITCODE = 1
            return
        }
        $command = $args[-1]
        if ($command -match "INSERT INTO.*VALUES \('([^']+)'\)") {
            $global:careerVerifyTestState.probeId = $Matches[1]
        }
        if ($command -match '^SELECT id') {
            if ($global:careerVerifyTestState.scenario -eq 'probe-mismatch') { return 'wrong-id' }
            return $global:careerVerifyTestState.probeId
        }
    }
    function Invoke-RestMethod {
        if ($global:careerVerifyTestState.scenario -eq 'http-failure') { throw 'Mock HTTP failure' }
        return @{ status = 'ready'; database = 'connected'; pgvector = 'mock' }
    }
    foreach ($scenario in @('missing-env', 'compose-failure', 'http-failure', 'probe-mismatch', 'ps-failure', 'success')) {
        $global:careerVerifyTestState.scenario = $scenario
        $global:careerVerifyTestState.dockerCalls = 0
        $global:careerVerifyTestState.probeId = $null
        $report = Join-Path $sandbox 'verification.json'
        $envFile = Join-Path $sandbox '.env'
        '{"persistence_passed":true,"verified_at":"old"}' | Set-Content -LiteralPath $report
        if ($global:careerVerifyTestState.scenario -eq 'missing-env') {
            if (Test-Path -LiteralPath $envFile) { Remove-Item -LiteralPath $envFile }
        } else {
            'MOCK_ONLY=1' | Set-Content -LiteralPath $envFile
        }
        $failed = $false
        try { & (Join-Path $sandbox 'verify.ps1') } catch { $failed = $true }
        if ($global:careerVerifyTestState.scenario -eq 'success') {
            if ($failed) { throw 'Success scenario unexpectedly failed' }
            $result = Get-Content -LiteralPath $report -Raw | ConvertFrom-Json
            if ($result.persistence_passed -ne $true -or $result.verified_at -eq 'old' -or
                $result.persisted_probe_id -ne $global:careerVerifyTestState.probeId) {
                throw 'Success report does not describe the current probe'
            }
        } else {
            if (-not $failed) { throw "Expected failure: $($global:careerVerifyTestState.scenario)" }
            if (Test-Path -LiteralPath $report) { throw "Stale success survived: $($global:careerVerifyTestState.scenario)" }
            if ($global:careerVerifyTestState.scenario -eq 'missing-env' -and $global:careerVerifyTestState.dockerCalls -ne 0) {
                throw 'Docker was called despite missing .env'
            }
        }
        Write-Host "PASS: $($global:careerVerifyTestState.scenario)"
    }
} finally {
    Remove-Variable -Name careerVerifyTestState -Scope Global -ErrorAction SilentlyContinue
    Set-Location $originalLocation
    # Delete only this test's verified, unique temporary directory.
    $resolved = [IO.Path]::GetFullPath($sandbox)
    $tempRoot = [IO.Path]::GetFullPath([IO.Path]::GetTempPath())
    if ($resolved.StartsWith($tempRoot, [StringComparison]::OrdinalIgnoreCase) -and
        (Split-Path $resolved -Leaf) -match '^career-verify-test-[0-9a-f]{32}$') {
        Remove-Item -LiteralPath $resolved -Recurse -Force
    }
}
