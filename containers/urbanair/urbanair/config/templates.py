"""
Gets template directory paths
"""

# pylint: disable=C0103

from pathlib import Path

from fastapi.templating import Jinja2Templates

TEMPLATE_DIR = Path(__file__).parent.parent / "templates"

templates = Jinja2Templates(directory=str(TEMPLATE_DIR.absolute()))

auth_templates = Jinja2Templates(directory=str((TEMPLATE_DIR / "auth").absolute()))
