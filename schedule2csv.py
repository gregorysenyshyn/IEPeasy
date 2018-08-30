import os
import re
import io
import sys
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
    return re.compile('(([A-Z0-9]+?)[a-z](M(r|s) [A-Z]\. [a-zA-Z]+?)(([0-9]{3}|PTB3))|\.\.\.)')


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

def main(filename, output_dir):

    oen_re = get_oen_re()
    ugcloud_re = get_ugcloud_re()
    course_string_re = get_course_string_re()
    courses_re = get_courses_re()

    reader = None
    student_data = {}
    with open(filename, 'rb') as f:
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
                student_oen = oen.group(1).replace('-','')
                student_data[student_oen] = {'ugcloud': email_address} 
                course_string = course_string_re.search(text)
                courses = courses_re.finditer(course_string.group())
                period = 1
                for item in courses:
                    student_data[student_oen][f"period {period} course"] = item.group(2)
                    student_data[student_oen][f"period {period} teacher"] = item.group(3)
                    student_data[student_oen][f"period {period} room"] = item.group(5)
                    period += 1

                if not ugcloud:
                    print(f"{email_address} is not a valid UGCloud address")
                    
    import pdb; pdb.set_trace()



if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=("Take a Maplewood timetable "
        "pdf and split it into individual files named with a student's ugcloud"
        " user name"))
    parser.add_argument("-f", "--filename", dest="filename")
    parser.add_argument("-o", "--output", dest="output")
    args = parser.parse_args()
    filename = file_checker(args, "filename", "Maplewood Timetable")
    output = file_checker(args, "output", "Output")

    main(filename, output)
