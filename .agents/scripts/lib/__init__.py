# SPDX-FileCopyrightText: 2026 AIS CR (Archaeological Information System of the Czech Republic) <https://ror.org/01a7rqj69>
# SPDX-License-Identifier: MIT
# delivery-version: 083eb1bc1a0c628b2d6d48b806b6568be3f67ac2 2026-11-07T12:31:37+01:00

"""Shared platform libraries: the estate modules that expose no entrypoint.

Residence is the invocability split. A module here is imported, never run. Package-private helpers stay inside the
package whose members are their only consumers; a module the wider estate imports belongs here however its name begins.

Contract: pipeline/script-authoring
Class: library
Exit codes: Package initializer; no entrypoint.
"""
