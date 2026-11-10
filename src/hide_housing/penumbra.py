"""Penumbra mod-format constants. See docs/penumbra-format.md for sources."""

# meta.json schema version; v4 keeps DefaultData and Groups inline in meta.json.
FILE_VERSION = 4

# Penumbra ignores Multi group options beyond this count (IModGroup.MaxMultiOptions).
MAX_MULTI_OPTIONS = 32

# Multi groups store DefaultSettings as a bitmask; 0 means every option is off.
ALL_OPTIONS_OFF = 0
