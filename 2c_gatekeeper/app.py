import json
import time
from ferris_cli.v2 import FerrisEvents
from ferris_ef import context

def send_event(job_data, cand_data):
    try:
        print(f"Attempting to send event ferris.apps.hr.coverage_ratio")
        print(f"Sender: {context.package.name}")
        print(f"Payload: {json.dumps({'job_data': job_data, 'cand_data': cand_data}, indent=2)}")
        
        context.events.send(
            "ferris.apps.hr.coverage_ratio",
            context.package.name,
            {
                'job_data': job_data,
                'cand_data': cand_data
            }
        )
        print(f"Event ferris.apps.hr.coverage_ratio sent successfully")
        print("Job Data: ", job_data)
        print("Candidate Data: ", cand_data)
    except Exception as e:
        print(f"Error sending event: {str(e)}")
        raise  # Re-raise the exception to ensure it's properly logged in the system


def main():
    # Define the predefined array of event types and their error counterparts
    predefined_events = ["ferris.apps.hr.job_extract", "ferris.apps.hr.cand_extract"]
    error_events = ["ferris.apps.hr.job_error", "ferris.apps.hr.cand_error"]

    # Get the current execution ID to ensure we're tracking events for this run only
    current_exec_id = context.params.get('_fxparentexec')
    
    # Retrieve the current state
    state = context.state.get()
    print("Current state:", state)
    
    # Initialize state if needed
    if 'executions' not in state:
        state['executions'] = {}
    if current_exec_id not in state['executions']:
        state['executions'][current_exec_id] = {
            'seen_events': [],
            'job_data': None,
            'cand_data': None
        }
    
    # Get state for current execution
    exec_state = state['executions'][current_exec_id]
    
    # Retrieve the incoming event type
    incoming_event = context.params.get('origin_event_type')
    print(f"Processing event {incoming_event} for execution {current_exec_id}")

    # If we receive an error event, clear the state for this execution
    if incoming_event in error_events:
        print(f"Received error event: {incoming_event}. Clearing state for execution {current_exec_id}")
        del state['executions'][current_exec_id]
        context.state.put('executions', state['executions'])
        return

    if incoming_event == 'ferris.apps.hr.job_extract':
        exec_state['job_data'] = {
            "job_name": context.params.get('job'),
            "job_industry": context.params.get('job_industry'),
            "job_hard_skills": context.params.get('job_hard_skills'),
            "job_soft_skills": context.params.get('job_soft_skills'),
            "job_language_skills": context.params.get('job_language_skills')
        }

    if incoming_event == 'ferris.apps.hr.cand_extract':
        exec_state['cand_data'] = {
            "candidate_name": context.params.get('candidate'),
            "candidate_industry": context.params.get('candidate_industry'),
            "candidate_hard_skills": context.params.get('candidate_hard_skills'),
            "candidate_soft_skills": context.params.get('candidate_soft_skills'),
            "candidate_language_skills": context.params.get('candidate_language_skills'),
            "candidate_experience": context.params.get("candidate_experience", [])
        }
    
    # Add the incoming event to the 'seen_events' array if not already present
    if incoming_event in predefined_events and incoming_event not in exec_state['seen_events']:
        exec_state['seen_events'].append(incoming_event)
    
    # Update state
    state['executions'][current_exec_id] = exec_state
    context.state.put('executions', state['executions'])

    # Wait loop to ensure both events are received
    max_wait_time = 300  # 5 minutes maximum wait time
    wait_interval = 5    # Check every 5 seconds
    start_time = time.time()

    while True:
        # Check if we've exceeded the maximum wait time
        if time.time() - start_time > max_wait_time:
            print(f"Timeout waiting for events after {max_wait_time} seconds")
            print(f"Current events received: {exec_state['seen_events']}")
            return

        # Check if all predefined events are seen for this execution
        if all(event in exec_state['seen_events'] for event in predefined_events):
            print(f"All events received for execution {current_exec_id}")
            
            job_payload = exec_state['job_data']
            cand_payload = exec_state['cand_data']

            if not job_payload or not cand_payload:
                print("Missing required data. Job or Candidate data is empty.")
                return

            # Send event and clean up state
            send_event(job_payload, cand_payload)
            del state['executions'][current_exec_id]
            context.state.put('executions', state['executions'])
            return

        print(f"Waiting for remaining events. Current events: {exec_state['seen_events']}")
        time.sleep(wait_interval)

        # Refresh state to check for new events
        state = context.state.get()
        exec_state = state['executions'][current_exec_id]

main()

