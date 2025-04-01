# utils.py

import warnings
warnings.filterwarnings("ignore", category=FutureWarning)

import logging
logging.basicConfig(level=logging.CRITICAL)
logging.getLogger('soccerdata').setLevel(logging.CRITICAL)
logging.disable(logging.INFO)

import pandas as pd
import numpy as np
import soccerdata as sd
from understatapi import UnderstatClient

