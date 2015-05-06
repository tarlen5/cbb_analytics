#! /usr/bin/env python
#
# author: Timothy C. Arlen
#         timothyarlen@gmail.com
#
# A set of logging utilities.
#

import pandas as pd
import logging
import logging.config

def set_verbosity(verbosity):

    logconfig = {
        "version" : 1,
        "formatters": {
            "simple": { "format": "[%(levelname)8s] %(message)s" }
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "formatter": "simple",
                "stream": "ext://sys.stdout"
            }
        },
        "root": {
            "handlers": [ "console" ],
            "level": "WARN"
        }
    }

    logging.config.dictConfig(logconfig)
    if verbosity is None: return

    levels = {0:logging.WARN,1:logging.INFO,2:logging.DEBUG}
    logging.root.setLevel(levels[min(2,verbosity)])
    return

def set_frame_display(max_cols, expand_frame=False, max_rows=20):
    """
    Set properties to display DataFrame
    """

    pd.set_option('display.max_columns', max_cols)
    pd.set_option('expand_frame_repr', expand_frame)
    pd.set_option('max_rows',max_rows)

    return
