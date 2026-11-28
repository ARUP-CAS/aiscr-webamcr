#!/usr/bin/env python3
# delivery-version: a9e7178f2056994b3ac481702b0ec38cdb13c576 2026-11-28T16:49:05+01:00

"""Refuse, before a shell tool call runs, the accidents a prefix permission rule cannot express.

A seatbelt for the accident class, not enforcement: an allowed interpreter running a newly authored script reaches every
effect this guard refuses, so it earns no enforcement credit against a determined route, and its registry rows record
that route as their residual. What it catches is the accident shape — a command whose own text names the damage.

It refuses three shapes in a shell tool's command:

1. **A destructive operation aimed at a catastrophic target.** A deletion, a ``find`` that deletes, a mirror or purge
   copy, or a pipeline stage feeding a deletion, whose target resolves to a drive or filesystem root, a home directory,
   the repository root, or a path outside the workspace (the repository and the system temporary directory), or whose
   target cannot be resolved because it carries a variable the guard cannot expand. A match-all glob counts as its
   directory; a narrowing glob or a filtered ``find`` is judged only on whether it leaves the workspace. Exec wrappers
   such as ``bash -c``, ``env``, ``sudo`` or ``xargs``, abbreviated PowerShell parameters and directory changes earlier
   in the command do not hide the operation.
2. **A shell-authored write to a kind A or kind B protected path**, by redirection, ``tee``, an in-place editor, a
   content cmdlet, a copy or move destination, or a deletion. Kinds resolve through ``lib/protected_paths.py`` from the
   deny floor's protected-path table, so the guard and close-out cannot disagree. File-tool writes are left to the
   permission rules, which can express them.
3. **Heredoc or here-string file authoring**: a ``cat`` or ``tee`` heredoc whose body lands in a file, or a PowerShell
   here-string sent to a content cmdlet or a redirection. Content then passes through the tool call's encoding, the
   shell and the literal, so escapes collapse at the wrong layer and the file comes out silently wrong. A heredoc fed to
   an interpreter's standard input is not refused.

It also refuses running an operator-reserved entry point, ``run_operator_patch.py`` or
``setup_workstation_assistant_safety.py``, in any spelling: as the command, as an interpreter's script or as its ``-m``
module. A command that only names one, such as a search or a read, stays allowed.

For Kilo Code it also refuses first a call its own permission map is certain to refuse, naming the piece no allow key
covers. Kilo's refusal names only the rule, and an agent reads it as a refusal of the whole operation. This steering
admits nothing, and it steps aside wherever its reading of the call could differ from Kilo's. Where Kilo's matcher
splits a PowerShell command at a bare dot-prefixed token (Kilo-Org/kilocode#15938), the guard names the quoted form
that keeps an allowed command whole. It also refuses a command that a deny key names as PowerShell runs it but that the
split would hide from that key.

Input is one JSON document on standard input, in any of the shapes the registered products send: ``tool_name`` with
``tool_input.command`` (Claude Code, Codex, Gemini CLI), ``toolName`` with ``toolArgs.command``, as an object or a JSON
string (Copilot), Cursor's ``beforeShellExecution`` event with a top-level ``command``, or the Kilo Code plugin
adapter's ``tool`` with ``args.command``; each may carry ``cwd``. Any tool other than a shell is allowed at once.
``--product <id>`` names the registering product, so the answer takes the form that product reads: exit 2 with the step
to take instead on standard error by default, a JSON refusal with exit 0 for Codex and Copilot, and an explicit JSON
allow for Cursor (see ``respond``). The guard fails closed: an input or argument it cannot read, or an internal error,
refuses the call and says so.
A repository that carries no deny floor has no protected-path table, and the protected-write check then has nothing to
protect.

It imports only the standard library and two repository helpers built on it, and reads only the protected-path table,
plus Kilo's project and user permission maps for a Kilo call, so it stays well inside the hot-path budget of a hook
that fires on every tool call.

**Decision record.** After it has answered, the guard appends one line per shell call it decided to a dated file in
the repository's ignored cache: the time, the product, the tool, whether it allowed or refused the call, the rule that
refused it, and a hash of the whitespace-normalized command. The command's text is never written. The record serves
proof acquisition as corroboration only, because it lies inside the agent's reach. Writing it can never change a
decision, prints nothing, and is skipped silently when the cache cannot be written; files older than the retention
window are removed as new days begin.

Contract: agent/ai-automation-governance
Class: script
Exit codes: 0 the call may proceed, or is refused through the JSON answer of a product that reads one; 2 the call is
    refused, including when the guard cannot evaluate it
"""

from __future__ import annotations

import datetime
import hashlib
import json
import os
import re
import shlex
import sys
from pathlib import Path
from typing import List, Mapping, Sequence, Tuple

_SCRIPTS_DIR = Path(__file__).resolve().parent
if str(_SCRIPTS_DIR) not in sys.path:  # pragma: no cover -- direct script startup already supplies this path
    sys.path.insert(0, str(_SCRIPTS_DIR))

from lib.protected_paths import load_protected_paths, protected_kind_of  # noqa: E402
from lib.runtime_env import guard_decision_dir  # noqa: E402

