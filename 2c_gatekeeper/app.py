import json
from ferris_cli.v2 import FerrisEvents
from ferris_ef import context


def send_event(job_data, cand_data):
    context.events.send(
        "ferris.apps.hr.coverage_ratio",
        context.package.name,
        {
            'job_data': job_data,
            'cand_data': cand_data
        }
    )
    print("Job Data: ", job_data)
    print("Candidate Data: ", cand_data)
    print("Job and Candidate profiling step completed, Trigger Event: hr_coverage_ratio")


def main():

    # Define the predefined array of event types
    predefined_events = ["ferris.apps.hr.job_extract", "ferris.apps.hr.cand_extract"]

    # Retrieve the current state
    state = context.state.get()

    # Retrieve the incoming event type A
    incoming_event = context.params.get('ferris.apps.hr.job_extract')
    data = {
        "job_name": context.params.get('job'),
        "job_industry": context.params.get('job_industry'),
        "job_hard_skills": context.params.get('job_hard_skills'),
        "job_soft_skills": context.params.get('job_soft_skills'),
        "job_language_skills": context.params.get('job_language_skills')
    }
    context.state.put('job_data', data)
    if incoming_event = None:
        incoming_event = context.params.get('ferris.apps.hr.cand_extract')
        data = {
            "candidate_name": context.params.get('candidate'),
            "candidate_industry": context.params.get('candidate_industry'),
            "candidate_hard_skills": context.params.get('candidate_hard_skills'),
            "candidate_soft_skills": context.params.get('candidate_soft_skills'),
            "candidate_language_skills": context.params.get('candidate_language_skills')
        }
        context.state.put('cand_data', data)
    print("Event: ", incoming_event)
    
    # Add the incoming event to the 'seen_events' array
    seen_events = state.get('seen_events', [])
    if incoming_event not in seen_events:
        seen_events.append(incoming_event)

    # Update the state with the new list of seen events
    context.state.put('seen_events', seen_events)

    # Check if all predefined events are seen
    if all(event in seen_events for event in predefined_events):
        job_payload = state.get('job_data')
        cand_payload = state.get('cand_data')
        send_event(job_payload, cand_payload)
        
        # Reset State to Clean
        context.state.put([])

        
main()

