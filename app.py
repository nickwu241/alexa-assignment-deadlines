#!/usr/bin/env python
import os

from canvasapi import Canvas

def parse_assignment(assignment):
    return {
        'name': assignment.name,
        'due_at': assignment.due_at,
        'course_id': assignment.course_id,
        'html_url': assignment.html_url,
        'submission': assignment.submission
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

cta = {}
courses = {}

for course in canvas.get_courses():
    courses[course.id] = course
    # cta[course.id] = [parse_assignment(a) for a in course.get_assignments(include=['all_dates', 'submission'])]
    cta[course.id] = [parse_assignment_group(a) for a in course.get_assignment_groups(include=['assignments', 'submission'])]

cid = 10266
total_weight = 0
total_grade = 0
for group in cta[cid]:
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
print('current grade: ', total_grade)
