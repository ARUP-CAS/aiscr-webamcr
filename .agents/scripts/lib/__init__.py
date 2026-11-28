# delivery-version: a9e7178f2056994b3ac481702b0ec38cdb13c576 2026-11-28T16:49:05+01:00

"""Shared platform libraries: the estate modules that expose no entrypoint.

Residence is the invocability split. A module here is imported, never run. Package-private helpers stay inside the
package whose members are their only consumers; a module the wider estate imports belongs here however its name begins.

Contract: pipeline/script-authoring
Class: library
Exit codes: Package initializer; no entrypoint.
"""