REPO_ROOT = Path(os.path.abspath(_SCRIPTS_DIR.parent.parent))
# The shell tools each product exposes, as its hook surface names them. This is the single declaration of what the guard
# evaluates: a registration that selects tools by name selects exactly these, and the test suite holds each product's
# registration to it, so a renamed or added shell tool cannot fall outside the guard unnoticed.
PRODUCT_SHELL_TOOLS = {
    "claude_code": ("Bash", "PowerShell"),
    "kilo_code": ("bash",),
    "codex": ("Bash",),
    "cursor": ("Shell",),
    "copilot": ("bash", "powershell"),
    "gemini": ("run_shell_command",),
}
SHELL_TOOLS = frozenset(name.lower() for names in PRODUCT_SHELL_TOOLS.values() for name in names)
# The product a registration that names none answers for: Claude Code's registration and the Kilo Code adapter pass no
# product, and both read the exit status.
DEFAULT_PRODUCT = "claude_code"
# Products whose shell tool runs Windows PowerShell on a Windows host although its name says otherwise: Codex runs its
# Bash tool through powershell.exe there.
POWERSHELL_HOSTED = frozenset({"codex"})
# Cursor's shell event carries the command at the top level instead of under a tool name.
CURSOR_SHELL_EVENT = "beforeShellExecution"
# The timeout every product's guard registration declares, in seconds; the test suite holds each registration to it.
# On 2026-11-22 the slowest launch measured under the close-out checkpoint's parallel load took 7.0 s, while Claude
# Code's own hook dispatch had twice overrun a 10 s timeout under that load. The value leaves over four times the
# slowest launch, and it costs nothing on the normal path, where a launch takes well under a second.
GUARD_TIMEOUT_SECONDS = 30
# Kilo Code decides a shell call piece by piece against its project map, the last matching key winning. Pieces split at
# the shell's command separators, and a $( ) body is a piece of its own; this was established by probe on build 7.8.32.
# Kilo's refusal names the rule but never the piece, and an agent reads it as a refusal of the whole operation. For Kilo
# the guard therefore refuses first and names the piece. It steps aside wherever its reading could differ from Kilo's.
KILO_MAP_RELPATH = Path(".kilo") / "kilo.jsonc"
KILO_USER_MAPS = (Path(".config") / "kilo" / "kilo.jsonc", Path(".config") / "kilo" / "kilo.json")
KILO_UNSURE = ("`", "@'", '@"', "<<", "{", "}", "\\")
SUBSTITUTION = re.compile(r"\$\(([^()]*)\)")
# On Windows PowerShell, Kilo's matcher also splits a command at a bare token beginning with a dot and a name that
# follows `--` or a `,` array separator. It decides the remainder as a command of its own, although PowerShell runs the
# line as one command; this is Kilo-Org/kilocode#15938, reproduced on build 7.8.32. The cause is the tree-sitter
# PowerShell grammar: the head lands in an ERROR node and the tail in a command node of its own. Fixes are open in
# Kilo-Org/kilocode#16207 and Kilo-Org/kilocode#16289. Quoting the token, or prefixing it with ./, keeps the command
# whole. Once a Kilo build carries a fix, the false-denial branch below refuses calls Kilo admits and is removed; the
# deny-key branch stays correct either way.
KILO_DOT_SPLIT_ISSUE = "https://github.com/Kilo-Org/kilocode/issues/15938"
_DOT_TOKEN = re.compile(r"^\.[A-Za-z_]")
PROTECTED_KINDS = frozenset({"A", "B"})
# The operator-reserved entry points: the operator runs them in their own terminal, and an agent only prepares their
# input. The deny floor refuses their usual invocation spellings; the guard refuses running them in any spelling, while
# a command that only names them, such as a search or a read, stays allowed.
OPERATOR_RESERVED = frozenset({"run_operator_patch.py", "setup_workstation_assistant_safety.py"})
PYTHON_VALUE_OPTIONS = frozenset({"-x", "-w"})

DELETERS = frozenset({"rm", "rmdir", "rd", "del", "erase", "unlink", "shred", "remove-item", "ri", "clear-item"})
WRAPPERS = frozenset(
    {"sudo", "env", "nohup", "time", "nice", "ionice", "setsid", "command", "exec", "builtin", "xargs"}
)
SHELL_RUNNERS = frozenset({"bash", "sh", "zsh", "dash"})
POWERSHELL_RUNNERS = frozenset({"powershell", "pwsh"})
DIRECTORY_CHANGERS = frozenset({"cd", "pushd", "set-location", "sl", "chdir"})
SLASH_SWITCH_COMMANDS = frozenset({"rd", "del", "erase", "robocopy", "xcopy"})
CONTENT_CMDLETS = frozenset({"set-content", "add-content", "out-file", "new-item", "clear-content", "sc", "ac"})
COPIERS = frozenset({"cp", "mv", "install", "copy", "move", "xcopy", "copy-item", "move-item", "cpi", "mi"})
FIND_FILTERS = frozenset(
    {"-name", "-iname", "-path", "-ipath", "-regex", "-iregex", "-type", "-newer", "-mtime", "-size"}
)
NAMED_PARAMETERS = frozenset(
    {"-path", "-literalpath", "-destination", "-filepath", "-value", "-filter", "-include", "-exclude", "-encoding"}
)
MATCH_ALL = frozenset({"*", ".*", "*.*", "**"})
NULL_SINKS = frozenset({"/dev/null", "$null", "nul", "nul:"})

