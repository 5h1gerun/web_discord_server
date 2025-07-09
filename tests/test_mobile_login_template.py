from pathlib import Path

TEMPLATE = Path(__file__).resolve().parents[1] / 'web' / 'templates' / 'mobile' / 'login.html'


def test_mobile_login_has_discord_join_link():
    text = TEMPLATE.read_text(encoding='utf-8')
    assert 'アカウントをお持ちでない方は' in text
    assert 'Discordに参加' in text
