param()

$ErrorActionPreference = "SilentlyContinue"

$stdin = [Console]::In.ReadToEnd()
if ($stdin) {
    try {
        $null = $stdin | ConvertFrom-Json
    } catch {
        Write-Error "Cline TaskStart hook received invalid JSON input; continuing advisory-only."
    }
}

$message = @(
    "AIS CR planning baseline: before mutating work, confirm branch/upstream state, read the active OpenSpec change artifacts, and keep sibling apply steps dry-run/approval gated."
) -join " "

[pscustomobject]@{
    cancel = $false
    contextModification = $message
    errorMessage = ""
} | ConvertTo-Json -Compress
