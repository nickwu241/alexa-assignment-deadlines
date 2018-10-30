import os

from datetime import datetime
from canvasapi import Canvas

import date_helper

API_URL = 'https://canvas.ubc.ca'
API_KEY = os.environ['CANVAS_ACCESS_TOKEN']
canvas = Canvas(API_URL, API_KEY)

settings = {
    'course_names': {},
    'within_days': 3
}

cta = {}         # course_id to assignment
ctag = {}        # course_id to assignment_group
courses = {}     # course_id to course
assignments = {} # assignment_id to assignemnt

def parse_assignment(assignment):
    return {
        'id': assignment.id,
        'name': assignment.name,
        'due_at': date_helper.parse_canvas_date(assignment.due_at),
        'course_id': assignment.course_id,
        'html_url': assignment.html_url,
        'submission': assignment.submission,
        'points_possible': assignment.points_possible,
    }

def parse_assignment_group(ag):
    return {
        'name': ag.name,
        'group_weight': ag.group_weight,
        'assignments': ag.assignments
    }

def get_deadline(now, due_at):
    if due_at is None:
        return 'Never'
    return date_helper.fmt_timedelta(due_at - now)

def get_deadlines(include_submitted=True, within_days=None):
    now = date_helper.now_utc()
    upcoming_assignments = [a for a in assignments.values() if a['due_at'] is None or a['due_at'] > now]
    if within_days:
        upcoming_assignments = [a for a in upcoming_assignments if a['due_at'] and (a['due_at'] - now).days < within_days]

    for assignment in sorted(upcoming_assignments, key=lambda a: (a['due_at'] is None, a['due_at'])):
        course_code = courses[assignment['course_id']].course_code
        deadline = {
            'course_name': courses[assignment['course_id']].name,
            'course_code': course_code,
            'course_nickname': settings['course_names'][course_code],
            'assignment_name': assignment['name'],
            'due_at': date_helper.fmt_pst(assignment['due_at']),
            'due_in': get_deadline(now, assignment['due_at']),
            'has_submitted': True if assignment['submission']['workflow_state'] != 'unsubmitted' else False
        }
        if not include_submitted and deadline['has_submitted']:
            continue
        yield deadline

for course in canvas.get_courses():
    settings['course_names'][course.course_code] = course.course_code
    courses[course.id] = course
    cta[course.id] = [parse_assignment(a) for a in course.get_assignments(include=['submission'])]
    for assignemnts_list in cta.values():
        assignments.update({a['id']: a for a in assignemnts_list})
    ctag[course.id] = [parse_assignment_group(a) for a in course.get_assignment_groups(include=['assignments', 'submission'])]