_HEREDOC = re.compile(r"<<-?\s*(['\"]?)([A-Za-z_][A-Za-z0-9_]*)\1")
_HERE_STRING_OPEN = re.compile(r"@(['\"])\s*$")
_REDIRECT = re.compile(r"^(\d|&|\*)?(>>?|>\|)(.*)$")
_UNEXPANDED = re.compile(r"\$\{?[A-Za-z_]|\$\(|%[A-Za-z_]+%|`")
_GIT_BASH_DRIVE = re.compile(r"^/([A-Za-z])(/|$)")
_SLASH_SWITCH = re.compile(r"^/[A-Za-z-]+(:\S*)?$")
_HOME_VARIABLES = ("$HOME", "${HOME}", "$env:USERPROFILE", "$env:HOME", "%USERPROFILE%")
_TEMP_VARIABLES = ("$env:TEMP", "$env:TMP", "$TMPDIR", "${TMPDIR}", "%TEMP%", "%TMP%")

HEREDOC_REFUSAL = (
    "Refused: a heredoc or here-string is being written into a file, where escapes collapse between the tool call, "
    "the shell and the literal and the file comes out silently wrong. Author the file with the file-writing tool "
    "instead; a heredoc fed to an interpreter's standard input is fine."
)
UNFOLLOWED_CD = "follows a directory change the guard cannot resolve, so its real target is unknown"
FAIL_CLOSED = (
    "Refused: the AIS CR tool-call guard could not evaluate this call ({error}); it fails closed. Retry, and report "
    "this message if it persists."
)


def read_call(raw: str) -> Tuple[str, str, Path]:
    """Return (tool, command, working directory) from any supported payload shape."""
    data = json.loads(raw)
    if not isinstance(data, dict):
        raise ValueError("the payload is not a JSON object")
    cwd = Path(os.path.abspath(str(data.get("cwd") or os.getcwd())))
    if data.get("hook_event_name") == CURSOR_SHELL_EVENT:
        tool, args = PRODUCT_SHELL_TOOLS["cursor"][0], {"command": data.get("command", "")}
    elif "tool_name" in data:
        tool, args = str(data["tool_name"]), data.get("tool_input")
    elif "toolName" in data:
        tool, args = str(data["toolName"]), data.get("toolArgs")
        # Copilot may send a shell tool's arguments as a JSON string; one that cannot be read fails closed.
        if isinstance(args, str) and tool.lower() in SHELL_TOOLS:
            args = json.loads(args)
    else:
        tool, args = str(data.get("tool", "")), data.get("args")
    command = args.get("command", "") if isinstance(args, dict) else ""
    return tool, str(command), cwd


def strip_heredocs(command: str) -> Tuple[str, List[str]]:
    """Return the command with heredoc bodies removed, and the lines that open a heredoc."""
    lines, kept, openers, index = command.split("\n"), [], [], 0
    while index < len(lines):
        line = lines[index]
        kept.append(line)
        delimiters = [match.group(2) for match in _HEREDOC.finditer(line)]
        if delimiters:
            openers.append(line)
        index += 1
        for delimiter in delimiters:
            while index < len(lines) and lines[index].strip() != delimiter:
                index += 1
            index += 1
    return "\n".join(kept), openers


def strip_here_strings(command: str) -> Tuple[str, List[str]]:
    """Return the command with PowerShell here-string bodies collapsed, and each collapsed statement."""
    lines, kept, statements, index = command.split("\n"), [], [], 0
    while index < len(lines):
        match = _HERE_STRING_OPEN.search(lines[index])
        if not match:
            kept.append(lines[index])
            index += 1
            continue
        close = match.group(1) + "@"
        end = index + 1
        while end < len(lines) and not lines[end].lstrip().startswith(close):
            end += 1
        rest = lines[end].lstrip()[2:] if end < len(lines) else ""
        statement = lines[index][: match.start()] + " HERESTRING " + rest
        kept.append(statement)
        statements.append(statement)
        index = end + 1
    return "\n".join(kept), statements


def _is_redirect_ampersand(command: str, index: int) -> bool:
    """Return True for the ``&`` of ``2>&1``, ``>&2`` or ``&>``, which redirects rather than separates."""
    before = command[index - 1] if index else ""
    after = command[index + 1] if index + 1 < len(command) else ""
    return before == ">" or after == ">"


def split_pipelines(command: str, *, escapes: bool) -> List[List[str]]:
    """Split a command into pipelines of stages on unquoted ``&&``, ``||``, ``;``, ``&``, newlines and ``|``."""
    pipelines: List[List[str]] = []
    stages: List[str] = []
    buffer: List[str] = []
    quote = ""
    index = 0

    def end_stage() -> None:
        stages.append("".join(buffer).strip())
        buffer.clear()

    def end_pipeline() -> None:
        end_stage()
        if any(stages):
            pipelines.append([stage for stage in stages if stage])
        stages.clear()

    while index < len(command):
        char, pair = command[index], command[index : index + 2]
        if quote:
            buffer.append(char)
            quote = "" if char == quote else quote
        elif char in "'\"":
            quote = char
            buffer.append(char)
        elif escapes and char == "\\" and index + 1 < len(command):
            buffer.append(pair)
            index += 1
        elif pair in ("&&", "||"):
            end_pipeline()
            index += 1
        elif char in ";\n" or (char == "&" and not _is_redirect_ampersand(command, index)):
            end_pipeline()
        elif char == "|":
            end_stage()
        else:
            buffer.append(char)
        index += 1
    end_pipeline()
    return pipelines


def tokenize(stage: str) -> List[str]:
    """Split one stage into words, removing quotes but keeping backslashes, so Windows paths survive."""
    lexer = shlex.shlex(stage, posix=True)
    lexer.whitespace_split = True
    lexer.escape = ""
    try:
        return list(lexer)
    except ValueError:
        return stage.split()


