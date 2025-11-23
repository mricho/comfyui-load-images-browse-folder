class BatchManager:
    """
    Manages meta-batch processing to enable processing images one at a time
    through the entire workflow, similar to VideoHelperSuite's batch manager.
    """
    def __init__(self):
        self.inputs = {}
        self.outputs = {}
        self.frames_per_batch = 1  # Process 1 image at a time by default
        self.total_frames = float('inf')
        self.has_closed_inputs = False
        self.unique_id = None

    def reset(self):
        self.inputs = {}
        self.outputs = {}
        self.has_closed_inputs = False


class BatchManagerNode:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "frames_per_batch": ("INT", {"default": 1, "min": 1, "max": 10000, "step": 1}),
            },
            "hidden": {
                "unique_id": "UNIQUE_ID"
            },
        }

    RETURN_TYPES = ("BATCH_MANAGER",)
    FUNCTION = "create_batch_manager"
    CATEGORY = "image"

    def __init__(self):
        self.batch_manager = None

    def create_batch_manager(self, frames_per_batch, unique_id=None):
        if self.batch_manager is None:
            self.batch_manager = BatchManager()
        self.batch_manager.frames_per_batch = frames_per_batch
        self.batch_manager.unique_id = unique_id
        return (self.batch_manager,)
