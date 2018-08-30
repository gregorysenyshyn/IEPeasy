#! /usr/bin/env python3

import argparse
import os
import re
import csv

import PyPDF2

def get_data_re():
    return re.compile('Individual Education Plan for  (.+?)Student ID.+?OEN ([0-9]{3}-[0-9]{3}-[0-9]{3}).+?Accommodations Instructional Environmental Assessment(.+?)(Human|!).+?Jennifer Meeker Date')

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

def extract_data(iep_text):
    data_re = get_data_re()
    data = data_re.finditer(iep_text)
    return data

def main(folder, output_dir):

    all_ieps_data = []

    for filename in os.listdir(folder):

        with open(os.path.join(folder, filename), 'rb') as f:
            reader = PyPDF2.PdfFileReader(f)

            writer = PyPDF2.PdfFileWriter()
            current_ugcloud = None
            iep_text = ''

            print(f"processing {filename} pages...\n")
            for page in reader.pages:
                raw_text = page.extractText()
                iep_text += raw_text.replace("\n"," ")

            students = extract_data(iep_text)
            for student in students:
                all_ieps_data.append(student)

    with open(args.output, 'a', newline='') as f:
        data_writer = csv.writer(f)
        for item in all_ieps_data:
            data_writer.writerow([item.group(1),
                                  item.group(2),
                                  item.group(3)])
        

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=("Takes a folder with PDFs of IEPS"
        "and copies specified fields to a CSV file"))
    parser.add_argument("-f", "--folder", dest="folder")
    parser.add_argument("-o", "--output", dest="output")
    args = parser.parse_args()
    print(args)
    folder = file_checker(args, "folder", "Folder of PDFs of IEPs")
    output = file_checker(args, "output", "Output")

    main(folder, output)