def command_word(token: str) -> str:
    """Return a token's command name: lower case, without a directory or an executable suffix."""
    name = token.replace("\\", "/").rsplit("/", 1)[-1].lower()
    return name[:-4] if name.endswith((".exe", ".cmd", ".bat")) else name


def unwrap(tokens: Sequence[str]) -> Tuple[List[str], str | None, bool]:
    """Strip exec wrappers; return (remaining tokens, an inner command string to analyze, whether it is PowerShell)."""
    rest = list(tokens)
    while rest:
        word = command_word(rest[0])
        if "=" in rest[0] and not rest[0].startswith(("-", "$")):
            rest = rest[1:]
        elif word in WRAPPERS or word == "timeout":
            rest = rest[1:]
            while rest and (rest[0].startswith("-") or (word == "timeout" and rest[0][:1].isdigit())):
                rest = rest[1:]
        elif word in SHELL_RUNNERS and len(rest) > 2 and rest[1] == "-c":
            return [], rest[2], False
        elif word in POWERSHELL_RUNNERS:
            flags = [index for index, token in enumerate(rest) if token.lower() in ("-command", "-c")]
            return ([], " ".join(rest[flags[0] + 1 :]), True) if flags else (rest, None, False)
        elif word == "cmd" and len(rest) > 2 and rest[1].lower() in ("/c", "/k"):
            return [], " ".join(rest[2:]), False
        else:
            break
    return rest, None, False


def _expand(raw: str) -> str:
    """Expand a leading home or temporary-directory reference; leave anything else as written."""
    home = str(Path.home())
    if raw == "~" or raw.startswith(("~/", "~\\")):
        return home + raw[1:]
    for variable in _HOME_VARIABLES:
        if raw.startswith(variable):
            return home + raw[len(variable) :]
    for variable in _TEMP_VARIABLES:
        if raw.startswith(variable):
            return _temp_dir() + raw[len(variable) :]
    return raw


def _temp_dir() -> str:
    # Only a temporary-directory target pays for this import, which keeps it off the hot path.
    import tempfile  # pylint: disable=import-outside-toplevel

    return os.path.abspath(tempfile.gettempdir())


def resolve(raw: str, cwd: Path | None, *, windows: bool = os.name == "nt") -> Path | None:
    """Resolve a path argument against *cwd*; ``None`` when a variable or an unfollowed directory change hides it."""
    expanded = _expand(raw)
    if _UNEXPANDED.search(expanded):
        return None
    if windows:
        expanded = _GIT_BASH_DRIVE.sub(lambda match: match.group(1).upper() + ":/", expanded)
    path = Path(expanded)
    if path.is_absolute():
        return Path(os.path.abspath(path))
    return Path(os.path.abspath(cwd / path)) if cwd is not None else None


def _within(path: Path, base: Path) -> bool:
    try:
        path.relative_to(base)
    except ValueError:
        return False
    return True


def _glob_base(raw: str) -> str:
    """Return the directory a glob expands inside."""
    head = re.split(r"[*?\[]", raw, maxsplit=1)[0]
    if not head:
        return "."
    if head.endswith(("/", "\\")):
        base = head[:-1]
        return base if base and not base.endswith(":") else head
    return os.path.dirname(head.replace("\\", "/")) or "."


def catastrophic_reason(raw: str, cwd: Path | None, *, narrowed: bool = False) -> str | None:
    """Return why acting destructively on *raw* is catastrophic, or ``None`` when the target is ordinary."""
    target, whole = raw, not narrowed
    if any(char in raw for char in "*?["):
        whole = whole and re.split(r"[/\\]", raw)[-1] in MATCH_ALL
        target = _glob_base(raw)
    path = resolve(target, cwd)
    if path is None:
        return (
            UNFOLLOWED_CD
            if cwd is None
            else "carries a variable the guard cannot expand, so its real target is unknown"
        )
    named = {
        Path(path.anchor): "is a drive or filesystem root",
        Path.home(): "is the home directory",
        REPO_ROOT: "is the repository root",
    }
    if whole and path in named:
        return named[path]
    if not (_within(path, REPO_ROOT) or _within(path, Path(_temp_dir()))):
        return "lies outside the workspace (the repository and the system temporary directory)"
    return None


def _script_name(token: str) -> str:
    """Return a token's file name, whichever separator its path uses."""
    return token.replace("\\", "/").rsplit("/", 1)[-1]


def reserved_entry_point(head: str, args: Sequence[str]) -> str | None:
    """Return the operator-reserved script an invocation runs, or ``None``.

    A reserved script runs when it is the command itself, the first script an interpreter is given, or the module an
    interpreter's ``-m`` names. ``cmd /c`` hands the rest of the line on; PowerShell's call operator is split off as a
    separator before this check. An interpreter held in a variable is read as one, because the guard cannot know what
    the variable holds.
    """
    word = command_word(head)
    if word == "cmd":
        handed = next((index for index, token in enumerate(args) if token.lower() in ("/c", "/k")), None)
        rest = list(args[handed + 1 :]) if handed is not None else []
        return reserved_entry_point(rest[0], rest[1:]) if rest else None
    if _script_name(head) in OPERATOR_RESERVED:
        return _script_name(head)
    if word == "py" or word.startswith(("python", "$")):
        return _interpreter_script(args)
    return None


