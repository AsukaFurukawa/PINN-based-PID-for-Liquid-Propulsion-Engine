#!/usr/bin/env python3
"""
Run the rocket engine visualization showcase dashboard.
This script launches a comprehensive visualization showcase that demonstrates 
all the different visualization techniques implemented in the project.
"""

import streamlit as st
import sys
import os

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import the showcase dashboard
from visualization.showcase_dashboard import create_showcase_dashboard

if __name__ == "__main__":
    # Run the showcase dashboard
    create_showcase_dashboard() 