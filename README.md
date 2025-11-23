# ComfyUI Load Images Browse Folder

A ComfyUI custom node that allows you to browse and select a folder, then load and process all images from that folder **one at a time through the complete workflow** (like VideoHelperSuite's meta-batch processing).

## Features

- **Folder browsing interface** - Select folders through a user-friendly UI
- **Automatic meta-batch processing** - Each image runs through the entire workflow independently
- **One image at a time** - Perfect for preventing memory issues and processing images sequentially
- **Automatic sorting** - Optional alphabetical sorting of images
- **Format support** - Supports JPG, PNG, BMP, WebP, and TIFF image formats

## Installation

1. Clone this repository into your ComfyUI custom_nodes directory:
```bash
cd ComfyUI/custom_nodes
git clone <repository-url> comfyui-load-images-browse-folder
```

2. Restart ComfyUI

## Usage

Simply add the **"Load Images From Folder (Browse)"** node to your workflow:

1. Enter a folder path (or use the browse functionality if available)
2. The node will automatically process **one image at a time** through your entire workflow
3. If you have 10 images, the workflow will run 10 times (once per image)

### How it works differently from regular batch loading:

**Traditional batch loading:**
- All images load at once → All process through step 1 → All process through step 2 → etc.
- Preview nodes show all images in a grid

**This node (meta-batch):**
- Image 1: Load → Process completely through workflow → Save
- Image 2: Load → Process completely through workflow → Save
- Image 3: Load → Process completely through workflow → Save
- ...and so on

This is perfect for workflows where you want each image to be processed independently, matching VideoHelperSuite's behavior.

## Node Parameters

### Load Images From Folder (Browse)

- **folder_path** (required): Path to the folder containing images
- **sort** (optional, default: True): Sort images alphabetically

**Outputs:**
- **IMAGE**: Currently loaded image (1 image per workflow execution)
- **frame_count**: Number of images in this batch (always 1)

## Example Use Cases

- **Sequential img2img processing**: Process each source image through the pipeline independently
- **Batch upscaling**: Upscale images one at a time to avoid memory issues  
- **Iterative processing**: Any workflow where each image needs independent processing

## Credits

Meta-batch processing implementation inspired by [ComfyUI-VideoHelperSuite](https://github.com/Kosinkadink/ComfyUI-VideoHelperSuite).
