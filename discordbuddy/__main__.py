"""Package entrypoint when invoked via `python -m discordbuddy`."""

import sys
from discordbuddy.main import main

if __name__ == "__main__":
    sys.exit(main())
