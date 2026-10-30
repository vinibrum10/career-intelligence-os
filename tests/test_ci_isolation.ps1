# No real Docker calls: prove CI refuses existing resources and scopes failure cleanup.
$ErrorActionPreference = 'Stop'
$ciScript = Join-Path (Split-Path $PSScriptRoot -Parent) 'scripts/verify-ci.ps1'
$global:careerCiIsolation = @{ scenario = ''; calls = [Collections.Generic.List[object]]::new() }
function docker {
    $global:careerCiIsolation.calls.Add([string[]]$args)
    $global:LASTEXITCODE = 0
    if ($args[0] -eq 'ps' -and $global:careerCiIsolation.scenario -eq 'existing-container') { return 'existing-container-id' }
    if ($args[0] -eq 'volume' -and $global:careerCiIsolation.scenario -eq 'existing-volume') { return 'existing-volume-name' }
    if ($args[0] -eq 'compose' -and $args -contains 'build') { $global:LASTEXITCODE = 1 }
}
try {
    foreach ($scenario in @('existing-container', 'existing-volume', 'build-failure', 'invalid-name')) {
        $global:careerCiIsolation.scenario = $scenario
        $global:careerCiIsolation.calls.Clear()
        $project = if ($scenario -eq 'invalid-name') { 'production' } else { "career-ci-isolation-$scenario" }
        $failure = $null
        try { & $ciScript -ProjectName $project } catch { $failure = $_ }
        if (-not $failure) { throw "Expected refusal or failure: $scenario" }
        $composeCalls = @($global:careerCiIsolation.calls | Where-Object { $_[0] -eq 'compose' })
        if ($scenario -eq 'build-failure') {
            if ($failure.Exception.Message -notlike '*CI Compose command failed*') { throw $failure }
            $cleanup = @($composeCalls | Where-Object { $_ -contains 'down' })
            if ($cleanup.Count -ne 1 -or $cleanup[0] -notcontains '--volumes') { throw 'Missing scoped cleanup after build failure' }
            foreach ($call in $composeCalls) {
                $projectIndex = [array]::IndexOf($call, '--project-name')
                $fileIndex = [array]::IndexOf($call, '--file')
                if ($projectIndex -lt 0 -or $call[$projectIndex + 1] -ne $project -or
                    $fileIndex -lt 0 -or [IO.Path]::GetFileName($call[$fileIndex + 1]) -ne 'compose.ci.yaml' -or
                    $call -notcontains '--env-file') { throw 'CI escaped its isolated configuration' }
            }
        } elseif ($composeCalls.Count) {
            throw "Existing resources or invalid name must not be changed: $scenario"
        }
        if ($scenario -eq 'invalid-name' -and $global:careerCiIsolation.calls.Count) { throw 'Invalid name reached Docker' }
        Write-Host "PASS: CI isolation $scenario"
    }
} finally {
    Remove-Item Function:docker -ErrorAction SilentlyContinue
    Remove-Variable careerCiIsolation -Scope Global
}
