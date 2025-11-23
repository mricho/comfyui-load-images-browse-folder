from .node import LoadImagesFromFolder

NODE_CLASS_MAPPINGS = {
    "LoadImagesFromFolder": LoadImagesFromFolder
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "LoadImagesFromFolder": "Load Images From Folder (Browse)"
}

WEB_DIRECTORY = "./js"

__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS", "WEB_DIRECTORY"]
