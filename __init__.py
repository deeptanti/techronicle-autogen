"""
TechRonicle AutoGen - An Agentic AI Application
Multi-agent crypto newsroom for automated content curation
"""

__version__ = "1.0.0"
__author__ = "TechRonicle Team"
__description__ = "Multi-agent crypto newsroom for automated content curation and editorial workflows"

# Import main modules for easy access
from . import utils
from . import agents

# Make key components available at package level
try:
    from .app import main as streamlit_main
except ImportError:
    streamlit_main = None

try:
    from .main import main as cli_main
except ImportError:
    cli_main = None

# Key classes for direct import
from .agents.newsroom import TechronicleNewsroom
from .utils.config import config

__all__ = [
    "utils",
    "agents",
    "TechronicleNewsroom", 
    "config",
    "streamlit_main",
    "cli_main",
    "__version__",
    "__author__",
    "__description__"
]