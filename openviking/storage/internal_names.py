"""Shared internal file-name constants for Python storage code."""

from __future__ import annotations

MULTIWRITE_PATH_LOCK_FILE = ".path.ovlock"
MULTIWRITE_EXACT_LOCK_FILE_PREFIX = ".exact.ovlock."
MULTIWRITE_REDIRECT_FILE = ".redirect.json"
MULTIWRITE_SYNC_LOG_FILE = ".sync_log.json"

MULTIWRITE_INTERNAL_FILE_NAMES = frozenset(
    {
        MULTIWRITE_PATH_LOCK_FILE,
        MULTIWRITE_REDIRECT_FILE,
        MULTIWRITE_SYNC_LOG_FILE,
    }
)


def is_storage_internal_name(name: str) -> bool:
    """Return whether ``name`` is multi-write metadata owned by the storage layer.

    Mirrors ``is_hidden_internal_name`` in ``crates/ragfs/src/core/internal_names.rs``:
    the directory lock, exact (sidecar) locks, redirect and sync-log files that RAGFS
    keeps next to user content in any directory. Such an entry is hidden from every
    listing and must never be created, written, copied or moved by a user.

    The account-root internal directories (``/local/{account}/_system`` and
    ``/local/{account}/tasks``) are deliberately not part of this predicate: root
    listings use ``VikingURI.LISTABLE_SCOPES`` as a whitelist, and below the root a
    user directory that happens to be called ``tasks`` or ``_system`` is ordinary
    content.
    """
    return name in MULTIWRITE_INTERNAL_FILE_NAMES or name.startswith(
        MULTIWRITE_EXACT_LOCK_FILE_PREFIX
    )


WEBDAV_RESERVED_FILENAMES = frozenset(
    {
        ".abstract.md",
        ".overview.md",
        ".relations.json",
        *MULTIWRITE_INTERNAL_FILE_NAMES,
    }
)

# Dot-files OpenViking itself keeps inside ``viking://resources``. User files
# with the same names are shadowed, so the set stays limited to real metadata.
RESOURCE_METADATA_FILENAMES = frozenset(
    {
        ".abstract.md",
        ".overview.md",
        ".relations.json",
        ".artifact_manifest.json",
        ".image_mappings.json",
        ".source.json",
        ".git_source_repo",
        ".watch_tasks.json",
        ".watch_tasks.json.bak",
        ".watch_tasks.json.tmp",
    }
)

_USER_DOTFILE_SCOPES = frozenset({"resources"})


def _uri_scope(uri: str) -> str:
    rest = uri.removeprefix("viking://").lstrip("/")
    return rest.split("/", 1)[0]


def may_list_user_dotfiles(uri: str) -> bool:
    """Return whether a listing rooted at ``uri`` can reach user dot-files.

    Callers use it to ask the storage backend for hidden entries and then filter
    them with :func:`is_hidden_entry_name`. The account root qualifies because
    it contains ``resources``.
    """
    scope = _uri_scope(uri)
    return not scope or scope in _USER_DOTFILE_SCOPES


def is_hidden_entry_name(name: str, uri: str) -> bool:
    """Return whether a dot-named entry is hidden from listings and indexing.

    ``uri`` is the entry itself or its parent directory; only its scope matters.
    In ``viking://resources`` user content such as ``.gitlab-ci.yml`` or
    ``.helm/`` is ordinary content, so only OpenViking metadata and storage-layer
    internal files are hidden. Other scopes keep their own dot-file metadata
    (``.meta.json``, ``.done``, ``.recall_log.json``, ...) and hide every
    dot-name.
    """
    if not name.startswith("."):
        return False
    if _uri_scope(uri) not in _USER_DOTFILE_SCOPES:
        return True
    return name in RESOURCE_METADATA_FILENAMES or is_storage_internal_name(name)
