#!/usr/bin/env python3
"""Convert a JSON channel list to an extended M3U (IPTV) playlist."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

HEADER = "#EXTM3U"
# Attribute order matches the existing canada.m3u playlist.
JSON_TO_ATTR = {
    "tvg_id": "tvg-id",
    "tvg_logo": "tvg-logo",
    "group_title": "group-title",
    "tvg_status": "tvg-status",
}
REQUIRED_FIELDS = ("name", "url")
NEWLINE = "\r\n"


def _escape(value: str) -> str:
    """Escape characters that would break a quoted M3U attribute value."""
    return str(value).replace('"', "&quot;")


def channel_to_extinf(channel: dict) -> str:
    """Return the two M3U lines (EXTINF + URL) for one channel."""
    name = str(channel["name"])
    url = str(channel["url"])
    attrs = [
        f'{attr}="{_escape(channel.get(json_key, ""))}"'
        for json_key, attr in JSON_TO_ATTR.items()
    ]
    extinf = f'#EXTINF:-1 {" ".join(attrs)},{name}'
    return f"{extinf}{NEWLINE}{url}"


def build_m3u(channels: list[dict]) -> str:
    """Return the full playlist text (header + every channel), CRLF terminated."""
    lines = [HEADER]
    for channel in channels:
        lines.append(channel_to_extinf(channel))
    return NEWLINE.join(lines) + NEWLINE


def load_channels(path: Path) -> list[dict]:
    """Read a JSON file and return its list of channel dicts.

    Accepts a top-level JSON array, or an object with a "channels" array.
    """
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if isinstance(data, dict):
        data = data.get("channels", [])
    if not isinstance(data, list):
        raise ValueError(
            "JSON must be an array of channels or an object with a 'channels' array"
        )
    for i, channel in enumerate(data):
        if not isinstance(channel, dict):
            raise ValueError(f"channel #{i} is not an object")
        for field in REQUIRED_FIELDS:
            if not channel.get(field):
                raise ValueError(f"channel #{i} is missing required field '{field}'")
    return data


def convert(json_path: Path, m3u_path: Path) -> int:
    """Convert a JSON channel file to an M3U file. Returns the channel count."""
    channels = load_channels(json_path)
    # newline="" prevents Windows text-mode re-translating our \r\n to \r\r\n.
    Path(m3u_path).write_text(build_m3u(channels), encoding="utf-8", newline="")
    return len(channels)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description="Convert a JSON channel list to an M3U playlist."
    )
    parser.add_argument("input", type=Path, help="input JSON file")
    parser.add_argument(
        "-o", "--output", type=Path, help="output M3U file (default: <input>.m3u)"
    )
    args = parser.parse_args(argv)
    output = args.output or args.input.with_suffix(".m3u")
    count = convert(args.input, output)
    print(f"Wrote {count} channel(s) to {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
