"""Docker GPU test script"""
import tensorflow as tf

print(f"GPUs Available: {len(tf.config.experimental.list_physical_devices('GPU'))}")

import sys
print(sys.version)
