from __future__ import print_function
import sys
import os
import pip
from clint.arguments import Args
from clint.textui import puts, colored, indent
import subprocess
import json
from json2html import *
from collections import defaultdict
from bs4 import BeautifulSoup
from ansi2html import Ansi2HTMLConverter
import webbrowser
from flask import Flask, render_template, send_file

#docker run -v ~/.aws/:/root/.aws/ -p 5000:5000 -ti final -pacu
# creates a Flask application, named app
app = Flask(__name__, template_folder='', static_url_path='', static_folder='',)

# Routes to the html file generated by ScoutSuite
@app.route("/scout")
def serve_scout_content():
    if os.path.isfile(os.path.abspath(os.path.dirname(os.path.abspath(__file__))) + 'scout-report.html'):
        return app.send_static_file('scout-report.html')
    else:
        return 'Scout Report Not Available'

# Routes to the HTML file generated by the defensive checks
@app.route("/")
def serve_content():
    if os.path.isfile(os.path.abspath(os.path.dirname(os.path.abspath(__file__))) + 'report.html'):
        return render_template('report.html')
    else:
        return 'Report Not Available'


html_files = {
    'pmapper': 'pmapper.html',
    'prowler': 'prowler.html',
    'benchmark': 'security_checklist.html'
}

# Helper function to convert a json object to an HTML file
def make_html(json_obj, html_file):
    html_doc = open(html_file, "w")
    html_doc.write(
        "<!doctype html><html lang='en'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width, initial-scale=1, shrink-to-fit=no'><link rel='stylesheet' href='https://maxcdn.bootstrapcdn.com/bootstrap/4.0.0/css/bootstrap.min.css' integrity='sha384-Gn5384xqQ1aoWXA+058RXPxPg6fy4IWvTNh0E263XmFcJlSAwiGgFAW/dAiS6JXm' crossorigin='anonymous'></head><body>")
    html_doc.write(json2html.convert(json=json_obj,
                                     table_attributes="id=\"info-table\" class=\"table table-bordered table-hover\""))
    html_doc.write("</body></html>")
    html_doc.close()

# Combines multiple html files
def combine_html(present_args):
    html_doc = open("report.html", "w")
    html_doc.write("<!doctype html><html lang='en'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width, initial-scale=1, shrink-to-fit=no'><link rel='stylesheet' href='https://maxcdn.bootstrapcdn.com/bootstrap/4.0.0/css/bootstrap.min.css' integrity='sha384-Gn5384xqQ1aoWXA+058RXPxPg6fy4IWvTNh0E263XmFcJlSAwiGgFAW/dAiS6JXm' crossorigin='anonymous'></head><body>")

    if present_args['pmapper']:
        soup = BeautifulSoup(open(html_files['pmapper'], 'r'), 'html.parser')
        html_doc.write("<br/><br/><h3>PMapper Report</h3>")
        html_doc.write(str(soup.table))

    if present_args['benchmark']:
        html_doc.write("<br/><br/><h3>Benchmark Report</h3>")
        soup = BeautifulSoup(open(html_files['benchmark'], 'r'), 'html.parser')
        html_doc.write(str(soup.table))

    if present_args['prowler']:
        html_doc.write("<br/><br/><h3>Prowler Report</h3>")
        soup = BeautifulSoup(open(html_files['prowler'], 'r'), 'html.parser')
        html_doc.write(str(soup.table))

    if ((not present_args['prowler']) and (not present_args['benchmark']) and (not present_args['pmapper'])):
        html_doc.write("<h3>No Report Available</h3>")

    html_doc.write("</body></html>")
    html_doc.close()

    app.run(host='0.0.0.0')

args = Args()
args = args.all

present_args = {
    'scout': '-scout' in args,
    'pmapper': '-pmapper' in args,
    'benchmark': '-benchmark' in args,
    'prowler': '-prowler' in args,
    'pacu': '-pacu' in args
}

if ('-help' in args):
    puts(colored.green('Commands: '))
    puts(colored.green('-all: runs a check on the AWS account using defensive checks'))
    puts(colored.green('-configure: configures the AWS account credentials'))
    puts(colored.green('-pacu: starts pacu, an offensive toolkit to audit an AWS account'))
    puts(colored.green('-scout: runs a check on the AWS account using AWSScout2'))
    puts(colored.green('-pmapper: runs a check on the AWS account using pmapper'))
    puts(colored.green('-prowler: runs a check on the AWS account using prowler'))
    puts(colored.green('-benchmark: runs a check on the AWS account using the AWS provided security guidelines'))

if ('-configure' in args):
    subprocess.call(['aws', 'configure'])

if ('-all' in args):
    present_args['scout'] = True
    present_args['pmapper'] = True
    present_args['prowler'] = True
    present_args['benchmark'] = True

if (present_args['scout']):
    subprocess.call(['python', 'ScoutSuite/scout.py', 'aws', '--no-browser'])
    subprocess.call(['cp -R /scoutsuite-report/* .'], shell=True)
    subprocess.call(['mv aws*.html scout-report.html'], shell=True)

if (present_args['pmapper']):
    subprocess.call(['pmapper', 'graph', '--create'])
    subprocess.call(['pmapper', 'analysis', '--output-type', 'json'], stdout=open('pmapper.json', 'w'))

    iam_data = json.load(open('pmapper.json', 'r'))
    make_html(iam_data, 'pmapper.html')

if (present_args['benchmark']):
    subprocess.call(['python', 'aws-cis-foundation-benchmark-checklist.py'], stdout=open('security_checklist.json', 'w'))
    failed_items = []

    with open('security_checklist.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
        for item in data:
            for num in data[item]:
                if not data[item][num]['Result']:
                    data[item][num].pop('Result')
                    data[item][num].pop('ScoredControl')
                    failed_items.append(data[item][num])


    failed_items.sort(key=lambda x: x['ControlId'])
    make_html(failed_items, 'security_checklist.html')

if (present_args['prowler']):
    subprocess.call(['/prowler/prowler', '-M', 'json'], stdout=open('prowler.json', 'w'))
    failed_items = []

    with open('prowler.json', 'r', encoding='utf-8') as f:
        # Removes non-json lines of output file
        data = f.readlines()[8:]
        for item in data:
            json_item = json.loads(item)
            if (json_item['Status'] == 'Fail'):

                json_item.pop('Profile', None)
                json_item.pop('Account Number', None)
                json_item.pop('Scored', None)
                json_item.pop('Level', None)
                json_item.pop('Region', None)
                json_item.pop('Timestamp', None)
                json_item.pop('Status', None)
                failed_items.append(json_item)

    failed_items.sort(key=lambda x: x['Control ID'])
    make_html(failed_items, 'prowler.html')

if (present_args['pacu']):
    os.system("cd pacu; python3 pacu.py")

if present_args['prowler'] or present_args['benchmark'] or present_args['pmapper'] or present_args['scout']:
    combine_html(present_args)
elif not present_args['pacu']:
    puts(colored.green('Invalid input. Valid inputs are:'))
    puts(colored.green('-configure: configures the AWS account credentials'))
    puts(colored.green('-all: runs a check on the AWS account using all available methods'))
    puts(colored.green('-scout: runs a check on the AWS account using AWSScout2'))
    puts(colored.green('-pmapper: runs a check on the AWS account using pmapper'))
    puts(colored.green('-prowler: runs a check on the AWS account using prowler'))
    puts(colored.green('-benchmark: runs a check on the AWS account using the AWS provided security guidelines'))