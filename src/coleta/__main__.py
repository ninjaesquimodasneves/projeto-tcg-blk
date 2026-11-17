"""CLI: PYTHONPATH=src python -m coleta (sem parametro de data) [RF-10, RF-11]."""

import logging
import sys

from coleta.orquestrador import main

logging.basicConfig(level=logging.INFO, format="%(message)s", stream=sys.stdout)
sys.exit(main())
