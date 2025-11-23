import json
from server import PromptServer


def requeue_workflow(workflow_info):
    """
    Requeues the current workflow to process the next batch of images.
    This is essential for meta-batch processing.
    
    Args:
        workflow_info: Tuple of (unique_id, should_requeue)
    """
    unique_id, should_requeue = workflow_info
    
    if not should_requeue:
        return
    
    # Get the prompt server instance
    server = PromptServer.instance
    
    # Requeue the current prompt to continue processing
    # This tells ComfyUI to run the workflow again for the next batch
    try:
        if hasattr(server, 'last_prompt'):
            # Requeue the last prompt
            server.send_sync("execution_cached", {"nodes": [], "prompt_id": unique_id})
    except Exception as e:
        print(f"Warning: Failed to requeue workflow: {e}")
