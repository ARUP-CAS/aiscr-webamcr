# SPDX-FileCopyrightText: 2026 AIS CR (Archaeological Information System of the Czech Republic) <https://ror.org/01a7rqj69>
# SPDX-License-Identifier: MIT
# delivery-version: b257a1a89279be5e17cda3c133aa77b8c4d2706c 2026-11-07T11:18:12+01:00

"""Shared platform libraries: the estate modules that expose no entrypoint.

Residence is the invocability split. A module here is imported, never run. Package-private helpers stay inside the
package whose members are their only consumers; a module the wider estate imports belongs here however its name begins.

Contract: pipeline/script-authoring
Class: library
Exit codes: Package initializer; no entrypoint.
"""
