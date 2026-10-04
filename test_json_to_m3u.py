import json
import subprocess
import sys
from pathlib import Path

import pytest

from json_to_m3u import build_m3u, channel_to_extinf, convert, load_channels


SAMPLE = {
    "name": "Noovo",
    "url": "http://official8k.com/899eab2914/2763b0270149/177327",
    "tvg_id": "Noovo.ca2",
    "tvg_logo": "",
    "group_title": "Canada 🇨🇦",
    "tvg_status": "not-working",
}


def test_build_m3u_empty_has_header_only():
    assert build_m3u([]) == "#EXTM3U\r\n"


def test_channel_line_matches_canada_format():
    expected = (
        '#EXTINF:-1 tvg-id="Noovo.ca2" tvg-logo="" group-title="Canada 🇨🇦" '
        'tvg-status="not-working",Noovo\r\n'
        'http://official8k.com/899eab2914/2763b0270149/177327'
    )
    assert channel_to_extinf(SAMPLE) == expected


def test_missing_optional_fields_default_to_empty():
    line = channel_to_extinf({"name": "X", "url": "http://x"})
    assert line == (
        '#EXTINF:-1 tvg-id="" tvg-logo="" group-title="" tvg-status="",X'
        "\r\nhttp://x"
    )


def test_quotes_in_values_are_escaped():
    line = channel_to_extinf({"name": 'A "B"', "url": "http://x", "tvg_id": 'q"q'})
    assert 'tvg-id="q&quot;q"' in line
    assert ',A "B"' in line


def test_build_m3u_multiple_channels_uses_crlf_only():
    text = build_m3u([SAMPLE, {**SAMPLE, "name": "TVA Sports"}])
    assert text.startswith("#EXTM3U\r\n")
    assert text.count("\r\n") == 5  # header + 2 lines x 2 channels
    assert "\n" not in text.replace("\r\n", "")


def test_load_channels_accepts_top_level_array(tmp_path):
    p = tmp_path / "in.json"
    p.write_text(json.dumps([SAMPLE]), encoding="utf-8")
    assert load_channels(p) == [SAMPLE]


def test_load_channels_accepts_channels_object(tmp_path):
    p = tmp_path / "in.json"
    p.write_text(json.dumps({"channels": [SAMPLE]}), encoding="utf-8")
    assert load_channels(p) == [SAMPLE]


def test_load_channels_rejects_missing_url(tmp_path):
    p = tmp_path / "in.json"
    p.write_text(json.dumps([{"name": "X"}]), encoding="utf-8")
    with pytest.raises(ValueError):
        load_channels(p)


def test_convert_writes_utf8_crlf_file(tmp_path):
    src = tmp_path / "in.json"
    dst = tmp_path / "out.m3u"
    src.write_text(json.dumps({"channels": [SAMPLE]}), encoding="utf-8")
    assert convert(src, dst) == 1
    raw = dst.read_bytes()
    assert raw.startswith(b"#EXTM3U\r\n")
    assert "Canada 🇨🇦".encode("utf-8") in raw
    assert b"\r\r\n" not in raw  # no double-CR from text-mode translation


def test_cli_default_output_name(tmp_path):
    src = tmp_path / "list.json"
    src.write_text(json.dumps([SAMPLE]), encoding="utf-8")
    result = subprocess.run(
        [sys.executable, "json_to_m3u.py", str(src)],
        capture_output=True,
        text=True,
        cwd=Path(__file__).parent,
    )
    assert result.returncode == 0, result.stderr
    assert (tmp_path / "list.m3u").read_bytes().startswith(b"#EXTM3U\r\n")
