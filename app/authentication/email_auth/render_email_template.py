from html import escape
from pathlib import Path

_TEMPLATE_DIRECTORY = Path(__file__).parent.parent / "auth_templates"


def render_email_template(
    template_name: str,
    *,
    escape_values: bool = True,
    **values: str,
) -> str:
    template = (_TEMPLATE_DIRECTORY / template_name).read_text(encoding="utf-8")
    for key, value in values.items():
        rendered_value = escape(value, quote=True) if escape_values else value
        template = template.replace(f"{{{{{key}}}}}", rendered_value)
    return template
