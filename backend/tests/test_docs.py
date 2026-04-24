from pathlib import Path


def test_readme_mentions_public_data_key_and_start_commands():
    readme = Path('../README.md').read_text(encoding='utf-8')
    assert 'PUBLIC_DATA_SERVICE_KEY' in readme
    assert 'uvicorn app.main:app --reload' in readme
