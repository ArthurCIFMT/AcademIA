import sys
from pathlib import Path

# O simulador executa a partir da raiz e tem dependências no venv do backend.
sys.path.insert(0, str(Path(__file__).resolve().parents[4]))
