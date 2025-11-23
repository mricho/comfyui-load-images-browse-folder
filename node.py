import os
import torch
import numpy as np
from PIL import Image, ImageOps
from server import PromptServer
from aiohttp import web

def images_generator(folder_path, sort=True, meta_batch=None, unique_id=None):
    """Generator that yields images one at a time for meta-batch processing"""
    if not os.path.isdir(folder_path):
        raise FileNotFoundError(f"Folder not found: {folder_path}")

    files = [f for f in os.listdir(folder_path) if os.path.isfile(os.path.join(folder_path, f))]
    
    valid_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.webp', '.tiff'}
    files = [f for f in files if os.path.splitext(f)[1].lower() in valid_extensions]

    if sort:
        files.sort()

    if not files:
        raise FileNotFoundError(f"No images found in folder {folder_path}")

    # Yield total count for meta_batch setup
    if meta_batch is not None:
        yield len(files)

    for filename in files:
        image_path = os.path.join(folder_path, filename)
        try:
            i = Image.open(image_path)
            i = ImageOps.exif_transpose(i)
            
            if i.mode == 'I':
                i = i.point(lambda i: i * (1 / 255))
            image = i.convert("RGB")
            image = np.array(image).astype(np.float32) / 255.0
            image = torch.from_numpy(image)
            
            yield image
        except Exception as e:
            print(f"Error loading image {filename}: {e}")
            continue

    # Mark inputs as closed for meta_batch
    if meta_batch is not None:
        meta_batch.inputs.pop(unique_id, None)
        meta_batch.has_closed_inputs = True


class LoadImagesFromFolder:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "folder_path": ("STRING", {"default": "", "multiline": False}),
                "sort": ("BOOLEAN", {"default": True}),
            },
            "optional": {
                "meta_batch": ("BATCH_MANAGER",),
            },
            "hidden": {
                "unique_id": "UNIQUE_ID"
            },
        }

    RETURN_TYPES = ("IMAGE", "INT")
    RETURN_NAMES = ("IMAGE", "frame_count")
    FUNCTION = "load_images"
    CATEGORY = "image"

    def load_images(self, folder_path, sort, meta_batch=None, unique_id=None):
        # Initialize generator if this is first run or meta_batch is not being used
        if meta_batch is None or unique_id not in meta_batch.inputs:
            gen = images_generator(folder_path, sort, meta_batch, unique_id)
            
            if meta_batch is not None:
                # Get total image count
                total_frames = next(gen)
                meta_batch.inputs[unique_id] = gen
                # Set frames_per_batch to total number of images as user requested
                meta_batch.total_frames = min(meta_batch.total_frames, total_frames)
        else:
            # Retrieve existing generator
            gen = meta_batch.inputs[unique_id]

        # Collect images for this batch
        images = []
        try:
            if meta_batch is not None:
                # Load frames_per_batch images
                for _ in range(meta_batch.frames_per_batch):
                    image = next(gen)
                    images.append(image)
            else:
                # Load all images at once (no meta_batch)
                for image in gen:
                    images.append(image)
        except StopIteration:
            pass

        if not images:
            print(f"Warning: No images loaded from folder {folder_path}")
            return (torch.zeros((1, 64, 64, 3), dtype=torch.float32), 0)

        # Stack images into batch
        output_images = torch.stack(images, dim=0)
        frame_count = len(images)

        # Requeue workflow if meta_batch is active and has more images
        if meta_batch is not None and not meta_batch.has_closed_inputs:
            from .utils import requeue_workflow
            requeue_workflow((meta_batch.unique_id, True))

        return (output_images, frame_count)

    @classmethod
    def IS_CHANGED(s, folder_path, sort, **kwargs):
        return float("nan")  # Always re-run to check for new files or changes

# API Endpoints for Directory Browsing

@PromptServer.instance.routes.post("/antigravity/browse/get_directory")
async def api_get_directory(request):
    try:
        data = await request.json()
        path = data.get("path", "")
        
        if not path:
            path = os.path.expanduser("~")
        
        if not os.path.isdir(path):
             return web.json_response({"error": "Directory not found", "path": path}, status=404)

        # List directories and files
        items = []
        try:
            with os.scandir(path) as entries:
                for entry in entries:
                    if entry.is_dir() and not entry.name.startswith('.'):
                        items.append({
                            "name": entry.name,
                            "type": "dir",
                            "path": entry.path
                        })
        except PermissionError:
             return web.json_response({"error": "Permission denied", "path": path}, status=403)

        # Sort items: directories first, then alphabetical
        items.sort(key=lambda x: x['name'].lower())
        
        parent = os.path.dirname(path)
        
        return web.json_response({
            "current_path": path,
            "parent_path": parent,
            "items": items
        })
    except Exception as e:
        return web.json_response({"error": str(e)}, status=500)
