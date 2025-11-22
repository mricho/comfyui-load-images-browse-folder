import os
import torch
from node import LoadImagesFromFolder

# Create a dummy folder with images
os.makedirs("test_images", exist_ok=True)
from PIL import Image
img = Image.new('RGB', (64, 64), color = 'red')
img.save('test_images/img1.png')
img = Image.new('RGB', (64, 64), color = 'blue')
img.save('test_images/img2.png')

node = LoadImagesFromFolder()
try:
    # Test loading all
    images, masks = node.load_images("test_images", 0, 2, True)
    print(f"Loaded {images.shape[0]} images. Shape: {images.shape}")
    assert images.shape[0] == 2
    
    # Test batching
    images, masks = node.load_images("test_images", 0, 1, True)
    print(f"Batch 0: Loaded {images.shape[0]} images.")
    assert images.shape[0] == 1
    
    images, masks = node.load_images("test_images", 1, 1, True)
    print(f"Batch 1: Loaded {images.shape[0]} images.")
    assert images.shape[0] == 1
    
    print("Verification successful!")
except Exception as e:
    print(f"Verification failed: {e}")
    exit(1)
finally:
    import shutil
    shutil.rmtree("test_images")
