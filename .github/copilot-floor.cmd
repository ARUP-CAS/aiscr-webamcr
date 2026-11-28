REM delivery-version: a9e7178f2056994b3ac481702b0ec38cdb13c576 2026-11-28T16:49:05+01:00

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
  --deny-tool="write(.kilo/plugin/*)" ^
  --deny-tool="write(.kilocode/plugin/*)" ^
  --deny-tool="write(.agents/scripts/run_operator_patch.py)" ^
  --deny-tool="write(.agents/scripts/sibling/sibling_repo_write.py)" ^
  --deny-tool="write(.agents/scripts/validate_command_deny_floor_alignment.py)" ^
  --deny-tool="write(.agents/scripts/validate_permission_rule_syntax.py)" ^
  --deny-tool="write(.agents/scripts/lib/command_surface_model.py)" ^
  --deny-tool="write(.agents/scripts/lib/codex_rule_readback.py)" ^
  --deny-tool="write(.agents/hooks/*)" ^
  --deny-tool="write(.codex/hooks.json)" ^
  --deny-tool="write(.cursor/hooks.json)" ^
  --deny-tool="write(.cursor/permissions.json)" ^
  --deny-tool="write(.github/hooks/*)" ^
  --deny-tool="write(.agents/scripts/check_tool_call_guard.py)" ^
  --deny-tool="write(.agents/scripts/lib/protected_paths.py)" ^
  --deny-tool="write(.agents/canonical_configs/templates/workstation_safety/*)" ^
  --deny-tool="write(.agents/scripts/validate_command_allowlist_alignment.py)" ^
  --deny-tool="write(.agents/scripts/validate_workspace_safety_registry.py)" ^
  --deny-tool="write(.agents/scripts/lib/workspace_safety_registry.py)" ^
  %*
exit /b %errorlevel%
