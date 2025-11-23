# ComfyUI Load Images Browse Folder

A ComfyUI custom node that allows you to browse and select a folder, then load all images from that folder for processing.

## Features

- **Folder browsing interface** - Select folders through a user-friendly UI
- **Batch image loading** - Load all images from a selected folder
- **Meta-batch processing** - Process each image through the entire workflow independently (like VideoHelperSuite)
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

### Basic Usage (All Images at Once)

1. Add the **"Load Images From Folder (Browse)"** node to your workflow
2. Enter a folder path or use the browse functionality
3. All images will be loaded and processed as a batch

### Meta-Batch Processing (One Image at a Time)

To process each image through the entire workflow independently:

1. Add a **"Batch Manager"** node to your workflow
2. Set `frames_per_batch` to `1` (process one image at a time)
3. Connect the Batch Manager output to the **"Load Images From Folder (Browse)"** node's `meta_batch` input
4. The workflow will automatically run once for each image in the folder

**Why use meta-batch processing?**
- Each image goes through the complete workflow independently
- Preview nodes show one image at a time instead of all images in a grid
- Better memory management for large image sets
- Matches VideoHelperSuite's behavior

## Node Parameters

### Load Images From Folder (Browse)

- **folder_path** (required): Path to the folder containing images
- **sort** (optional, default: True): Sort images alphabetically
- **meta_batch** (optional): Connect a Batch Manager to enable per-image processing

**Outputs:**
- **IMAGE**: Loaded image(s)
- **frame_count**: Number of images loaded in this batch

### Batch Manager

- **frames_per_batch** (default: 1): Number of images to process per workflow execution

**Outputs:**
- **BATCH_MANAGER**: Manager object for meta-batch processing

## Example Workflows

### Process each image individually through img2img:
```
[Batch Manager] → [Load Images From Folder] → [img2img pipeline] → [Save Image]
  (frames_per_batch: 1)
```

### Load all images at once for comparison:
```
[Load Images From Folder] → [Preview Node]
  (no Batch Manager connected)
```

## Credits

Meta-batch processing implementation inspired by [ComfyUI-VideoHelperSuite](https://github.com/Kosinkadink/ComfyUI-VideoHelperSuite).
