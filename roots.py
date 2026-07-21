"""
fatturapa_mcp.utils.roots
~~~~~~~~~~~~~~~~~~~~~~~~~~
File-system root guard: prevents path-traversal attacks and unbounded file
access by verifying that requested paths fall within configured allowed
directories.

Security model — the guard is *fail closed*:

* ``FATTURAPA_ALLOWED_ROOTS`` set   → only paths nested under those roots are
  readable.
* nothing configured               → every ``file_path`` argument is refused.
* ``FATTURAPA_ALLOW_ALL_PATHS=1``  → unrestricted mode, opt-in and explicit.

Refusing by default matters here more than in an ordinary library: this server
is driven by an LLM agent, and the documents it is asked to analyse are
themselves untrusted input. An agent talked into reading ``~/.ssh/id_rsa`` must
be stopped by configuration, not by the agent's good judgement.

Passing ``xml_content`` directly is unaffected — the guard only governs reads
from the file system.
"""

import logging
import os
from pathlib import Path

_ROOTS_ENV_VAR = "FATTURAPA_ALLOWED_ROOTS"
_ALLOW_ALL_ENV_VAR = "FATTURAPA_ALLOW_ALL_PATHS"

# Values accepted as "yes" for the unrestricted-mode opt-in.
_TRUTHY = frozenset({"1", "true", "yes", "on"})

_logger = logging.getLogger(__name__)

# Unrestricted mode is warned about once per process, not once per call, so a
# batch of a thousand invoices does not produce a thousand identical lines.
_unrestricted_warning_emitted = False


def get_allowed_roots() -> list[Path]:
    """Return the allowed file-system roots from the environment.

    Reads ``FATTURAPA_ALLOWED_ROOTS``, which should contain one or more
    directory paths joined by :data:`os.pathsep` (``:`` on POSIX, ``;`` on
    Windows). Returns an empty list when the variable is absent or blank.

    Returns:
        Possibly-empty list of :class:`~pathlib.Path` objects.
    """
    raw = os.environ.get(_ROOTS_ENV_VAR, "")
    if not raw.strip():
        return []
    return [Path(p.strip()) for p in raw.split(os.pathsep) if p.strip()]


def is_unrestricted_mode() -> bool:
    """Return True when the operator has explicitly opted out of the guard.

    Controlled by ``FATTURAPA_ALLOW_ALL_PATHS``. Accepts ``1``, ``true``,
    ``yes`` or ``on``, case-insensitively. Any other value — including an
    unset variable — leaves the guard active.

    Returns:
        True if every path is permitted by explicit operator choice.
    """
    return os.environ.get(_ALLOW_ALL_ENV_VAR, "").strip().lower() in _TRUTHY


def is_path_allowed(
    file_path: str | Path,
    allowed_roots: list[Path],
) -> bool:
    """Return True if *file_path* may be read.

    Resolves symlinks and ``..`` components via :meth:`Path.resolve` before
    comparing, so path-traversal sequences are neutralised before the check.

    An empty *allowed_roots* denies access unless unrestricted mode has been
    explicitly enabled; a warning is emitted once per process in that case.

    Args:
        file_path: Absolute or relative path to verify.
        allowed_roots: Directories the caller is authorised to read from.

    Returns:
        True if access is permitted, False otherwise.
    """
    global _unrestricted_warning_emitted

    if is_unrestricted_mode():
        if not _unrestricted_warning_emitted:
            _logger.warning(
                "%s is enabled: every file-system path is readable. "
                "Set %s instead to restrict access.",
                _ALLOW_ALL_ENV_VAR,
                _ROOTS_ENV_VAR,
            )
            _unrestricted_warning_emitted = True
        return True

    if not allowed_roots:
        return False

    resolved = Path(file_path).resolve()
    return any(resolved.is_relative_to(root.resolve()) for root in allowed_roots)


def ensure_path_allowed(file_path: str | Path) -> None:
    """Raise :class:`PermissionError` unless *file_path* may be read.

    Distinguishes the two denial causes in the message, because they need
    different fixes: an unconfigured server needs roots declared, a configured
    one needs the path moved inside them.

    Args:
        file_path: Path the caller wants to read.

    Raises:
        PermissionError: If access is denied, with actionable remediation text.
    """
    allowed_roots = get_allowed_roots()
    if is_path_allowed(file_path, allowed_roots):
        return

    if not allowed_roots:
        raise PermissionError(
            "Access denied: file-system reads are disabled because no allowed "
            f"roots are configured. Set {_ROOTS_ENV_VAR} to one or more "
            f"directories (joined by {os.pathsep!r}), or pass the document via "
            "the xml_content argument instead."
        )

    raise PermissionError(
        "Access denied: path is outside the allowed roots configured in "
        f"{_ROOTS_ENV_VAR}."
    )
