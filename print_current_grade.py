#!/usr/bin/env python -W ignore::DeprecationWarning
import models

courses = list(models.courses.values())

def prompt_course_select():
    for i, c in enumerate(courses):
        print('{:d}: {:s}'.format(i + 1, c.name))

    while True:
        selection = input('Select a course from 1 to {}): '.format(len(courses)))
        try:
            number = int(selection)
        except ValueError:
            continue
        if not 1 <= number < len(courses):
            continue
        return number - 1

def print_current_grade(cid):
    total_weight = 0
    total_grade = 0
    for group in models.ctag[cid]:
        group_name = group['name']
        group_weight = group['group_weight']
        print('{:s} {}%'.format(group_name, group_weight))

        group_points_possible_total = 0.0
        group_grade_total = 0.0
        for assignment in group['assignments']:
            points_possible = assignment.get('points_possible')
            submission = assignment['submission']
            # TODO: grade might not be a float
            grade = submission.get('grade')
            if points_possible and grade and submission['workflow_state'] == 'graded':
                group_points_possible_total += float(points_possible)
                group_grade_total += float(grade)
                print('-- {:s}: {:.2f} / {:.2f}'.format(assignment['name'], float(grade), points_possible))

        if group_grade_total and group_grade_total:
            group_total = group_grade_total / group_points_possible_total
            total_grade += (group_total * group_weight)
            total_weight += group_weight
            print('----> {:.2f}%\n'.format(group_total * 100))

    print('------------------------------')
    print('Weighted Grade: {0:.2f}%'.format(total_grade / total_weight * 100))
    print('Current Grade: {0:.2f}%'.format(total_grade))

if __name__ == '__main__':
    i = prompt_course_select()
    print_current_grade(courses[i].id)
