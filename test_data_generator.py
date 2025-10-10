"""
Quick test to generate 50 realistic shipments first
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from generate_realistic_data import *

# Override the total for testing
TOTAL_SHIPMENTS = 50

if __name__ == "__main__":
    main()