$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = New-Object System.Text.UTF8Encoding($false)
$OutputEncoding = [Console]::OutputEncoding
$taskRoot = $PSScriptRoot
if ($env:PROCESSOR_ARCHITECTURE -ne 'AMD64') { throw 'This bundle supports Windows x64. Native Windows ARM64 is not included.' }
$taskLock = Get-Content -LiteralPath (Join-Path $taskRoot 'dependencies.lock.json') -Raw | ConvertFrom-Json
$taskPlatform = 'windows-x64'
$taskRuntime = Join-Path $taskRoot ".runtime/$taskPlatform"
New-Item -ItemType Directory -Force -Path $taskRuntime | Out-Null
$taskGuard = $null
for ($taskAttempt = 0; $taskAttempt -lt 600 -and $null -eq $taskGuard; $taskAttempt++) {
    try { $taskGuard = [IO.File]::Open((Join-Path $taskRuntime 'bootstrap.lock'), 'OpenOrCreate', 'ReadWrite', 'None') }
    catch [IO.IOException] { Start-Sleep -Milliseconds 100 }
}
if ($null -eq $taskGuard) { throw 'Another runtime extraction is still running. Retry shortly.' }
try {
    foreach ($taskKind in @('python', 'java')) {
        $taskEntry = $taskLock.platforms.$taskPlatform.$taskKind
        $taskDestination = Join-Path $taskRuntime $taskKind
        $taskMarker = Join-Path $taskDestination '.archive-sha256'
        if ((Test-Path -LiteralPath $taskMarker) -and (Get-Content -LiteralPath $taskMarker -Raw).Trim() -eq $taskEntry.sha256) { continue }
        $taskArchive = Join-Path $taskRoot $taskEntry.path
        if (-not (Test-Path -LiteralPath $taskArchive)) { throw "Runtime missing: $($taskEntry.path). Download the universal portable release, or run scripts/fetch_dependencies.py with Python 3.11+." }
        $taskStream = [IO.File]::OpenRead($taskArchive)
        $taskHasher = [Security.Cryptography.SHA256]::Create()
        try { $taskHash = [BitConverter]::ToString($taskHasher.ComputeHash($taskStream)).Replace('-', '').ToLowerInvariant() }
        finally { $taskStream.Dispose(); $taskHasher.Dispose() }
        if ($taskHash -ne $taskEntry.sha256) { throw "Checksum mismatch: $($taskEntry.path)" }
        [Console]::Error.WriteLine("Preparing bundled $taskKind; this happens once per platform...")
        $taskStaging = Join-Path $taskRuntime ('.extract-' + $taskKind + '-' + [Guid]::NewGuid().ToString('N'))
        New-Item -ItemType Directory -Path $taskStaging | Out-Null
        if ($taskArchive.EndsWith('.zip')) {
            Add-Type -AssemblyName System.IO.Compression.FileSystem
            [IO.Compression.ZipFile]::ExtractToDirectory($taskArchive, $taskStaging)
        } else {
            # Windows tar can lose non-ANSI characters in absolute arguments.
            # The working directory is Unicode; both arguments are package-relative ASCII.
            Push-Location -LiteralPath $taskRoot
            try {
                $taskRelativeStaging = '.runtime/' + $taskPlatform + '/' + [IO.Path]::GetFileName($taskStaging)
                & tar.exe -xzf $taskEntry.path -C $taskRelativeStaging
                if ($LASTEXITCODE -ne 0) { throw 'Runtime extraction failed.' }
            } finally { Pop-Location }
        }
        [IO.File]::WriteAllText((Join-Path $taskStaging '.archive-sha256'), $taskEntry.sha256)
        if (Test-Path -LiteralPath $taskDestination) { Move-Item -LiteralPath $taskDestination -Destination ($taskDestination + '.previous-' + [Guid]::NewGuid().ToString('N')) }
        Move-Item -LiteralPath $taskStaging -Destination $taskDestination
    }
} finally { $taskGuard.Dispose() }
$taskPython = Join-Path $taskRuntime 'python/python/python.exe'
if (-not (Test-Path -LiteralPath $taskPython)) { throw 'Bundled Python executable not found after extraction.' }
& $taskPython -I -X utf8 (Join-Path $taskRoot 'launcher.py') @args
exit $LASTEXITCODE
