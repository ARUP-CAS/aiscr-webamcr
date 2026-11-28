REM delivery-version: a9e7178f2056994b3ac481702b0ec38cdb13c576 2026-11-28T16:49:05+01:00

@echo off
rem AIS CR tool-call guard launcher - Windows half (POSIX twin: aiscr-guard).
rem
rem Reached when a host runs the extensionless launcher through cmd.exe, which appends PATHEXT. Resolution mirrors
rem `validation_suite.resolve_python()`: the repository virtualenv first, then a PATH interpreter run before it is
rem trusted, because the Microsoft Store alias is on PATH, resolvable and non-functional.
rem
rem Blocking contract: the guard's exit status passes through unchanged - 0 lets the tool call proceed, 2 refuses it.
rem With no usable interpreter the launcher exits 2 with the corrective step, so the guard fails closed.

setlocal
for %%I in ("%~dp0..\..") do set "AISCR_GUARD_ROOT=%%~fI"
set "AISCR_GUARD=%AISCR_GUARD_ROOT%\.agents\scripts\check_tool_call_guard.py"

if exist "%AISCR_GUARD_ROOT%\.venv\Scripts\python.exe" goto venv_scripts
if exist "%AISCR_GUARD_ROOT%\.venv\bin\python" goto venv_bin
if exist "%AISCR_GUARD_ROOT%\venv\Scripts\python.exe" goto legacy_scripts
python -c "" >nul 2>nul
if not errorlevel 1 goto path_python

echo AIS CR guard could not start: no usable Python interpreter. Create the repository virtualenv ^(python -m venv .venv^) and retry; the call is refused because the guard fails closed. 1>&2
exit /b 2

:venv_scripts
"%AISCR_GUARD_ROOT%\.venv\Scripts\python.exe" -I -S "%AISCR_GUARD%" %*
exit /b %errorlevel%

:venv_bin
"%AISCR_GUARD_ROOT%\.venv\bin\python" -I -S "%AISCR_GUARD%" %*
exit /b %errorlevel%

:legacy_scripts
"%AISCR_GUARD_ROOT%\venv\Scripts\python.exe" -I -S "%AISCR_GUARD%" %*
exit /b %errorlevel%

:path_python
python -I -S "%AISCR_GUARD%" %*
exit /b %errorlevel%
