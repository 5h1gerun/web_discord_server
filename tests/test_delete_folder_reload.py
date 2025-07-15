from pathlib import Path

TEMPLATE = Path(__file__).resolve().parents[1] / 'web' / 'templates' / 'index.html'
MOBILE_TEMPLATE = Path(__file__).resolve().parents[1] / 'web' / 'templates' / 'mobile' / 'index.html'


def test_folder_delete_forms_have_class():
    text = TEMPLATE.read_text(encoding='utf-8')
    mobile = MOBILE_TEMPLATE.read_text(encoding='utf-8')
    assert 'action="/delete_folder/' in text
    assert 'class="delete-form"' in text
    assert 'action="/delete_subfolders"' in text
    assert 'class="delete-form"' in text
    assert 'action="/delete_folder/' in mobile
    assert 'class="delete-form"' in mobile
    assert 'action="/delete_subfolders"' in mobile
    assert 'class="delete-form"' in mobile
