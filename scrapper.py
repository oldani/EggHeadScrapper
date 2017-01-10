import os
import re
import sys
from subprocess import Popen
import requests
from bs4 import BeautifulSoup


COURSES_URL = "https://egghead.io/courses"
BASE_COMMAND = "egghead-downloader -f -e {email} -p {password} {url} {output}"


def parse_courses(stack):
    """ Return a dict of course:link. """
    courses = stack.find_all('div', 'card-course')
    courses_dict = {}
    for course in courses:
        course_name = course.find('h3', 'course-title').text
        course_name = '-'.join(course_name.split())
        course_name = re.sub(r"[():/\\|{}?<>'\"+=]", "", course_name)
        course_link = course.find('a', 'link-overlay').attrs['href']
        courses_dict[course_name] = course_link
    return courses_dict


def stack_name(stack):
    """ Return a stack name. """
    name = stack.find('h4', 'title').text
    name = '-'.join(name.split())
    return re.sub(r"[():/\\|{}?<>'\"+=]", "", name)


def parse_courses_stack(stacks):
    """ Return a dict of stack name: dict of courses. """
    stacks = {stack_name(stack): parse_courses(stack) for stack in stacks}
    return stacks


def fetch_courses():
    # Fetch the courses page
    response = requests.get(COURSES_URL)

    # Create a bs4 object
    html_doc = BeautifulSoup(response.text, 'html.parser')

    # Create a list with all the courses links
    courses_stack = html_doc.find_all('div', 'technology-set')
    return parse_courses_stack(courses_stack)


def create_dir(base_path, path=None):
    """ Takes in a course link and create a dir with and return it. """
    if not path:
        directory = os.path.join(os.getcwd(), 'egghead-courses', base_path)
    else:
        directory = os.path.join(base_path, path)
    if not os.path.exists(directory):
        os.makedirs(directory)
    return directory


def run_shells(stack_dir, courses, email, password):
    """ Create a shell per course to run in parallel. """
    running_shells = []
    for name, link in courses.items():
        course_dir = create_dir(stack_dir, name)
        egghead_downloader = BASE_COMMAND.format(url=link, email=email,
                                                 password=password, output=course_dir)
        run_downloader = Popen(egghead_downloader, shell=True)
        running_shells.append(run_downloader)

    for shell in running_shells:
        shell.wait()


def main(email, password):
    """ Run the script, create a shell per course to run in parallel. """
    courses_stack = fetch_courses()

    for stack, courses in courses_stack.items():
        stack_dir = create_dir(stack)
        run_shells(stack_dir, courses, email, password)


if __name__ == "__main__":
    email, password = sys.argv[1:]
    main(email, password)
