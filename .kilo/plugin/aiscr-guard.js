// AIS CR accident guard for Kilo Code.
//
// Forwards each shell tool call to the repository's tool-call guard and refuses the call when the guard does. The
// decision logic lives once, in .agents/scripts/check_tool_call_guard.py; this adapter only carries the call to it
// through the launcher pair under .agents/hooks/. It fails closed: a guard that cannot start, crashes, times out or
// answers anything but 0 refuses the call, and Kilo turns a thrown error into a failed tool call.
import { spawnSync } from "node:child_process"
import { join } from "node:path"
import { fileURLToPath } from "node:url"

// Must equal PRODUCT_SHELL_TOOLS["kilo_code"] in check_tool_call_guard.py; the test suite holds the two together.
const SHELL_TOOLS = ["bash"]

const ROOT = fileURLToPath(new URL("../../", import.meta.url))
// The guard answers a Kilo call in Kilo's own terms, including the steering that names a piece the map would refuse.
const LAUNCHER =
  process.platform === "win32"
    ? ["cmd.exe", ["/d", "/c", join(ROOT, ".agents", "hooks", "aiscr-guard.cmd"), "--product", "kilo_code"]]
    : ["sh", [join(ROOT, ".agents", "hooks", "aiscr-guard"), "--product", "kilo_code"]]

const guard = async ({ directory }) => ({
  "tool.execute.before": async (input, output) => {
    if (!SHELL_TOOLS.includes(input?.tool)) return
    const payload = JSON.stringify({ tool: input.tool, args: output?.args ?? {}, cwd: directory })
    // GUARD_TIMEOUT_SECONDS in check_tool_call_guard.py, in milliseconds; the test suite holds the two together.
    const result = spawnSync(LAUNCHER[0], LAUNCHER[1], { input: payload, encoding: "utf8", windowsHide: true, timeout: 30000 })
    if (result.status === 0) return
    const reason =
      (result.stderr || "").trim() ||
      `The AIS CR tool-call guard did not answer (status ${result.status}, ${result.error ?? "no error"}); ` +
        "the call is refused because the guard fails closed."
    throw new Error(reason)
  },
})

export default { id: "aiscr-guard", server: guard }
