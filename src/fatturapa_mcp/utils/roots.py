"""
fatturapa_mcp.utils.roots
~~~~~~~~~~~~~~~~~~~~~~~~~~
File-system root guard: prevents path-traversal attacks by verifying
that requested paths fall within configured allowed directories.
"""

import os
from pathlib import Path

_ROOTS_ENV_VAR = "FATTURAPA_ALLOWED_ROOTS"


def is_path_allowed(
    file_path: str | Path,
    allowed_roots: list[Path],
) -> bool:
    """Return True if *file_path* is nested under one of the *allowed_roots*.

    Resolves symlinks and ``..`` components via :meth:`Path.resolve` before
    comparing, so path-traversal sequences are neutralised before the check.
    When *allowed_roots* is empty every path is permitted — backward-compatible
    open mode for deployments that do not restrict file access.

    Args:
        file_path: Absolute or relative path to verify.
        allowed_roots: Directories the caller is authorised to read from.

    Returns:
        True if access is permitted, False if the path is outside all roots.
    """
    if not allowed_roots:
        return True
    resolved = Path(file_path).resolve()
    return any(resolved.is_relative_to(root.resolve()) for root in allowed_roots)


def get_allowed_roots() -> list[Path]:
    """Return the allowed file-system roots from the environment.

    Reads ``FATTURAPA_ALLOWED_ROOTS``, which should contain one or more
    directory paths joined by :data:`os.pathsep`.  Returns an empty list
    when the variable is absent or blank, enabling the backward-compatible
    open mode (all paths permitted).

    Returns:
        Possibly-empty list of :class:`~pathlib.Path` objects.
    """
    raw = os.environ.get(_ROOTS_ENV_VAR, "")
    if not raw.strip():
        return []
    return [Path(p.strip()) for p in raw.split(os.pathsep) if p.strip()]
