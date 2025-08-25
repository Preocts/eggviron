from __future__ import annotations

import logging
import os


class EnvironLoader:
    """Load os.environ values"""

    log = logging.getLogger("eggviron")
    name = "EnvironLoader"

    def run(self) -> dict[str, str]:
        """Fetch all of os.environ key:value pairs."""
        return dict(os.environ)
