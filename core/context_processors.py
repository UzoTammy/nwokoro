from pathlib import Path

from django.urls import reverse


def ai_advisor_url(request):
    return {'AI_ADVISOR_URL': reverse('advisor-home')}


def asset_version(request):
    """Cache-buster for the site stylesheet/script: changes whenever either file changes.

    Production already serves hashed filenames (ManifestStaticFilesStorage); this
    mainly stops browsers reusing stale copies from the dev server.
    """
    folder = Path(__file__).resolve().parent / 'static' / 'home'
    try:
        stamp = max(int((folder / name).stat().st_mtime) for name in ('home.css', 'home.js'))
    except OSError:
        stamp = 0
    return {'ASSET_VERSION': str(stamp)}  # str: avoid locale thousand separators
