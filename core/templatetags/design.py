import json
from pathlib import Path
from django import template
from django.conf import settings
from django.templatetags.static import static
from django.utils.html import format_html

register = template.Library()
ASSETS = json.loads((settings.BASE_DIR / 'reference/assets.json').read_text())

@register.simple_tag
def asset(page, name):
    return static(ASSETS[page][name]['path'].removeprefix('static/'))

@register.simple_tag
def icon(name, page='documents'):
    key = 'imgIcon' + name
    if key not in ASSETS[page]:
        key = 'imgIconDoc'
    return format_html('<img class="icon" src="{}" alt="" loading="lazy">', asset(page, key))
