import os
import torch
import numpy as np
from PIL import Image, ImageOps
from server import PromptServer
from aiohttp import web

class LoadImagesFromFolder:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "folder_path": ("STRING", {"default": "", "multiline": False}),
                "sort": ("BOOLEAN", {"default": True}),
            }
        }

    RETURN_TYPES = ("IMAGE",)
    OUTPUT_IS_LIST = (True,)
    FUNCTION = "load_images"
    CATEGORY = "image"

    def load_images(self, folder_path, sort):
        if not os.path.isdir(folder_path):
            raise FileNotFoundError(f"Folder not found: {folder_path}")

        files = [f for f in os.listdir(folder_path) if os.path.isfile(os.path.join(folder_path, f))]
        
        valid_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.webp', '.tiff'}
        files = [f for f in files if os.path.splitext(f)[1].lower() in valid_extensions]

        if sort:
            files.sort()

        if not files:
            # Return empty list if no images found
            print(f"Warning: No images found in folder {folder_path}")
            return ([],)

        images = []

        for filename in files:
            image_path = os.path.join(folder_path, filename)
            try:
                i = Image.open(image_path)
                i = ImageOps.exif_transpose(i)
                
                if i.mode == 'I':
                    i = i.point(lambda i: i * (1 / 255))
                image = i.convert("RGB")
                image = np.array(image).astype(np.float32) / 255.0
                image = torch.from_numpy(image)[None,]
                
                images.append(image)
            except Exception as e:
                print(f"Error loading image {filename}: {e}")
                continue

        return (images,)

    @classmethod
    def IS_CHANGED(s, folder_path, sort):
        return float("nan") # Always re-run to check for new files or changes

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
