from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for
)

import google.generativeai as genai
import os
from markupsafe import Markup

genai.configure(api_key=os.environ["API_KEY"])

model = genai.GenerativeModel(model_name='gemini-1.5-flash',
                              system_instruction="""I would like you to act as a place-based education curriculum writer who prioritizes the following approaches: learner-centered practices; consideration of place on scales ranging from local to global; community engagement; inquiry; design thinking; and project-based learning. Consider “place” to include the aspects of ecology, culture, and economy. 
""")

bp = Blueprint('home', __name__, url_prefix='/')

def get_api_data(prompt):
    try:
        response = model.generate_content(prompt).text
    except ValueError:
        return {'Header': '''Error: Curriculum failed to generate. Please try
                again.'''}
    start_index = response.find('##')
    end_index = response.find('\n',start_index)
    header = response[start_index + 3:end_index]
    sections = {}
    sections['Header'] = header.strip()

    start_index = end_index
    end_index = response.find('**',start_index)
    intro = response[start_index + 1:end_index].strip()
    sections['Intro'] = intro

    main_sections = []
    while(end_index > 0):
        start_index = response.find('**',end_index)
        if start_index < end_index:
            break
        section_words = ["\n**"]
        poss_ends = [response.find(word, start_index + 1) for word in section_words]
        end_index = max(poss_ends)
        if end_index == -2:
            end_index = len(response)
        sec = response[start_index:end_index].strip()
        print(sec)
        print("**********")
        main_sections.append(sec)
    sections['Main Sections'] = main_sections
    return sections

def dict_to_html(sections):
    final_str = '<div id = "title"><h1>' + sections['Header'] + '</h1></div>'
    final_str += '<div id = "intro"><text>' + sections['Intro'] + "</text></div><br>"
    for section in sections['Main Sections']:
        new_section = boldify(section)
        final_str += '<div id = "section"><button type="button" class="btn text-start">' + new_section + "</button></div>"
    return final_str

def boldify(section):
    new_section = section[:]
    parity = True
    loc = 0
    while new_section.find("**", loc) != -1:
        loc = new_section.find("**", loc)
        if parity == True:
            updated = new_section[:loc] + "<b>" + new_section[loc + 2:]
        else:
            updated = new_section[:loc] + "</b>" + new_section[loc + 2:]
        parity = not parity
        new_section = updated

    new_section = new_section.replace("*", "<ul><li>", 1)
    new_section = new_section.replace("    *", '</li><li class="ms-4">')
    new_section = new_section.replace("*", "</li><li>")
    new_section += "</li></ul>"
    return new_section

@bp.route('/', methods = ["GET", "POST"])
def home():
    display = ""
    if request.method == 'POST':
        grade = request.form['grades']
        grade_to_word = {1:"first", 2:"second", 3:"third", 4:"fourth",
                         5:"fifth", 6:"sixth", 7:"seventh", 8:"eighth",
                         9:"ninth", 10:"tenth", 11:"eleventh", 12:"twelfth"}
        grade = grade_to_word[int(grade)]
        return redirect(url_for('.curriculum', grade = grade))
    return render_template('home.html')

@bp.route('/curriculum', methods = ["GET", "POST"])
def curriculum():
    grade = request.args['grade']
    prompt = f"""Write a place-based year-long curriculum guide for
    {grade}-grade science that addresses all NGSS Standards."""
    display = dict_to_html(get_api_data(prompt))
    return render_template('curriculum.html', display = Markup(display))
