param()

$ErrorActionPreference = "SilentlyContinue"

$stdin = [Console]::In.ReadToEnd()
$promptText = ""
if ($stdin) {
    try {
        $payload = $stdin | ConvertFrom-Json
        $promptText = @(
            $payload.prompt
            $payload.message
            $payload.text
            $payload.userPrompt
        ) -join " "
    } catch {
        Write-Error "Cline UserPromptSubmit hook received invalid JSON input; continuing advisory-only."
    }
}

$highImpactPatterns = @(
    "sync_agent_configs.py",
    "orchestrate_local_agent_sync.py apply",
    "port_workspace_safety_config.py"
)

$message = ""
foreach ($pattern in $highImpactPatterns) {
    if ($promptText -match [regex]::Escape($pattern)) {
        $message = "AIS CR approval reminder: high-impact sync or workspace-safety scripts require explicit human approval and dry-run/inspect evidence before apply."
        break
    }
}

[pscustomobject]@{
    cancel = $false
    contextModification = $message
    errorMessage = ""
} | ConvertTo-Json -Compress
