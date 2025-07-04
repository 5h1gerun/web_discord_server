import urllib.parse


def build_discord_oauth_url(client_id: str, redirect_uri: str, state: str) -> str:
    params = {
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": "identify",
        "state": state,
        "prompt": "consent",
    }
    return "https://discord.com/api/oauth2/authorize?" + urllib.parse.urlencode(params)
