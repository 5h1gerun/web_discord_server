from pathlib import Path

APP_PATH = Path(__file__).resolve().parents[1] / 'web' / 'app.py'


def test_gdrive_flows_store_user():
    text = APP_PATH.read_text(encoding='utf-8')
    assert 'app["gdrive_flows"][state] = (flow, discord_id)' in text


def test_gdrive_callback_fallback():
    text = APP_PATH.read_text(encoding='utf-8')
    assert 'data = app["gdrive_flows"].pop(state or sess_state, None)' in text
    assert 'discord_id = sess.get("user_id", stored_id)' in text
