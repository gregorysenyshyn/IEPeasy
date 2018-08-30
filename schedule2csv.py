import os
import re
import io
import sys
import csv
import argparse

import PyPDF2


def strip_punctuation(full_name):
    things_to_remove = ["'", "-", ".", " "]
    for thing in things_to_remove:
       full_name = full_name.replace(thing, "")
    return full_name


def get_oen_re():
    return re.compile('OEN Number: +([0-9]{3}-[0-9]{3}-[0-9]{3})')


def get_ugcloud_re():
    return re.compile('^[a-zA-Z]{5}[0-9]{4}$')


def get_course_string_re():
    return re.compile('Semester   1   Term  1Period19:00 am10:15 am(.+?)210:20 am11:35 am')


def get_courses_re():
    return re.compile('(([A-Z0-9]+?)[a-z]((M(r|s|rs)\.? )?[A-Z]\. [a-zA-Z\-\']+?)(([0-9]{3}|PTB3))|\.\.\.)')


def get_username(text, oen_match):
                
    oen = oen_match.group(1).replace('-','')
    full_name = strip_punctuation(text[35:oen_match.start()].strip())
    last_name, first_name = full_name.split(',')
    return '{0}{1}{2}'.format(first_name.strip().capitalize()[:2],
                              last_name.strip().capitalize()[:3],
                              oen[5:])


def file_checker(args, value_type, message):
    if vars(args)[value_type] is not None: 
        if os.path.exists(vars(args)[value_type]):
            return vars(args)[value_type]
    else:
        value = None
        while not value:
            value = input(f"{message} location: ").strip()
            if os.path.exists(value):
                return value
            else:
                print(f"{value} is not a valid location")
                value = None


def get_student_data(maplewood):
    oen_re = get_oen_re()
    ugcloud_re = get_ugcloud_re()
    course_string_re = get_course_string_re()
    courses_re = get_courses_re()
    reader = None
    student_data = {}
    with open(maplewood, 'rb') as f:
        reader = PyPDF2.PdfFileReader(f)

        writer = PyPDF2.PdfFileWriter()
        current_ugcloud = None
        new_document = True

        print("processing pages...\n")
        for page in reader.pages:
            text = page.extractText()
            oen = oen_re.search(text)
            if oen:
                email_address = get_username(text, oen)
                ugcloud = ugcloud_re.search(email_address)
                print(f"processing {email_address}...", end="")
                student_oen = oen.group(1)
                student_data[student_oen] = {'ugcloud': email_address} 
                course_string = course_string_re.search(text)
                courses = courses_re.finditer(course_string.group())
                period = 1
                for item in courses:
                    student_data[student_oen][f"period {period} course"] = item.group(2)
                    student_data[student_oen][f"period {period} teacher"] = item.group(3)
                    student_data[student_oen][f"period {period} room"] = item.group(6)
                    period += 1

                if not ugcloud:
                    print(f"{email_address} is not a valid UGCloud address")

    return student_data



def main(maplewood, iep, output):
    student_data = get_student_data(maplewood)
    combined_data = []

    with open(iep, 'r') as f:
        reader = csv.reader(f)
        for row in reader:
            if row[1] in student_data:
                student_data[row[1]]['name'] = row[0]
                student_data[row[1]]['oen'] = row[1]
                student_data[row[1]]['accommodations'] = row[2]
                combined_data.append(student_data[row[1]])

    with open(args.output,'w', newline='') as f:
        fieldnames = ['name', 'oen', 'ugcloud',
                      'period 1 course', 'period 1 teacher', 'period 1 room',
                      'period 2 course', 'period 2 teacher', 'period 2 room',
                      'period 3 course', 'period 3 teacher', 'period 3 room',
                      'period 4 course', 'period 4 teacher', 'period 4 room',
                      'accommodations']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(combined_data)

                    



if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=("Take a Maplewood timetable "
        "pdf and split it into individual files named with a student's ugcloud"
        " user name"))
    parser.add_argument("-iep", "--iep", dest="iep")
    parser.add_argument("-mw", "--maplewood", dest="maplewood")
    parser.add_argument("-o", "--output", dest="output")
    args = parser.parse_args()
    maplewood = file_checker(args, "maplewood", "Maplewood Timetable")
    iep = file_checker(args, "iep", "IEP Engine CSV")
    output = file_checker(args, "output", "Output")

    main(maplewood, iep, output)
