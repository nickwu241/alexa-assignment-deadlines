#!/usr/bin/env python
from datetime import datetime
import csv
import json
import os

from canvasapi import Canvas
from flask import Flask, jsonify, request, send_from_directory

app = Flask(__name__, static_url_path='/static')

settings = {
    'course_names': {},
    'within_days': 3
}

@app.route('/settings', methods=['GET', 'POST'])
def settings_endpoint():
    if request.method == 'POST':
        global settings
        settings = json.loads(request.data)
    return jsonify(settings)


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        print(request.data)
        return jsonify(get_alexa_deadline())
    else:
        return send_from_directory(app.static_folder, 'index.html')
        # return jsonify(get_alexa_feed())

def get_alexa_deadline():
    sentences = ['']
    for deadline in get_deadlines(include_submitted=False, within_days=settings['within_days']):
        sentences.append('<p>{} from {} is due in {}.</p>'.format(
            deadline['assignment_name'],
            settings['course_names'][deadline['course_code']],
            deadline['deadline']))

    return {
        'version': '1.0',
        'response': {
            'outputSpeech': {
                'type': 'SSML',
                'ssml': '<speak>' + '\n'.join(sentences) + '\n</speak>\n'
            },
        }
    }

def get_alexa_feed():
    feed = []
    now_utc = datetime.utcnow()
    deadlines = list(get_deadlines(include_submitted=False, within_days=3))
    for i, deadline in enumerate(deadlines):
        # update_date = (now_utc - datetime(second=len(deadlines) - i))
        feed.append({
            'uid': i,
            'updateDate': deadline['due_at'].strftime('%Y-%m-%dT%H:%M:%S.0Z'),
            'titleText': '{} from {}'.format(deadline['assignment_name'], deadline['course_code']),
            'mainText': deadline['deadline'] + ' ' + str(i)
        })
    return feed

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
    settings['course_names'][course.course_code] = course.course_code
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
    return ' and '.join(result)

def get_deadlines(include_submitted=True, within_days=None):
    now = datetime.now()
    upcoming_assignments = [a for a in assignments.values() if a['due_at'] is None or a['due_at'] > now]
    if within_days:
        upcoming_assignments = [a for a in upcoming_assignments if a['due_at'] and (a['due_at'] - now).days < within_days]

    for assignment in sorted(upcoming_assignments, key=lambda a: (a['due_at'] is None, a['due_at'])):
        aname = assignment['name']
        deadline = {
            'course_name': courses[assignment['course_id']].name,
            'course_code': courses[assignment['course_id']].course_code,
            'assignment_name': assignment['name'],
            'due_at': assignment['due_at'],
            'deadline': get_deadline(now, assignment['due_at']),
        }
        if include_submitted:
            deadline['has_submitted'] = True if assignment['submission']['workflow_state'] != 'unsubmitted' else False

        yield deadline

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
# print_upcoming_assignments()