from pathlib import Path

from django.urls import reverse


def ai_advisor_url(request):
    return {'AI_ADVISOR_URL': reverse('advisor-home')}


def asset_version(request):
    """Cache-buster for the site's CSS/JS files: changes whenever any of them changes.

    Production already serves hashed filenames (ManifestStaticFilesStorage); this
    mainly stops browsers reusing stale copies from the dev server.
    """
    folder = Path(__file__).resolve().parent / 'static' / 'home'
    try:
        stamp = max(int(f.stat().st_mtime) for f in folder.glob('*.[cj]s*'))
    except OSError:
        stamp = 0
    return {'ASSET_VERSION': str(stamp)}  # str: avoid locale thousand separators