def _interpreter_script(args: Sequence[str]) -> str | None:
    """Return the reserved script or module an interpreter is given, or ``None``.

    Interpreter options are skipped, and so is the value of an option that takes one; code passed with ``-c`` names no
    script.
    """
    skip_next = False
    for index, token in enumerate(args):
        if skip_next:
            skip_next = False
        elif token == "-m":
            module = f"{args[index + 1]}.py" if index + 1 < len(args) else ""
            return module if module in OPERATOR_RESERVED else None
        elif token == "-c":
            return None
        elif token.lower() in PYTHON_VALUE_OPTIONS:
            skip_next = True
        elif not token.startswith("-"):
            return _script_name(token) if _script_name(token) in OPERATOR_RESERVED else None
    return None


def positionals(word: str, args: Sequence[str]) -> List[str]:
    """Return the arguments that are neither options, option values nor redirection targets."""
    found: List[str] = []
    skip_next = False
    for token in args:
        lowered = token.lower()
        if skip_next:
            skip_next = False
        elif lowered in NAMED_PARAMETERS:
            skip_next = True
        elif token.startswith("-") or (word in SLASH_SWITCH_COMMANDS and _SLASH_SWITCH.match(token)):
            continue
        elif _REDIRECT.match(token):
            skip_next = not _REDIRECT.match(token).group(3)
        else:
            found.append(token)
    return found


def named_value(args: Sequence[str], names: Sequence[str]) -> List[str]:
    """Return the values that follow any of the named PowerShell parameters (case-insensitive)."""
    return [args[index + 1] for index, token in enumerate(args[:-1]) if token.lower() in names]


def destructive_targets(word: str, args: Sequence[str]) -> Tuple[List[str], bool] | None:
    """Return (targets, narrowed) for a destructive invocation, or ``None`` when the invocation is not destructive."""
    if word in DELETERS:
        return named_value(args, ("-path", "-literalpath")) + positionals(word, args), False
    if word == "find" and ("-delete" in args or any(command_word(token) in DELETERS for token in args)):
        starts = [token for token in args[: _first_expression(args)] if not token.startswith("-")]
        return starts or ["."], any(token.lower() in FIND_FILTERS for token in args)
    if word == "robocopy" and any(token.upper() in ("/MIR", "/PURGE") for token in args):
        return positionals(word, args)[1:2] or ["."], False
    return None


def _first_expression(args: Sequence[str]) -> int:
    for index, token in enumerate(args):
        if token.startswith(("-", "(", "!")):
            return index
    return len(args)


def write_targets(word: str, args: Sequence[str]) -> List[str]:
    """Return the paths an invocation writes by its own arguments rather than by redirection."""
    places = positionals(word, args)
    if word in DELETERS:
        return named_value(args, ("-path", "-literalpath")) + places
    if word == "tee" or (word in ("sed", "perl") and any(token.startswith(("-i", "--in-place")) for token in args)):
        return places
    if word in COPIERS:
        return named_value(args, ("-destination",)) or places[-1:]
    if word in CONTENT_CMDLETS:
        return named_value(args, ("-path", "-literalpath", "-filepath")) or places[:1]
    if word == "dd":
        return [token[3:] for token in args if token.startswith("of=")]
    return []


def redirect_targets(tokens: Sequence[str]) -> List[str]:
    """Return the files a stage redirects output into, skipping stream duplication and null sinks."""
    targets: List[str] = []
    for index, token in enumerate(tokens):
        match = _REDIRECT.match(token)
        if not match:
            continue
        target = match.group(3) or (tokens[index + 1] if index + 1 < len(tokens) else "")
        if target and not target.startswith("&") and target.lower() not in NULL_SINKS:
            targets.append(target)
    return targets


def _authors_file(statement: str, *, heredoc: bool) -> bool:
    """Return True when a heredoc opener or here-string statement sends its body into a file."""
    for pipeline in split_pipelines(statement, escapes=True):
        for stage in pipeline:
            tokens = tokenize(stage)
            if not tokens or (heredoc and "<<" not in stage):
                continue
            word = command_word(tokens[0])
            passes_body = not heredoc or word in ("cat", "tee") or tokens[0].startswith("<<")
            writes = bool(redirect_targets(tokens)) or (word == "tee" and bool(positionals(word, tokens[1:])))
            if (passes_body and writes) or (not heredoc and word in CONTENT_CMDLETS):
                return True
    return False


