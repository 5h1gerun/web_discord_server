from pathlib import Path

TEMPLATES = [
    Path(__file__).resolve().parents[1] / 'web' / 'templates' / 'base.html',
    Path(__file__).resolve().parents[1] / 'web' / 'templates' / 'base_public.html',
    Path(__file__).resolve().parents[1] / 'web' / 'templates' / 'mobile' / 'base_phone.html',
    Path(__file__).resolve().parents[1] / 'web' / 'templates' / 'mobile' / 'base_mobile.html',
    Path(__file__).resolve().parents[1] / 'web' / 'templates' / 'mobile' / 'base_friendly.html',
]


def test_body_has_logged_in_attr():
    for tpl in TEMPLATES:
        text = tpl.read_text(encoding='utf-8')
        assert 'data-logged-in="{{ 1 if user_id else 0 }}"' in text
