from django import template
from django.utils.safestring import mark_safe

register = template.Library()


@register.simple_tag
def dst_active_theme():
    """Slug tema CMS aktif (luwu/pesisir/pegunungan/vulkanik/rawa).

    Dipakai pada atribut ``data-theme`` di <body> agar variabel warna tema
    berlaku global (landing, admin, viewer). Default 'luwu'.
    """
    try:
        from geonode_project.models import SiteIdentity

        return SiteIdentity.load().theme or "luwu"
    except Exception:
        return "luwu"


@register.simple_tag
def dst_theme_logo_url():
    """Return the URL of the active GeoNode theme logo, or '' if none set."""
    try:
        from geonode.themes.models import GeoNodeThemeCustomization

        theme = GeoNodeThemeCustomization.objects.filter(is_enabled=True).first()
        if theme and theme.logo:
            return theme.logo.url
    except Exception:
        pass
    return ""


def _site_from_db():
    """Site langsung dari DB (lewati SITE_CACHE per-worker) agar perubahan
    nama/domain langsung konsisten di semua worker uwsgi."""
    from django.conf import settings
    from django.contrib.sites.models import Site

    return Site.objects.get(pk=getattr(settings, "SITE_ID", 1))


@register.simple_tag
def dst_site_name(fallback="DST Kabupaten Luwu"):
    """Return the current Django Site.name, or fallback when unavailable."""
    try:
        name = (_site_from_db().name or "").strip()
        return name or fallback
    except Exception:
        return fallback


@register.simple_tag
def dst_site_domain(fallback=""):
    """Return the current Django Site.domain, or fallback when unavailable."""
    try:
        domain = (_site_from_db().domain or "").strip()
        return domain or fallback
    except Exception:
        return fallback


@register.simple_tag
def dst_font_vars():
    """Output Google Fonts <link> + CSS --serif/--sans/--mono dari SiteIdentity.font_combo()."""
    try:
        from geonode_project.models import SiteIdentity

        combo = SiteIdentity.load().font_combo()
    except Exception:
        combo = None
    if not combo:
        combo = {
            "serif": "'Fraunces', serif",
            "sans": "'Geist', sans-serif",
            "mono": "'Geist Mono', monospace",
        }

    families = []
    for key in ("serif", "sans", "mono"):
        fam = combo[key].split(",")[0].strip().strip("'\"")
        families.append(fam)

    gf = "https://fonts.googleapis.com/css2?" + "&".join(
        "family=" + f.replace(" ", "+") + ":ital,wght@0,400;0,600;0,700;1,400"
        for f in families
    )

    return mark_safe(
        '<link rel="preconnect" href="https://fonts.googleapis.com">'
        '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
        '<link href="' + gf + '" rel="stylesheet">'
        "<style>:root{--serif:" + combo["serif"] + ", serif;"
        + "--sans:" + combo["sans"] + ", system-ui, sans-serif;"
        + "--mono:" + combo["mono"] + ", monospace;}</style>"
    )
