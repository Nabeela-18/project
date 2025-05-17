from integrate_timetable_solver import IntegratedTimetableSolver
import generate_lab_timetable

#inputs

lab_timetable = [
    {
        "Batch": "Batch 1 (Lab 1, Java)",
        "Day": "Monday",
        "Section": "A",
        "Subject": "Java",
        "Time": "8:00 - 11:00",
        "Year": "1"
    },
    {
        "Batch": "Batch 2 (Lab 2, DBMS)",
        "Day": "Monday",
        "Section": "A",
        "Subject": "DBMS",
        "Time": "8:00 - 11:00",
        "Year": "1"
    },
    {
        "Batch": "Batch 1 (Lab 1, Java)",
        "Day": "Monday",
        "Section": "B",
        "Subject": "Java",
        "Time": "11:00 - 14:00",
        "Year": "1"
    },
    {
        "Batch": "Batch 2 (Lab 2, DBMS)",
        "Day": "Monday",
        "Section": "B",
        "Subject": "DBMS",
        "Time": "11:00 - 14:00",
        "Year": "1"
    },
    {
        "Batch": "Batch 1 (Lab 1, Java)",
        "Day": "Monday",
        "Section": "C",
        "Subject": "Java",
        "Time": "14:00 - 17:00",
        "Year": "1"
    },
    {
        "Batch": "Batch 2 (Lab 2, DBMS)",
        "Day": "Monday",
        "Section": "C",
        "Subject": "DBMS",
        "Time": "14:00 - 17:00",
        "Year": "1"
    },
    {
        "Batch": "Batch 1 (Lab 3, Machine learning)",
        "Day": "Monday",
        "Section": "D",
        "Subject": "Machine learning",
        "Time": "8:00 - 11:00",
        "Year": "2"
    },
    {
        "Batch": "Batch 2 (Lab 4, Mobile app development)",
        "Day": "Monday",
        "Section": "D",
        "Subject": "Mobile app development",
        "Time": "8:00 - 11:00",
        "Year": "2"
    },
    {
        "Batch": "Batch 1 (Lab 3, Machine learning)",
        "Day": "Monday",
        "Section": "E",
        "Subject": "Machine learning",
        "Time": "11:00 - 14:00",
        "Year": "2"
    },
    {
        "Batch": "Batch 2 (Lab 4, Mobile app development)",
        "Day": "Monday",
        "Section": "E",
        "Subject": "Mobile app development",
        "Time": "11:00 - 14:00",
        "Year": "2"
    },
    {
        "Batch": "Batch 1 (Lab 3, Machine learning)",
        "Day": "Monday",
        "Section": "F",
        "Subject": "Machine learning",
        "Time": "14:00 - 17:00",
        "Year": "2"
    },
    {
        "Batch": "Batch 2 (Lab 4, Mobile app development)",
        "Day": "Monday",
        "Section": "F",
        "Subject": "Mobile app development",
        "Time": "14:00 - 17:00",
        "Year": "2"
    },
    {
        "Batch": "Batch 1 (Lab 1, DBMS)",
        "Day": "Tuesday",
        "Section": "A",
        "Subject": "DBMS",
        "Time": "8:00 - 11:00",
        "Year": "1"
    },
    {
        "Batch": "Batch 2 (Lab 2, Java)",
        "Day": "Tuesday",
        "Section": "A",
        "Subject": "Java",
        "Time": "8:00 - 11:00",
        "Year": "1"
    },
    {
        "Batch": "Batch 1 (Lab 1, DBMS)",
        "Day": "Tuesday",
        "Section": "B",
        "Subject": "DBMS",
        "Time": "11:00 - 14:00",
        "Year": "1"
    },
    {
        "Batch": "Batch 2 (Lab 2, Java)",
        "Day": "Tuesday",
        "Section": "B",
        "Subject": "Java",
        "Time": "11:00 - 14:00",
        "Year": "1"
    },
    {
        "Batch": "Batch 1 (Lab 1, DBMS)",
        "Day": "Tuesday",
        "Section": "C",
        "Subject": "DBMS",
        "Time": "14:00 - 17:00",
        "Year": "1"
    },
    {
        "Batch": "Batch 2 (Lab 2, Java)",
        "Day": "Tuesday",
        "Section": "C",
        "Subject": "Java",
        "Time": "14:00 - 17:00",
        "Year": "1"
    },
    {
        "Batch": "Batch 1 (Lab 3, Mobile app development)",
        "Day": "Tuesday",
        "Section": "D",
        "Subject": "Mobile app development",
        "Time": "8:00 - 11:00",
        "Year": "2"
    },
    {
        "Batch": "Batch 2 (Lab 4, Machine learning)",
        "Day": "Tuesday",
        "Section": "D",
        "Subject": "Machine learning",
        "Time": "8:00 - 11:00",
        "Year": "2"
    },
    {
        "Batch": "Batch 1 (Lab 3, Mobile app development)",
        "Day": "Tuesday",
        "Section": "E",
        "Subject": "Mobile app development",
        "Time": "11:00 - 14:00",
        "Year": "2"
    },
    {
        "Batch": "Batch 2 (Lab 4, Machine learning)",
        "Day": "Tuesday",
        "Section": "E",
        "Subject": "Machine learning",
        "Time": "11:00 - 14:00",
        "Year": "2"
    },
    {
        "Batch": "Batch 1 (Lab 3, Mobile app development)",
        "Day": "Tuesday",
        "Section": "F",
        "Subject": "Mobile app development",
        "Time": "14:00 - 17:00",
        "Year": "2"
    },
    {
        "Batch": "Batch 2 (Lab 4, Machine learning)",
        "Day": "Tuesday",
        "Section": "F",
        "Subject": "Machine learning",
        "Time": "14:00 - 17:00",
        "Year": "2"
    }
] 

years_sections =  {
            "1": [
                "A",
                "B",
                "C"
            ],
            "2": [
                "D",
                "E",
                "F"
            ]
        }

num_subjects=4
lang=2
num_classrooms=2
subject_input=["chemistry", "biology", "maths", "physics"]
hours_input=1
teacher_name=["Ramesh", "Suresh", "1", "2", "3", "4"]
optional_subject=""
optional_subject_hours=""
optional_subject_teacher=""
rooms=2

lab_summary = generate_lab_timetable.print_lab_timetable(lab_timetable, 
                                                         )

solver = IntegratedTimetableSolver(
lab_summary,
years_sections, 
num_subjects=4,
lang="English",
num_classrooms=2,
subject_input=["chemistry", "biology", "maths", "physics"],
hours_input=1,
teacher_name=["Ramesh", "Suresh", "1", "2", "3", "4"],
optional_subject="",
optional_subject_hours="",
optional_subject_teacher="",
rooms=["1a", "1b"]
)

solver.create_variables()
solver.add_constraints()
solver.solve()