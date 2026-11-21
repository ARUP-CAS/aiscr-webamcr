# SPDX-FileCopyrightText: 2026 AIS CR (Archaeological Information System of the Czech Republic) <https://ror.org/01a7rqj69>
# SPDX-License-Identifier: MIT
# delivery-version: 4ce7896238fe9996ccf1b0740cf3d6440d8d4d3f 2026-11-21T16:40:49+01:00

"""Shared platform libraries: the estate modules that expose no entrypoint.

Residence is the invocability split. A module here is imported, never run. Package-private helpers stay inside the
package whose members are their only consumers; a module the wider estate imports belongs here however its name begins.

Contract: pipeline/script-authoring
Class: library
Exit codes: Package initializer; no entrypoint.
"""
