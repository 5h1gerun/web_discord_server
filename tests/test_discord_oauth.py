import sys
import urllib.parse
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT))

from web.utils import build_discord_oauth_url


def test_build_discord_oauth_url_includes_prompt():
    url = build_discord_oauth_url("123", "https://example.com/callback", "abc")
    parsed = urllib.parse.urlparse(url)
    assert parsed.scheme == "https"
    assert parsed.netloc == "discord.com"
    query = dict(urllib.parse.parse_qsl(parsed.query))
    assert query.get("prompt") == "consent"
    assert query.get("client_id") == "123"
    assert query.get("redirect_uri") == "https://example.com/callback"
    assert query.get("state") == "abc"


