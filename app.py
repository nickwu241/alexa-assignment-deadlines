#!/usr/bin/env python -W ignore::DeprecationWarning
import csv
import json
import os

from canvasapi import Canvas
from flask import Flask, jsonify, request, send_from_directory

import date_helper
import models

app = Flask(__name__, static_url_path='/static')

@app.route('/settings', methods=['GET', 'POST'])
def settings_endpoint():
    if request.method == 'POST':
        models.settings = json.loads(request.data)
    return jsonify(models.settings)


@app.route('/deadlines')
def deadline_endpoint():
    deadlines = list(models.get_deadlines(include_submitted=True, within_days=int(models.settings['within_days'])))
    for d in deadlines:
        print(d['due_at'])
    return jsonify({'data': deadlines})


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        return jsonify(get_alexa_deadlines())
    return send_from_directory(app.static_folder, 'index.html')

def get_alexa_deadlines():
    sentences = []
    for deadline in models.get_deadlines(include_submitted=False, within_days=int(models.settings['within_days'])):
        sentences.append('<p>{} from {} is due in {}.</p>'.format(
            deadline['assignment_name'],
            models.settings['course_names'][deadline['course_code']],
            deadline['due_in']))

    return {
        'version': '1.0',
        'response': {
            'outputSpeech': {
                'type': 'SSML',
                'ssml': '<speak>\n' + '\n'.join(sentences) + '\n</speak>\n'
            },
        }
    }

def print_upcoming_assignments():
    for deadline in models.get_deadlines():
        has_submitted = deadline['has_submitted']
        if has_submitted:
            continue
        ccode = deadline['course_code']
        aname = deadline['assignment_name']
        due_in = deadline['due_in']
        print('{} >> {}: {} << submitted?={}'.format(ccode, aname, due_in, has_submitted))

def write_deadline_report():
    deadlines = list(models.get_deadlines())
    with open('deadline.csv', 'w') as f:
        writer = csv.DictWriter(f, fieldnames=list(deadlines[0].keys()))
        writer.writeheader()
        writer.writerows(deadlines)

if __name__ == '__main__':
    print_upcoming_assignments()
    write_deadline_report()