class Guard:
    """Evaluate one shell command against the three refused shapes, following directory changes as it goes."""

    def __init__(self, cwd: Path, table: Mapping[str, Mapping[str, object]]) -> None:
        self.cwd: Path | None = cwd
        self.table = table

    def protected_refusal(self, raw: str) -> str | None:
        """Return the refusal for a write to a kind A or B path, or ``None``."""
        path = resolve(raw, self.cwd)
        if path is None or not _within(path, REPO_ROOT):
            return None
        relative = path.relative_to(REPO_ROOT).as_posix()
        kind = protected_kind_of(relative, self.table)
        if kind not in PROTECTED_KINDS:
            return None
        return (
            f"Refused: this command writes {relative}, a kind {kind} protected path. Kind {kind} changes travel as an "
            "operator patch: stage the edit with `python .agents/scripts/setup_operator_patch.py stage --label <label> "
            f"{relative}` and let the operator apply it."
        )

    def destructive_refusal(self, word: str, targets: Sequence[str], *, narrowed: bool) -> str | None:
        """Return the refusal for the first catastrophic destructive target, or ``None``."""
        for target in targets:
            reason = catastrophic_reason(target, self.cwd, narrowed=narrowed)
            if reason:
                return (
                    f"Refused: `{word}` would act destructively on {target!r}, which {reason}. Name literal paths "
                    "inside the repository instead, or ask the operator to run this one in their own terminal."
                )
        return None

    def change_directory(self, args: Sequence[str]) -> None:
        """Follow a directory change; an unresolvable one leaves later relative targets unknown."""
        places = positionals("cd", args)
        if "-" in args:
            self.cwd = None
        elif not places:
            self.cwd = Path.home()
        else:
            self.cwd = resolve(places[0], self.cwd)

    def stage_refusal(self, stage: str, position: int, *, powershell: bool) -> str | None:
        """Return the first refusal one pipeline stage earns, or ``None``."""
        tokens, inner, inner_powershell = unwrap(tokenize(stage))
        if inner is not None:
            return self.command_refusal(inner, powershell=inner_powershell or powershell)
        if not tokens:
            return None
        word, args = command_word(tokens[0]), tokens[1:]
        if word in DIRECTORY_CHANGERS:
            self.change_directory(args)
            return None
        return self.invocation_refusal(word, args, tokens, position)

    def invocation_refusal(self, word: str, args: Sequence[str], tokens: Sequence[str], position: int) -> str | None:
        """Return the first refusal one command invocation earns: reserved, pipeline-fed, destructive, protected."""
        reserved = reserved_entry_point(tokens[0], args)
        if reserved:
            return (
                f"Refused: `{reserved}` is an operator-reserved entry point, which the operator runs in their own "
                "terminal. Prepare what it needs (an operator patch is staged with `python "
                ".agents/scripts/setup_operator_patch.py stage --label <label> <paths>`) and hand the operator the "
                "exact command."
            )
        if position and word in DELETERS and not positionals(word, args):
            return (
                f"Refused: `{word}` is fed paths by an earlier pipeline stage, so what it deletes is decided at run "
                "time. List the paths first, then delete them by name."
            )
        destructive = destructive_targets(word, args)
        refusal = self.destructive_refusal(word, destructive[0], narrowed=destructive[1]) if destructive else None
        for target in write_targets(word, args) + redirect_targets(tokens):
            refusal = refusal or self.protected_refusal(target)
        return refusal

    def command_refusal(self, command: str, *, powershell: bool) -> str | None:
        """Return the first refusal a whole command earns, or ``None``."""
        without_heredocs, openers = strip_heredocs(command)
        cleaned, statements = strip_here_strings(without_heredocs)
        if any(_authors_file(line, heredoc=True) for line in openers) or any(
            _authors_file(line, heredoc=False) for line in statements
        ):
            return HEREDOC_REFUSAL
        for pipeline in split_pipelines(cleaned, escapes=not powershell):
            for position, stage in enumerate(pipeline):
                refusal = self.stage_refusal(stage, position, powershell=powershell)
                if refusal:
                    return refusal
        return None


def _jsonc(text: str) -> object:
    """Parse JSON carrying ``//`` line comments and trailing commas, the form Kilo's configuration files take."""
    kept: List[str] = []
    quoted = False
    index = 0
    while index < len(text):
        char = text[index]
        if quoted:
            kept.append(char)
            if char == "\\" and index + 1 < len(text):
                kept.append(text[index + 1])
                index += 1
            elif char == '"':
                quoted = False
        elif char == '"':
            quoted = True
            kept.append(char)
        elif text.startswith("//", index):
            while index < len(text) and text[index] != "\n":
                index += 1
            continue
        else:
            kept.append(char)
        index += 1
    return json.loads(re.sub(r",(\s*[}\]])", r"\1", "".join(kept)))


def kilo_shell_map(path: Path) -> List[Tuple[str, str]]:
    """Return a Kilo map's shell keys in evaluation order, or none when the file or its shell table is absent."""
    if not path.is_file():
        return []
    data = _jsonc(path.read_text(encoding="utf-8"))
    shell = data.get("permission", {}).get("bash", {}) if isinstance(data, dict) else {}
    return [(str(key), str(value)) for key, value in shell.items()] if isinstance(shell, dict) else []


def _key_matches(piece: str, key: str) -> bool:
    """Match a piece against a Kilo key: ``*`` and ``?`` are wildcards, case is ignored so a match is never missed."""
    pattern = re.escape(key).replace(r"\*", ".*").replace(r"\?", ".")
    return re.fullmatch(pattern, piece, flags=re.DOTALL | re.IGNORECASE) is not None


def _separator_in_quotes(command: str) -> bool:
    """Return True when a command separator sits inside quotes, where the guard and Kilo could split differently."""
    quote = ""
    for char in command:
        if quote:
            if char == quote:
                quote = ""
            elif char in ";|&\n":
                return True
        elif char in "'\"":
            quote = char
    return False


def kilo_pieces(command: str) -> List[str] | None:
    """Return the pieces Kilo decides separately, or ``None`` where the guard's reading could differ from Kilo's."""
    if any(marker in command for marker in KILO_UNSURE) or _separator_in_quotes(command):
        return None
    pieces = [stage for pipeline in split_pipelines(command, escapes=False) for stage in pipeline]
    pieces += [body.strip() for body in SUBSTITUTION.findall(command) if body.strip()]
    return pieces


