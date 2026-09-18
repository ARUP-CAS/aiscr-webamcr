param()

$ErrorActionPreference = "SilentlyContinue"

$stdin = [Console]::In.ReadToEnd()
if ($stdin) {
    try {
        $null = $stdin | ConvertFrom-Json
    } catch {
        Write-Error "Cline TaskComplete hook received invalid JSON input; continuing advisory-only."
    }
}

$message = ""
try {
    $changed = git status --short -- .agents .cursor .claude .codex .gemini .clinerules 2>$null
    if ($changed) {
        $message = "AIS CR close-out reminder: this session changed governed assistant/config paths; update the rolling usage log and run the relevant validation checks before reporting completion."
    }
} catch {
    Write-Error "Cline TaskComplete hook could not inspect git status; continuing advisory-only."
}

[pscustomobject]@{
    cancel = $false
    contextModification = $message
    errorMessage = ""
} | ConvertTo-Json -Compress
