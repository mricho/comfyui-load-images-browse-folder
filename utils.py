import json
import copy
import server
import uuid


# Get prompt queue instance
prompt_queue = server.PromptServer.instance.prompt_queue

# Guard to prevent multiple requeues
requeue_guard = [None, 0, 0, {}]


def requeue_workflow_unchecked():
    """Requeues the current workflow without checking for multiple requeues"""
    currently_running = prompt_queue.currently_running
    values = next(iter(currently_running.values()))
    
    # Handle different ComfyUI versions - unpack appropriately
    if len(values) == 6:
        (_, _, prompt, extra_data, outputs_to_execute, _) = values
    elif len(values) == 5:
        (_, _, prompt, extra_data, outputs_to_execute) = values
    else:
        print(f"Warning: Unexpected prompt_queue structure with {len(values)} values")
        return

    # Ensure batch_managers are marked stale
    prompt = prompt.copy()
    for uid in prompt:
        if prompt[uid].get('class_type') == 'LoadImagesFromFolder':
            if 'requeue' not in prompt[uid].get('inputs', {}):
                prompt[uid]['inputs'] = prompt[uid].get('inputs', {}).copy()
            prompt[uid]['inputs']['requeue'] = prompt[uid]['inputs'].get('requeue', 0) + 1

    # execution.py has guards for concurrency, but server doesn't
    number = -server.PromptServer.instance.number
    server.PromptServer.instance.number += 1
    prompt_id = str(uuid.uuid4())
    prompt_queue.put((number, prompt_id, prompt, extra_data, outputs_to_execute))


def requeue_workflow(requeue_required=(-1, True)):
    """
    Requeues the current workflow to process the next batch of images.
    Based on VideoHelperSuite's implementation.
    
    Args:
        requeue_required: Tuple of (unique_id, should_requeue)
    """
    if len(prompt_queue.currently_running) != 1:
        return
    
    global requeue_guard
    values = next(iter(prompt_queue.currently_running.values()))
    
    # Handle different ComfyUI versions
    if len(values) == 6:
        (run_number, _, prompt, _, _, _) = values
    elif len(values) == 5:
        (run_number, _, prompt, _, _) = values
    else:
        print(f"Warning: Cannot requeue - unexpected prompt_queue structure")
        return
    
    if requeue_guard[0] != run_number:
        # Count how many LoadImagesFromFolder nodes exist (each needs to report back)
        managed_outputs = 0
        for uid in prompt:
            if prompt[uid].get('class_type') == 'LoadImagesFromFolder':
                managed_outputs += 1
        managed_outputs = max(managed_outputs, 1) # Ensure at least 1 if no LoadImagesFromFolder nodes are found
        requeue_guard = [run_number, 0, managed_outputs, {}]
    
    requeue_guard[1] = requeue_guard[1] + 1
    requeue_guard[3][requeue_required[0]] = requeue_required[1]
    
    if requeue_guard[1] >= requeue_guard[2] and max(requeue_guard[3].values()):
        requeue_workflow_unchecked()
