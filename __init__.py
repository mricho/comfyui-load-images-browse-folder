from .node import LoadImagesFromFolder
from .batch_manager import BatchManagerNode

NODE_CLASS_MAPPINGS = {
    "LoadImagesFromFolder": LoadImagesFromFolder,
    "BatchManager": BatchManagerNode
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "LoadImagesFromFolder": "Load Images From Folder (Browse)",
    "BatchManager": "Batch Manager"
}

WEB_DIRECTORY = "./js"

__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS", "WEB_DIRECTORY"]
