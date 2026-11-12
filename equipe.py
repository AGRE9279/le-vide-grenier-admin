"""Blackist — point d'entrée de l'Espace équipe & partenaires.
Même code que app.py ; la différence vient du secret ESPACE = "equipe"."""
import runpy
from pathlib import Path

runpy.run_path(str(Path(__file__).with_name("app.py")), run_name="__main__")
