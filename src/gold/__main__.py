"""CLI: PYTHONPATH=src python -m gold (sem parametros) [RF-50]."""

import logging
import sys

from gold.reprocessamento import main

logging.basicConfig(level=logging.INFO, format="%(message)s", stream=sys.stdout)
sys.exit(main())
