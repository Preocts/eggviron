from __future__ import annotations

import logging
import os


class EnvironLoader:
    """Load os.environ values"""

    log = logging.getLogger("eggviron")
    name = "EnvironLoader"

    def run(self) -> dict[str, str]:
        """Fetch all of os.environ key:value pairs."""
        for key, value in os.environ.items():
            self.log.debug("Found, %s : ***%s", key, value[-(len(value) // 4) :])

        return dict(os.environ)
