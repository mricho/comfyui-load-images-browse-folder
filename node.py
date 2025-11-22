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
                "batch_index": ("INT", {"default": 0, "min": 0, "max": 999999}),
                "batch_size": ("INT", {"default": 1, "min": 1, "max": 64}),
                "sort": ("BOOLEAN", {"default": True}),
            }
        }

    RETURN_TYPES = ("IMAGE", "MASK")
    FUNCTION = "load_images"
    CATEGORY = "image"

    def load_images(self, folder_path, batch_index, batch_size, sort):
        if not os.path.isdir(folder_path):
            raise FileNotFoundError(f"Folder not found: {folder_path}")

        files = [f for f in os.listdir(folder_path) if os.path.isfile(os.path.join(folder_path, f))]
        
        valid_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.webp', '.tiff'}
        files = [f for f in files if os.path.splitext(f)[1].lower() in valid_extensions]

        if sort:
            files.sort()

        start_idx = batch_index * batch_size
        end_idx = start_idx + batch_size
        
        # Handle wrap-around or clamping if needed, but for now strict indexing
        if start_idx >= len(files):
            # Return empty or raise error? Standard is usually error or empty.
            # Let's return a single black frame to avoid crashing workflows if index goes over
            print(f"Warning: Batch index {batch_index} out of range for folder with {len(files)} images.")
            return (torch.zeros((1, 64, 64, 3), dtype=torch.float32), torch.zeros((1, 64, 64), dtype=torch.float32))

        selected_files = files[start_idx:end_idx]
        
        images = []
        masks = []

        for filename in selected_files:
            image_path = os.path.join(folder_path, filename)
            try:
                i = Image.open(image_path)
                i = ImageOps.exif_transpose(i)
                
                if i.mode == 'I':
                    i = i.point(lambda i: i * (1 / 255))
                image = i.convert("RGB")
                image = np.array(image).astype(np.float32) / 255.0
                image = torch.from_numpy(image)[None,]
                
                if 'A' in i.getbands():
                    mask = np.array(i.getchannel('A')).astype(np.float32) / 255.0
                    mask = 1. - torch.from_numpy(mask)
                else:
                    mask = torch.zeros((image.shape[1], image.shape[2]), dtype=torch.float32, device="cpu")
                
                images.append(image)
                masks.append(mask)
            except Exception as e:
                print(f"Error loading image {filename}: {e}")
                continue

        if images:
            # Find max dimensions to pad to
            max_h = max(img.shape[1] for img in images)
            max_w = max(img.shape[2] for img in images)
            
            padded_images = []
            padded_masks = []
            
            for img, mask in zip(images, masks):
                h, w = img.shape[1], img.shape[2]
                pad_h = max_h - h
                pad_w = max_w - w
                
                if pad_h > 0 or pad_w > 0:
                    # Pad image
                    img = torch.nn.functional.pad(img.permute(0, 3, 1, 2), (0, pad_w, 0, pad_h), mode='constant', value=0)
                    img = img.permute(0, 2, 3, 1)
                    
                    # Pad mask
                    mask = torch.nn.functional.pad(mask.unsqueeze(0), (0, pad_w, 0, pad_h), mode='constant', value=0).squeeze(0)
                
                padded_images.append(img)
                padded_masks.append(mask)

            output_image = torch.cat(padded_images, dim=0)
            output_mask = torch.cat([m[None,] for m in padded_masks], dim=0)
        else:
            output_image = torch.zeros((1, 64, 64, 3), dtype=torch.float32)
            output_mask = torch.zeros((1, 64, 64), dtype=torch.float32)

        return (output_image, output_mask)

    @classmethod
    def IS_CHANGED(s, folder_path, batch_index, batch_size, sort):
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
