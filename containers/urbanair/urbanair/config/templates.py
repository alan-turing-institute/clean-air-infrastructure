from fastapi.templating import Jinja2Templates
from pathlib import Path


template_dir = Path(__file__).parent.parent / "templates"

templates = Jinja2Templates(directory=str(template_dir.absolute()))

auth_templates = Jinja2Templates(directory=str((template_dir / "auth").absolute()))
