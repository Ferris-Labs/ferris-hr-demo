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

    # Define the predefined array of event types
    predefined_events = ["ferris.apps.hr.job_extract", "ferris.apps.hr.cand_extract"]

    # Retrieve the current state
    state = context.state.get()
    print(state)
    # Retrieve the incoming event type A
    incoming_event = context.params.get('origin_event_type')
    print(incoming_event)
    if incoming_event == 'ferris.apps.hr.job_extract':
        data = {
            "job_name": context.params.get('job'),
            "job_industry": context.params.get('job_industry'),
            "job_hard_skills": context.params.get('job_hard_skills'),
            "job_soft_skills": context.params.get('job_soft_skills'),
            "job_language_skills": context.params.get('job_language_skills')
        }
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
        context.state.put('cand_data', data)
    
    # Add the incoming event to the 'seen_events' array
    seen_events = state.get('seen_events', [])
    if incoming_event not in seen_events:
        seen_events.append(incoming_event)
        context.state.put('seen_events', seen_events)

    # Check if all predefined events are seen
    if all(event in seen_events for event in predefined_events):
        print("All Events here: ", seen_events)
        state = context.state.get()
        job_payload = state.get('job_data')
        cand_payload = state.get('cand_data')

        send_event(job_payload, cand_payload)
        # Reset State by removing the keys entirely
        context.state.delete('seen_events')
        context.state.delete('job_data')
        context.state.delete('cand_data')
    else:
        print("Waiting for both job and candidate data to be available.")

main()

