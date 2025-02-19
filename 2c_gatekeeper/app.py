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
    
    # Retrieve the incoming event type
    incoming_event = context.params.get('origin_event_type')
    print("Incoming event:", incoming_event)

    # If we receive an error event, clear the state and exit
    if incoming_event in error_events:
        print(f"Received error event: {incoming_event}. Clearing state.")
        context.state.delete('seen_events')
        context.state.delete('job_data')
        context.state.delete('cand_data')
        return

    if incoming_event == 'ferris.apps.hr.job_extract':
        data = {
            "job_name": context.params.get('job'),
            "job_industry": context.params.get('job_industry'),
            "job_hard_skills": context.params.get('job_hard_skills'),
            "job_soft_skills": context.params.get('job_soft_skills'),
            "job_language_skills": context.params.get('job_language_skills')
        }
        # Validate job data
        if not any(data.values()):
            print("Job data appears to be empty or invalid")
            return
        context.state.put('job_data', data)

    if incoming_event == 'ferris.apps.hr.cand_extract':
        data = {
            "candidate_name": context.params.get('candidate'),
            "candidate_industry": context.params.get('candidate_industry'),
            "candidate_hard_skills": context.params.get('candidate_hard_skills'),
            "candidate_soft_skills": context.params.get('candidate_soft_skills'),
            "candidate_language_skills": context.params.get('candidate_language_skills'),
            "candidate_experience": context.params.get("candidate_experience", [])
        }
        # Validate candidate data
        if not any(data.values()):
            print("Candidate data appears to be empty or invalid")
            return
        context.state.put('cand_data', data)
    
    # Add the incoming event to the 'seen_events' array
    if incoming_event in predefined_events:  # Only track expected events
        seen_events = state.get('seen_events', [])
        if incoming_event not in seen_events:
            seen_events.append(incoming_event)
            context.state.put('seen_events', seen_events)

    # Check if all predefined events are seen and data is valid
    if all(event in seen_events for event in predefined_events):
        print("All events received:", seen_events)
        state = context.state.get()
        job_payload = state.get('job_data')
        cand_payload = state.get('cand_data')

        # Additional validation before sending event
        if not job_payload or not cand_payload:
            print("Missing required data. Job or Candidate data is empty.")
            context.state.delete('seen_events')
            context.state.delete('job_data')
            context.state.delete('cand_data')
            return

        send_event(job_payload, cand_payload)
        # Reset State by removing the keys entirely
        context.state.delete('seen_events')
        context.state.delete('job_data')
        context.state.delete('cand_data')
    else:
        print("Waiting for both job and candidate data to be available.")

main()

