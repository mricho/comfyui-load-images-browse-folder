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
    (_, _, prompt, extra_data, outputs_to_execute) = next(iter(currently_running.values()))

    # Ensure batch_managers are marked stale
    prompt = prompt.copy()
    for uid in prompt:
        if prompt[uid].get('class_type') == 'BatchManager':
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
    (run_number, _, prompt, _, _) = next(iter(prompt_queue.currently_running.values()))
    
    if requeue_guard[0] != run_number:
        # Calculate a count of how many outputs are managed by a batch manager
        managed_outputs = 0
        for bm_uid in prompt:
            if prompt[bm_uid].get('class_type') == 'BatchManager':
                for output_uid in prompt:
                    # Check if any node uses this batch manager
                    for inp in prompt[output_uid].get('inputs', {}).values():
                        if inp == [bm_uid, 0]:
                            managed_outputs += 1
        requeue_guard = [run_number, 0, managed_outputs, {}]
    
    requeue_guard[1] = requeue_guard[1] + 1
    requeue_guard[3][requeue_required[0]] = requeue_required[1]
    
    if requeue_guard[1] == requeue_guard[2] and max(requeue_guard[3].values()):
        requeue_workflow_unchecked()

