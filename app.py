#final modified tt
from flask import Flask, request, jsonify
from datetime import time
import db_connection
from integrate_timetable_solver import IntegratedTimetableSolver
import generate_lab_timetable
import json
import ast

app = Flask(__name__)


def insert_data(query, values):
    try:
        connection = db_connection.get_connection()

        cursor = connection.cursor()

        print(query)
        cursor.execute(query, values)

        connection.commit()
        connection.close()
        return True
    except Exception as error:
        return error

def fetch_data(query):
    try:
        connection = db_connection.get_connection()

        cursor = connection.cursor()

        cursor.execute(query)

        results = cursor.fetchall()

        connection.commit()
        connection.close()
        return results
    except Exception as error:
        return error



#updated routes 
#--- Route to add a year ---
@app.route('/year', methods=['POST'])
def add_year():
    data = request.json
    name = data.get("name")

    query = "INSERT INTO Years (name) VALUES (%s);"
    values = (name,)

    insert_data(query, values)
    return jsonify({"message": "Year added successfully"})

#--Route to add section--
@app.route('/section', methods=['POST'])
def add_section():
    data = request.json
    year_id = data.get("year_id")
    section_name = data.get("section_name")

    query = "INSERT INTO Sections (year_id, section_name) VALUES (%s, %s);"
    values = (year_id, section_name)

    insert_data(query, values)
    return jsonify({"message": "Section added successfully"})

#--Route to add subject--
@app.route('/subject', methods=['POST'])
def add_subject():
    data = request.json
    year_id = data.get("year_id")
    subject_name = data.get("subject_name")
    is_lab = data.get("is_lab")

    query = "INSERT INTO Subjects (year_id, subject_name, is_lab) VALUES (%s, %s, %s);"
    values = (year_id, subject_name, is_lab)

    insert_data(query, values)
    return jsonify({"message": "Subject added successfully"})

#--- Route to add labs-per-section --
@app.route('/labs-per-section', methods=['POST'])
def add_labs_per_section():
    data = request.json
    section_id = data.get("section_id")
    num_labs = data.get("num_labs")

    query = "INSERT INTO LabsPerSection (section_id, num_labs) VALUES (%s, %s);"
    values = (section_id, num_labs)

    insert_data(query, values)
    return jsonify({"message": "Lab count added successfully"})

@app.route('/generate_lab_timetable', methods=['POST', 'GET'])
def _generate_lab_timetable():
    if request.method == "POST":
        data = request.json
        print(data)
        years_sections = data.get("years_sections")
        labs_per_sections = data.get("labs_per_sections")
        subjects_per_year = data.get("subjects_per_year")

        results = generate_lab_timetable.main(years_sections, labs_per_sections, subjects_per_year)
        query = "INSERT INTO lab_timetables (timetable) values (%s);"
        insert_data(query, f"{results}")

        return jsonify(results), 200
    elif request.method == "GET":
        query = "SELECT * FROM lab_timetables;"
        response = fetch_data(query)
        for item in response:
            item["timetable"] = ast.literal_eval(item["timetable"])
            item["created_date"] = item["created_date"].isoformat() 

        return jsonify(response), 200
    else:
        return 500


@app.route('/generate_timetable', methods=['POST', 'GET'])
def _generate_timetable():
    if request.method == "POST":
        data = request.json
        print(data)
        lab_summary=generate_lab_timetable.print_lab_timetable(data.get("lab_summary"))
        years_sections=data.get("years_sections") 
        num_subjects=data.get("num_subjects")
        lang=data.get("lang")
        num_classrooms=data.get("num_classrooms")
        subject_input=data.get("subject_input")
        hours_input=data.get("hours_input")
        teacher_name=data.get("teacher_name")
        optional_subject=data.get("optional_subject")
        optional_subject_hours=data.get("optional_subject_hours")
        optional_subject_teacher=data.get("optional_subject_teacher")
        rooms=data.get("rooms")
        

        solver = IntegratedTimetableSolver(
            lab_summary,
            years_sections, 
            num_subjects,
            lang,
            num_classrooms,
            subject_input,
            hours_input,
            teacher_name,
            optional_subject,
            optional_subject_hours,
            optional_subject_teacher,
            rooms,
            )

        solver.create_variables()
        solver.add_constraints()
        output = solver.solve()
        with open(output, 'r') as file:
            contents = file.read()
            return jsonify({"output": contents}), 200
    else:
        return 500



if __name__ == '__main__':
    # with app.app_context():
    #     db.create_all()
    app.run(debug=True)

