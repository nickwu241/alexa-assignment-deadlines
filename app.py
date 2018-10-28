#!/usr/bin/env python
from datetime import datetime
import csv
import os

from canvasapi import Canvas

def parse_assignment(assignment):
    return {
        'id': assignment.id,
        'name': assignment.name,
        'due_at': datetime.strptime(assignment.due_at, '%Y-%m-%dT%H:%M:%SZ') if assignment.due_at else None,
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

API_URL = "https://canvas.ubc.ca"
API_KEY = os.environ['CANVAS_ACCESS_TOKEN']

canvas = Canvas(API_URL, API_KEY)

cta = {}         # course_id to assignment
ctag = {}        # course_id to assignment_group
courses = {}     # course_id to course
assignments = {} # assignment_id to assignemnt

for course in canvas.get_courses():
    courses[course.id] = course
    cta[course.id] = [parse_assignment(a) for a in course.get_assignments(include=['submission'])]
    for assignemnts_list in cta.values():
        assignments.update({a['id']: a for a in assignemnts_list})
    # ctag[course.id] = [parse_assignment_group(a) for a in course.get_assignment_groups(include=['assignments', 'submission'])]

def get_deadline(now, due_at):
    if due_at is None:
        return 'Never'
    deadline = due_at - now
    days = deadline.days
    hours = deadline.seconds // 3600
    minutes = deadline.seconds % 3600 // 60
    # seconds = deadline.seconds % 60
    result = []
    if days > 0:
        result.append('{:d} {}'.format(days, 'day' if days == 1 else 'days'))
    if hours:
        result.append('{:d} {}'.format(hours, 'hour' if hours == 1 else 'hours'))
    result.append('{:d} {}'.format(minutes, 'minute' if minutes == 1 else 'minutes'))
    # result.append('{:d} {}'.format(seconds, 'second' if seconds == 1 else 'seconds'))
    return ' '.join(result)

def get_deadlines():
    now = datetime.now()
    upcoming_assignments = [a for a in assignments.values() if a['due_at'] is None or a['due_at'] > now]
    for assignment in sorted(upcoming_assignments, key=lambda a: (a['due_at'] is None, a['due_at'])):
        aname = assignment['name']
        yield {
            'course_code': courses[assignment['course_id']].course_code,
            'assignment_name': assignment['name'],
            'due_at': assignment['due_at'],
            'deadline': get_deadline(now, assignment['due_at']),
            'has_submitted': True if assignment['submission']['workflow_state'] != 'unsubmitted' else False
        }

def stress_check():
    pass

def current_grade(cid):
    total_weight = 0
    total_grade = 0
    for group in ctag[cid]:
        group_points_possible_total = 0.0
        group_grade_total = 0.0

        for assignment in group['assignments']:
            points_possible = assignment.get('points_possible')
            submission = assignment['submission']
            grade = submission.get('grade')
            if points_possible and grade and submission['workflow_state'] == 'graded':
                group_points_possible_total += float(points_possible)
                group_grade_total += float(grade)
                print('{} ({}): {} / {}'.format(assignment['name'], group['name'], grade, points_possible))

        if group_grade_total and group_grade_total:
            group_total = group_grade_total / group_points_possible_total
            group_weight = group['group_weight']
            print(group_total, group_weight)
            total_grade += (group_total * group_weight)
            total_weight += group_weight

    print(total_grade, total_weight)
    print('current grade: {0:.2f}'.format(total_grade))

def print_upcoming_assignments():
    for deadline in get_deadlines():
        has_submitted = deadline['has_submitted']
        if has_submitted:
            continue
        ccode = deadline['course_code']
        aname = deadline['assignment_name']
        at = deadline['deadline']
        print('{} >> {}: {} << submitted?={}'.format(ccode, aname, at, has_submitted))

def write_deadline_report():
    with open('deadline.csv', 'w') as f:
        writer = csv.DictWriter(f, fieldnames=['has_submitted', 'deadline', 'due_at', 'assignment_name', 'course_code'])
        writer.writeheader()
        writer.writerows(get_deadlines())

# current_grade(ctag, 10266)
print_upcoming_assignments()