def _tokens_with_offsets(piece: str) -> List[Tuple[int, str]]:
    """Return each whitespace-separated token with its offset, keeping quoted text inside its token."""
    tokens: List[Tuple[int, str]] = []
    start: int | None = None
    quote = ""
    for index, char in enumerate(piece + " "):
        if quote:
            quote = "" if char == quote else quote
        elif char.isspace():
            if start is not None:
                tokens.append((start, piece[start:index]))
                start = None
        else:
            start = index if start is None else start
            quote = char if char in "'\"" else ""
    return tokens


def kilo_dot_split(piece: str) -> Tuple[str, str, str] | None:
    """Return the head, the splitting token and the remainder Kilo's matcher cuts a piece into, or ``None``."""
    tokens = _tokens_with_offsets(piece)
    ended = False
    for position, (offset, token) in enumerate(tokens):
        after_comma = position > 0 and tokens[position - 1][1].endswith(",")
        if position and _DOT_TOKEN.match(token) and (ended or after_comma):
            return piece[:offset].rstrip().rstrip(",").rstrip(), token, piece[offset:]
        ended = ended or token == "--"
    return None


def _allowed(piece: str, allows: Sequence[str]) -> bool:
    return any(_key_matches(piece, key) for key in allows)


def _dot_split_refusal(piece: str, allows: Sequence[str], denies: Sequence[str]) -> str | None:
    """Return the refusal for a piece Kilo's dot-token split would misjudge, or ``None``.

    A deny key that names the piece as PowerShell runs it, but neither part Kilo decides, is honoured. An allowed head
    whose remainder no allow key covers is a false denial, and the refusal names the form that keeps the command whole.
    """
    split = kilo_dot_split(piece)
    if split is None:
        return None
    head, token, remainder = split
    hidden = [
        key for key in denies if _key_matches(piece, key) and not any(_key_matches(p, key) for p in (head, remainder))
    ]
    if hidden:
        return (
            f"Refused: the deny key `{hidden[0]}` in {KILO_MAP_RELPATH.as_posix()} names this command as PowerShell "
            f"runs it, but Kilo's matcher splits it at the bare token `{token}` ({KILO_DOT_SPLIT_ISSUE}) and would "
            "decide the parts out of that key's sight. The command is refused as the key intends; tell the operator "
            "if the task needs it."
        )
    if _allowed(head, allows) and not _allowed(remainder, allows):
        return (
            f"Refused before Kilo's permission map: on Windows PowerShell, Kilo's matcher splits this command at the "
            f"bare token `{token}` after `--` or `,` and decides `{remainder}` as a command of its own, which no allow "
            f"key covers, although PowerShell runs the line as one command ({KILO_DOT_SPLIT_ISSUE}). Write the token "
            f'quoted ("{token}") or with a ./ prefix (./{token}) and run the command again. That is not routing around '
            "the map: the map allows this command, and the quoted form lets the matcher see it whole."
        )
    return None


def kilo_steering(command: str, root: Path, home: Path) -> str | None:
    """Return the refusal naming a piece Kilo's map would refuse, or ``None`` when no piece is certain to be refused.

    A piece is certain to be refused when the project map carries a deny catch-all and no allow key of the project or
    the user map matches it, ignoring case. A piece Kilo's dot-token split would misjudge is answered first: a false
    denial names the form that keeps the command whole, and a deny key the split would hide is honoured. The guard
    admits nothing.
    """
    project = kilo_shell_map(root / KILO_MAP_RELPATH)
    if ("*", "deny") not in project:
        return None
    pieces = kilo_pieces(command)
    if not pieces:
        return None
    user: List[Tuple[str, str]] = []
    for relative in KILO_USER_MAPS:
        user += kilo_shell_map(home / relative)
    allows = [key for key, value in project + user if value == "allow"]
    denies = [key for key, value in project if value == "deny" and key != "*"]
    for piece in pieces:
        refusal = _dot_split_refusal(piece, allows, denies)
        if refusal:
            return refusal
    unlisted = [piece for piece in pieces if not _allowed(piece, allows)]
    if not unlisted:
        return None
    others = len(pieces) - len(unlisted)
    message = (
        f"Refused before Kilo's permission map: the piece `{unlisted[0]}` matches no allow key in "
        f"{KILO_MAP_RELPATH.as_posix()}, so the map would refuse this whole call. Only that piece is refused"
        + (
            f"; the other {others} piece(s) of the command are not, so run each of them as its own tool call. "
            if others
            else ". "
        )
        + "Drop the refused piece if it only formats or tidies output, or tell the operator what the task needs it "
        "for; never reshape it to get it past the map."
    )
    if unlisted[0].startswith("$"):
        message += (
            " A variable assigned in one call is gone in the next, so write its value into each command literally."
        )
    if "&&" in command or "||" in command:
        message += (
            " This bash tool runs Windows PowerShell 5.1 when no SHELL is set, where `&&` and `||` are syntax errors, "
            "so separate calls are the working form there too."
        )
    return message


def evaluate(  # pylint: disable=too-many-arguments
    raw: str,
    *,
    root: Path = REPO_ROOT,
    product: str = DEFAULT_PRODUCT,
    windows: bool = os.name == "nt",
    home: Path | None = None,
) -> Tuple[int, str]:
    """Return (exit code, refusal message) for one tool-call payload."""
    tool, command, cwd = read_call(raw)
    lowered = tool.lower()
    if lowered not in SHELL_TOOLS or not command.strip():
        return 0, ""
    try:
        table: Mapping[str, Mapping[str, object]] = load_protected_paths(root)
    except FileNotFoundError:
        table = {}
    powershell = lowered == "powershell" or (windows and product in POWERSHELL_HOSTED)
    refusal = Guard(cwd, table).command_refusal(command, powershell=powershell)
    if refusal is None and product == "kilo_code":
        refusal = kilo_steering(command, root, home or Path.home())
    return (2, refusal) if refusal else (0, "")


