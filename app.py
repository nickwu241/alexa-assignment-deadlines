#!/usr/bin/env python
import os

from canvasapi import Canvas
import requests

def parse_assignment(assignment):
    return {
        'name': assignment.name,
        'due_at': assignment.due_at,
        'course_id': assignment.course_id,
        'html_url': assignment.html_url,
        'submission': assignment.submission
    }

API_URL = "https://canvas.ubc.ca"
API_KEY = os.environ['CANVAS_ACCESS_TOKEN']

canvas = Canvas(API_URL, API_KEY)

cta = {}
courses = {}

for course in canvas.get_courses():
    courses[course.id] = course
    cta[course.id] = [parse_assignment(a) for a in course.get_assignments(include=['all_dates', 'submission'])]

cid = 10266
for a in cta[cid]:
    print('{} - {}'.format(a['name'], a['due_at']))
    score = a['submission'].get('score')
    grade = a['submission'].get('grade')
    if score and grade:
        print('{}/{}'.format(score, grade))
