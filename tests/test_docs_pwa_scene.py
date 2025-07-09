from pathlib import Path

def test_sequence_pwa_exists():
    path = Path(__file__).resolve().parents[1] / 'docs' / 'sequence_pwa.mmd'
    assert path.exists(), 'sequence_pwa.mmd should exist'
    text = path.read_text(encoding='utf-8')
    assert 'PWA' in text
    assert 'sequenceDiagram' in text
