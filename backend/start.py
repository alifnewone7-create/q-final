#!/usr/bin/env python3
"""Binary Algo Prime — clean launcher.

Runs the Telegram bot but keeps the console silent: only a single
"Bot running..." line is shown. All library / pyquotex / telegram logs
and prints are suppressed.
"""
import os
import sys
import logging
import warnings

# ---- silence everything ----
warnings.filterwarnings("ignore")
logging.disable(logging.CRITICAL)            # drop every log record <= CRITICAL
for _name in list(logging.root.manager.loggerDict):
    _lg = logging.getLogger(_name)
    _lg.disabled = True
    _lg.propagate = False
logging.getLogger().handlers = []            # remove root handlers


def _run():
    # the ONLY thing the user should ever see on the console
    sys.__stdout__.write("Bot running...\n")
    sys.__stdout__.flush()

    # from here on, hide all stdout noise (pyquotex uses print())
    class _Null:
        def write(self, *_a, **_k):
            return 0

        def flush(self):
            pass

    sys.stdout = _Null()

    import bot  # obfuscated module
    try:
        bot.main()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    _run()