def parse_product(argv: Sequence[str]) -> str:
    """Return the product named by ``--product``, or the default product when the registration names none."""
    if not argv:
        return DEFAULT_PRODUCT
    if len(argv) == 2 and argv[0] == "--product" and argv[1] in PRODUCT_SHELL_TOOLS:
        return argv[1]
    raise ValueError(f"unrecognised arguments: {' '.join(argv)}")


def respond(product: str, code: int, message: str) -> Tuple[int, str, str]:
    """Return (exit status, standard output, standard error) in the hook protocol the product reads.

    Codex treats any non-zero exit as a failed hook and runs the call, and Copilot drops the reason of an exit-2
    refusal, so both receive a JSON refusal with exit 0. Cursor's fail-closed registration treats empty output as a
    failure, so it receives an explicit JSON allow. Every other product reads exit 2 with the step on standard error.
    """
    if product == "codex":
        if not code:
            return 0, "", ""
        decision = {"hookEventName": "PreToolUse", "permissionDecision": "deny", "permissionDecisionReason": message}
        return 0, json.dumps({"hookSpecificOutput": decision}), ""
    if product == "copilot":
        if not code:
            return 0, "", ""
        return 0, json.dumps({"permissionDecision": "deny", "permissionDecisionReason": message}), ""
    if product == "cursor" and not code:
        return 0, json.dumps({"permission": "allow"}), ""
    return code, "", message


# The rule each refusal message carries, by a phrase only that refusal uses; the decision record stores the rule id.
GUARD_RULES = (
    ("would act destructively", "destructive-target"),
    ("is fed paths by an earlier pipeline stage", "pipeline-deletion"),
    ("protected path. Kind", "protected-write"),
    ("is an operator-reserved entry point", "reserved-entry-point"),
    ("a heredoc or here-string is being written", "heredoc-authoring"),
    ("Refused before Kilo's permission map", "kilo-steering"),
    ("Refused: the deny key", "kilo-hidden-deny"),
    ("could not evaluate this call", "fail-closed"),
)
# How many days of the decision record are kept: longer than the proof staleness threshold, so evidence still inside
# that threshold can be corroborated.
DECISION_RETENTION_DAYS = 120


def rule_of(message: str) -> str:
    """Return the id of the guard rule a refusal message carries; an allowed call carries none."""
    if not message:
        return ""
    return next((rule for phrase, rule in GUARD_RULES if phrase in message), "other")


def shape_of(command: str) -> str:
    """Return the record's hash of a command, whitespace-normalized, so the command's text is never kept."""
    return hashlib.sha256(" ".join(command.split()).encode("utf-8")).hexdigest()[:16]


def _prune_decisions(folder: Path, today: datetime.date) -> None:
    """Remove the record's day files older than the retention window."""
    cutoff = (today - datetime.timedelta(days=DECISION_RETENTION_DAYS)).isoformat()
    for old in folder.glob("decisions-*.jsonl"):
        if old.stem.removeprefix("decisions-") < cutoff:
            old.unlink()


def record_decision(  # pylint: disable=too-many-arguments
    raw: str, product: str, code: int, message: str, *, root: Path | None = None, now: datetime.datetime | None = None
) -> None:
    """Append the decision on one shell call to today's record; never raise, never print, never change the answer."""
    try:
        tool, command, _cwd = read_call(raw)
        if tool.lower() not in SHELL_TOOLS or not command.strip():
            return
        moment = now or datetime.datetime.now(datetime.timezone.utc)
        folder = guard_decision_dir(root or REPO_ROOT, create=True)
        target = folder / f"decisions-{moment.date().isoformat()}.jsonl"
        if not target.exists():
            _prune_decisions(folder, moment.date())
        entry = {
            "time": moment.isoformat(timespec="seconds"),
            "product": product,
            "tool": tool,
            "decision": "refuse" if code else "allow",
            "rule": rule_of(message) if code else "",
            "shape": shape_of(command),
        }
        with target.open("a", encoding="utf-8", newline="\n") as handle:
            handle.write(json.dumps(entry) + "\n")
    except Exception:  # pylint: disable=broad-exception-caught  # the record never blocks or changes a decision
        return


def main(argv: Sequence[str]) -> int:
    """Read the payload from standard input and answer in the registering product's hook protocol."""
    product = DEFAULT_PRODUCT
    raw = ""
    try:
        product = parse_product(argv)
        # A Windows runner may prefix the payload with a byte-order mark; it is not part of the JSON.
        raw = sys.stdin.buffer.read().decode("utf-8-sig")
        code, message = evaluate(raw, product=product)
    # The guard fails closed on anything it cannot read or evaluate.
    except Exception as exc:  # pylint: disable=broad-exception-caught
        code, message = 2, FAIL_CLOSED.format(error=exc)
    status, out, err = respond(product, code, message)
    if out:
        sys.stdout.write(out + "\n")
    if err:
        sys.stderr.write(err + "\n")
    record_decision(raw, product, code, message)
    return status


if __name__ == "__main__":  # pragma: no cover -- CLI bootstrap delegates to tested main
    raise SystemExit(main(sys.argv[1:]))
