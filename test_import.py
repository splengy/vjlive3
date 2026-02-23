import sys
print("Starting import test", flush=True)

print("Importing numpy", flush=True)
import numpy as np

print("Importing logging", flush=True)
import logging

print("Importing OpenGL", flush=True)
try:
    import OpenGL.GL as gl
except ImportError:
    pass

print("Importing EffectPlugin", flush=True)
from vjlive3.plugins.api import EffectPlugin, PluginContext

print("Importing vjlive3.plugins.depth_acid_fractal_datamosh", flush=True)
import vjlive3.plugins.depth_acid_fractal_datamosh

print("Success!", flush=True)
