import json
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

    # Retrieve the current state
    state = context.state.get()
    print("Current state:", state)
    
    # Initialize state if needed
    if 'events' not in state:
        state['events'] = {
            'seen_events': [],
            'job_data': None,
            'cand_data': None
        }
    
    # Get event state
    event_state = state['events']
    
    # Retrieve the incoming event type
    incoming_event = context.params.get('origin_event_type')
    print(f"Processing event {incoming_event}")

    # If we receive an error event, clear the state
    if incoming_event in error_events:
        print(f"Received error event: {incoming_event}. Clearing state.")
        state['events'] = {
            'seen_events': [],
            'job_data': None,
            'cand_data': None
        }
        context.state.put('events', state['events'])
        return

    if incoming_event == 'ferris.apps.hr.job_extract':
        event_state['job_data'] = {
            "job_name": context.params.get('job'),
            "job_industry": context.params.get('job_industry'),
            "job_hard_skills": context.params.get('job_hard_skills'),
            "job_soft_skills": context.params.get('job_soft_skills'),
            "job_language_skills": context.params.get('job_language_skills')
        }

    if incoming_event == 'ferris.apps.hr.cand_extract':
        event_state['cand_data'] = {
            "candidate_name": context.params.get('candidate'),
            "candidate_industry": context.params.get('candidate_industry'),
            "candidate_hard_skills": context.params.get('candidate_hard_skills'),
            "candidate_soft_skills": context.params.get('candidate_soft_skills'),
            "candidate_language_skills": context.params.get('candidate_language_skills'),
            "candidate_experience": context.params.get("candidate_experience", [])
        }
    
    # Add the incoming event to the 'seen_events' array if not already present
    if incoming_event in predefined_events and incoming_event not in event_state['seen_events']:
        event_state['seen_events'].append(incoming_event)
    
    # Update state
    state['events'] = event_state
    context.state.put('events', state['events'])

    # Check if all predefined events are seen
    if all(event in event_state['seen_events'] for event in predefined_events):
        print(f"All events received: {event_state['seen_events']}")
        
        job_payload = event_state['job_data']
        cand_payload = event_state['cand_data']

        if not job_payload or not cand_payload:
            print("Missing required data. Job or Candidate data is empty.")
            return

        # Send event
        send_event(job_payload, cand_payload)
        
        # Clean up state after sending the event
        print("Cleaning up state")
        state['events'] = {
            'seen_events': [],
            'job_data': None,
            'cand_data': None
        }
        context.state.put('events', state['events'])
    else:
        print(f"Waiting for remaining events. Current events: {event_state['seen_events']}")

main()

