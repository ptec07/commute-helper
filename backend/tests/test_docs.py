from pathlib import Path


def test_readme_mentions_public_data_key_and_start_commands():
    readme = Path('../README.md').read_text(encoding='utf-8')
    assert 'PUBLIC_DATA_SERVICE_KEY' in readme
    assert 'uvicorn app.main:app --reload' in readme


def test_readme_documents_live_provider_precedence_and_frontend_api_base_url():
    readme = Path('../README.md').read_text(encoding='utf-8')
    assert 'public-data primary' in readme
    assert 'ODsay backup' in readme
    assert 'VITE_API_BASE_URL' in readme


def test_github_workflow_uses_render_api_key_header_without_redacted_placeholder():
    workflow = Path('../.github/workflows/github-first-deploy.yml').read_text(encoding='utf-8')
    assert 'Authorization: Bearer $RENDER_API_KEY' in workflow
    assert 'Authorization: Bearer ***' not in workflow


def test_github_workflow_sets_public_api_base_url_for_vercel_build():
    workflow = Path('../.github/workflows/github-first-deploy.yml').read_text(encoding='utf-8')
    assert 'VITE_API_BASE_URL: https://commute-helper-backend.onrender.com' in workflow
