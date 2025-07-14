from pathlib import Path

APP_PATH = Path(__file__).resolve().parents[1] / "web" / "app.py"
JS_PATH = Path(__file__).resolve().parents[1] / "web" / "static" / "js" / "main.js"
CSS_PATH = Path(__file__).resolve().parents[1] / "web" / "static" / "css" / "style.css"
PHONE_CSS_PATH = Path(__file__).resolve().parents[1] / "web" / "static" / "css" / "style-phone.css"


def test_app_expiration_newline():
    text = APP_PATH.read_text(encoding="utf-8")
    assert "\n" in text


def test_js_expiration_newline():
    text = JS_PATH.read_text(encoding="utf-8")
    assert "\\n${line2.join" in text


def test_css_preline():
    text = CSS_PATH.read_text(encoding="utf-8")
    assert "white-space: pre-line;" in text
    phone = PHONE_CSS_PATH.read_text(encoding="utf-8")
    assert "white-space: pre-line;" in phone
