"""CLI: PYTHONPATH=src python -m silver (sem parametros) [RF-22, RF-24]."""

import logging
import sys

from silver.reprocessamento import main

logging.basicConfig(level=logging.INFO, format="%(message)s", stream=sys.stdout)
sys.exit(main())
