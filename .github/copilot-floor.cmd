REM delivery-version: b257a1a89279be5e17cda3c133aa77b8c4d2706c 2026-11-07T11:18:12+01:00

@echo off
rem GitHub Copilot CLI wrapper carrying the AIS CR irreversible-operation floor.
rem
rem Denial rules take precedence over allow rules, including --allow-all-tools,
rem so the baked flags below hold even when a caller appends permissive options
rem after the prompt. The wrapper is opt-in: invoking `copilot` directly
rem bypasses it, and that bypass is recorded with the rest of the floor's
rem known-open routes. The flags are session-scoped by product design -- there
rem is no persistent tool-rule key, which is the Copilot disparity this
rem wrapper narrows.

where copilot >nul 2>&1
if errorlevel 1 (
  echo copilot-floor could not find the GitHub Copilot CLI on PATH. 1>&2
  exit /b 127
)

copilot ^
  --disable-builtin-mcps ^
  --deny-tool="shell(git push --force:*)" ^
  --deny-tool="shell(git push --force-with-lease:*)" ^
  --deny-tool="shell(git push -f:*)" ^
  --deny-tool="shell(git push --delete:*)" ^
  --deny-tool="shell(git branch -D:*)" ^
  --deny-tool="shell(git branch --force:*)" ^
  --deny-tool="shell(git clean:*)" ^
  --deny-tool="shell(git stash clear:*)" ^
  --deny-tool="shell(gh repo delete:*)" ^
  --deny-tool="shell(rm:-rf /)" ^
  --deny-tool="shell(rm:-fr /)" ^
  --deny-tool="shell(rm:-rf /c)" ^
  --deny-tool="shell(rm:-rf /c/)" ^
  --deny-tool="shell(rm:-rf /d)" ^
  --deny-tool="shell(rm:-rf /d/)" ^
  --deny-tool="shell(format:*)" ^
  --deny-tool="shell(rm:-rf ~)" ^
  --deny-tool="shell(rm:-fr ~)" ^
  --deny-tool="shell(Clear-RecycleBin:*)" ^
  --deny-tool="shell(vssadmin:delete*)" ^
  --deny-tool="shell(wbadmin:delete*)" ^
  --deny-tool="shell(reg:delete*)" ^
  --deny-tool="shell(bcdedit:*)" ^
  --deny-tool="shell(cipher:/w*)" ^
  --deny-tool="shell(sdelete:*)" ^
  --deny-tool="shell(dd:*)" ^
  --deny-tool="shell(robocopy:* /MIR*)" ^
  --deny-tool="shell(robocopy:* /PURGE*)" ^
  --deny-tool="write(.env)" ^
  --deny-tool="write(.env.*)" ^
  --deny-tool="write(*.key)" ^
  --deny-tool="write(.kilo/kilo.jsonc)" ^
  --deny-tool="write(.gemini/settings.json)" ^
  --deny-tool="write(.cursor/cli.json)" ^
  --deny-tool="write(.claude/settings.json)" ^
  --deny-tool="write(.codex/rules/*)" ^
  --deny-tool="write(.github/copilot-floor.cmd)"
  --deny-tool="write(.agents/scripts/validate_tool_parity.py)" ^
  --deny-tool="write(.agents/scripts/lib/vendor_matrix_registry.py)" ^
  --deny-tool="write(.agents/scripts/validate_agent_tool_feature_matrix.py)" ^
  --deny-tool="write(.agents/scripts/validate_toolchain_pin_drift.py)" ^
  --deny-tool="write(.agents/canonical_configs/command_deny_floor.toml)" ^
  --deny-tool="write(.agents/canonical_configs/command_allowlist.toml)" ^
  %*
exit /b %errorlevel%
