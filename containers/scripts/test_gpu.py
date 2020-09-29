"""Docker GPU test script"""
import sys
import tensorflow as tf

print(f"GPUs Available: {len(tf.config.experimental.list_physical_devices('GPU'))}")
print(sys.version)
