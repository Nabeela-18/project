#from app import store_timetable_in_db, db, Section, Subject, Year, app, Timetable
#from app import store_timetable_in_db, Section, Subject, Year, app

from datetime import time
import itertools
from ortools.sat.python import cp_model
from tabulate import tabulate

# Part a: Lab Timetable Generator
def calculate_max_labs_per_week(time_slots, saturday_slots, lab_pairs):
    """
    Calculate the maximum number of labs that can be scheduled in a week.
    """
    max_pairs_per_day = len(time_slots) * len(lab_pairs)  # Lab pairs per weekday
    max_pairs_saturday = len(saturday_slots) * len(lab_pairs)  # Lab pairs on Saturday
    return (max_pairs_per_day * 5) + max_pairs_saturday  # 5 weekdays + Saturday

def check_lab_capacity(total_sections_to_assign, max_pairs_per_week):
    """
    Check if the total section assignments exceed the maximum capacity.
    """
    return total_sections_to_assign <= max_pairs_per_week

def generate_lab_timetable(years_sections, num_labs_per_section, subjects_per_year):
    days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
    time_slots = [(8, 11), (11, 14), (14, 17)]  # Available time slots (Monday to Friday)
    saturday_slots = [(8, 11), (11, 14)]  # Saturday has only morning slots

    # Create lab pairs
    labs = [1, 2, 3, 4, 5, 6]  # Available labs
    lab_pairs = [(1, 2), (3, 4), (5, 6)]  # Using fixed pairs to ensure consistent rotation

    lab_schedule = []
    years_sections=years_sections.split(",")
    # Create a list of all sections with their years
    section_list = [(year, section) for year in years_sections for section in years_sections[year]]

    # Create a priority queue based on the number of labs needed
    priority_queue = sorted([(year, section, num_labs_per_section[section])
                            for year, section in section_list
                            if num_labs_per_section[section] > 0],
                           key=lambda x: x[2], reverse=True)

    # Track lab usage per time slot per day
    lab_usage = {day: {slot: set() for slot in (saturday_slots if day == 'Saturday' else time_slots)} for day in days}

    # Track year usage per time slot per day
    year_slot_usage = {day: {slot: set() for slot in (saturday_slots if day == 'Saturday' else time_slots)} for day in days}

    # Track section usage per time slot per day
    section_slot_usage = {day: {slot: set() for slot in (saturday_slots if day == 'Saturday' else time_slots)} for day in days}

    # Track subject assignment history for each section
    section_subject_state = {section: {'cycle_position': 0, 'assigned_dates': set()}
                             for year in years_sections for section in years_sections[year]}

    # Calculate total sections that need lab assignments
    total_sections_to_assign = sum(1 for section in num_labs_per_section if num_labs_per_section[section] >= 2)

    # Calculate maximum possible lab pair assignments
    max_pairs_per_week = calculate_max_labs_per_week(time_slots, saturday_slots, lab_pairs)
    max_section_assignments = max_pairs_per_week

    print(f"Resource calculation:")
    print(f"- Total sections needing labs: {total_sections_to_assign}")
    print(f"- Maximum section assignments possible: {max_section_assignments}")
    print(f"- Total lab slots per week: {max_section_assignments * 2} (each section gets 2 lab slots)")

    # Check if the total sections exceed the maximum capacity
    if not check_lab_capacity(total_sections_to_assign, max_section_assignments):
        print("Warning: The required lab assignments exceed the maximum capacity.")
        print("Some sections might not get all their required lab slots.")

    # Track assignments made for each section
    section_assignments = {section: 0 for year in years_sections for section in years_sections[year]}
    total_labs_to_assign = sum(num_labs_per_section.values())
    labs_assigned = 0

    # Track which day-slots we've tried for each section to avoid repeated attempts
    tried_slots = {(year, section): set() for year, section in section_list}

    # Maximum attempts to prevent infinite loop
    max_attempts = 1000
    attempt_counter = 0

    # First scheduling pass - try to assign each section its required labs
    while priority_queue and labs_assigned < total_labs_to_assign and attempt_counter < max_attempts:
        attempt_counter += 1
        year, section, _ = priority_queue.pop(0)  # Get highest priority section

        if num_labs_per_section[section] < 2:
            continue  # Skip if fewer than 2 labs needed (we assign in pairs)

        # Get subject count for this year
        subject_count = len(subjects_per_year[year])
        if subject_count < 2:
            print(f"Warning: Year {year} needs at least 2 subjects for rotation.")
            continue

        # Determine subjects based on the current cycle position
        cycle_pos = section_subject_state[section]['cycle_position']
        if subject_count == 2:
            # For 2 subjects rotation
            if cycle_pos == 0:
                subject1 = subjects_per_year[year][0]
                subject2 = subjects_per_year[year][1]
            else:  # cycle_pos == 1
                subject1 = subjects_per_year[year][1]
                subject2 = subjects_per_year[year][0]
        elif subject_count == 3:
            # For 3 subjects rotation
            if cycle_pos == 0:
                subject1 = subjects_per_year[year][0]
                subject2 = subjects_per_year[year][1]
            elif cycle_pos == 1:
                subject1 = subjects_per_year[year][2]
                subject2 = subjects_per_year[year][0]
            else:  # cycle_pos == 2
                subject1 = subjects_per_year[year][1]
                subject2 = subjects_per_year[year][2]
        else:
            # For more than 3 subjects
            idx1 = cycle_pos % subject_count
            idx2 = (cycle_pos + 1) % subject_count
            subject1 = subjects_per_year[year][idx1]
            subject2 = subjects_per_year[year][idx2]

        # Try each day and time slot
        assigned = False
        for day in days:
            # Skip days this section already has an assignment on
            if day in section_subject_state[section]['assigned_dates']:
                continue

            slot_options = saturday_slots if day == 'Saturday' else time_slots
            for time_slot in slot_options:

                # Skip if we've already tried this combination
                if (day, time_slot) in tried_slots[(year, section)]:
                    continue

                # Mark this slot as tried
                tried_slots[(year, section)].add((day, time_slot))

                # Skip if this section already has a lab in this slot
                if section in section_slot_usage[day][time_slot]:
                    continue

                # Skip if the year already has a lab in this slot (to avoid year conflicts)
                if year in year_slot_usage[day][time_slot]:
                    continue

                # Try each lab pair
                for lab1, lab2 in lab_pairs:
                    # Check if both labs in the pair are available
                    if lab1 not in lab_usage[day][time_slot] and lab2 not in lab_usage[day][time_slot]:
                        # Found an available slot and lab pair!

                        # Assign Batch 1
                        lab_usage[day][time_slot].add(lab1)
                        year_slot_usage[day][time_slot].add(year)
                        section_slot_usage[day][time_slot].add(section)

                        batch1 = f'Batch 1 (Lab {lab1}, {subject1})'
                        lab_schedule.append({
                            'Year': year,
                            'Section': section,
                            'Day': day,
                            'Time': f'{time_slot[0]}:00 - {time_slot[1]}:00',
                            'Batch': batch1,
                            'Subject': subject1
                        })
                        num_labs_per_section[section] -= 1
                        labs_assigned += 1

                        # Assign Batch 2
                        lab_usage[day][time_slot].add(lab2)
                        batch2 = f'Batch 2 (Lab {lab2}, {subject2})'
                        lab_schedule.append({
                            'Year': year,
                            'Section': section,
                            'Day': day,
                            'Time': f'{time_slot[0]}:00 - {time_slot[1]}:00',
                            'Batch': batch2,
                            'Subject': subject2
                        })
                        num_labs_per_section[section] -= 1
                        labs_assigned += 1

                        # Update tracking
                        section_subject_state[section]['assigned_dates'].add(day)
                        section_assignments[section] += 1

                        # Update cycle position
                        if subject_count == 2:
                            section_subject_state[section]['cycle_position'] = (cycle_pos + 1) % 2
                        elif subject_count == 3:
                            section_subject_state[section]['cycle_position'] = (cycle_pos + 1) % 3
                        else:
                            section_subject_state[section]['cycle_position'] = (cycle_pos + 1) % subject_count

                        assigned = True
                        break
                if assigned:
                    break
            if assigned:
                break

        # If this section still needs labs, add it back to the queue
        if num_labs_per_section[section] >= 2:
            priority_queue.append((year, section, num_labs_per_section[section]))
        elif num_labs_per_section[section] == 1:
            print(f"Warning: Section {section} has 1 lab remaining which cannot be assigned (labs are assigned in pairs).")

    # Check if we hit the max attempts limit
    if attempt_counter >= max_attempts:
        print(f"Warning: Reached maximum scheduling attempts ({max_attempts}).")
        print("This could indicate a scheduling conflict or inadequate resources.")

    # If not all labs are assigned, show a warning
    if labs_assigned < total_labs_to_assign:
        print(f"Warning: Only {labs_assigned} out of {total_labs_to_assign} labs were assigned.")
        print("This could be due to scheduling constraints or resource limitations.")

        # Report on remaining unassigned labs
        for section in num_labs_per_section:
            if num_labs_per_section[section] > 0:
                year = next(y for y in years_sections if section in years_sections[y])
                print(f"  - {year} - {section}: {num_labs_per_section[section]} labs remaining")
    else:
        print(f"Success! All {total_labs_to_assign} labs were successfully assigned.")

    return lab_schedule

def print_lab_timetable(lab_schedule):
    if not lab_schedule:
        print("\nNo labs were scheduled.")
        return []

    # Sort the schedule by Day, Time, Year, Section, Batch
    day_order = {'Monday': 0, 'Tuesday': 1, 'Wednesday': 2, 'Thursday': 3, 'Friday': 4, 'Saturday': 5}
    sorted_schedule = sorted(
        lab_schedule,
        key=lambda x: (
            day_order[x['Day']],
            x['Time'],
            x['Year'],
            x['Section'],
            x['Batch']
        )
    )

    print("\nLab Timetable:")
    print("Year    | Section  | Day       | Time Slot     | Batch")
    print("-----------------------------------------------------------")
    for entry in sorted_schedule:
        print(f"{entry['Year']:7} | {entry['Section']:8} | {entry['Day']:9} | {entry['Time']:13} | {entry['Batch']}")

    # Print summary by day
    print("\nSchedule Summary by Day:")
    days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
    for day in days:
        day_entries = [entry for entry in sorted_schedule if entry['Day'] == day]
        if day_entries:
            print(f"{day}: {len(day_entries)} lab sessions")

    # Print lab utilization
    print("\nLab Utilization:")
    labs = set()
    for entry in sorted_schedule:
        batch = entry['Batch']
        lab_num = int(batch.split('Lab ')[1].split(',')[0])
        labs.add(lab_num)

    print(f"Labs used: {', '.join(str(lab) for lab in sorted(labs))}")

    # Print section allocation summary
    print("\nSection Allocation Summary:")
    section_labs = {}
    for entry in sorted_schedule:
        section = entry['Section']
        if section not in section_labs:
            section_labs[section] = 0
        section_labs[section] += 1

    for section in sorted(section_labs.keys()):
        print(f"{section}: {section_labs[section]} lab sessions")

    return sorted_schedule

def generate_teacher_timetables(years, sections, subjects, schedule, teacher_assignments, time_slots, days, lab_schedule, solver):
    """
    Generate individual timetables for each teacher based on their subject allocations.

    Parameters:
    - years: List of years
    - sections: Dictionary mapping years to lists of sections
    - subjects: Dictionary mapping years to lists of subjects
    - schedule: Dictionary of schedule variables
    - teacher_assignments: Dictionary mapping (year, section, subject) to teacher names
    - time_slots: List of time slots
    - days: List of days
    - lab_schedule: List of lab scheduling information
    - solver: CP solver instance with solution values

    Returns:
    - Dictionary mapping teacher names to their individual timetables
    """
    # First, identify all teachers in the system
    all_teachers = set()
    for (year, section, subject), teacher in teacher_assignments.items():
        all_teachers.add(teacher)

    print(f"\n===== INDIVIDUAL TEACHER TIMETABLES =====")
    print(f"Total teachers: {len(all_teachers)}")

    # For each teacher, create a timetable
    for teacher in sorted(all_teachers):
        print(f"\n\n== Timetable for Teacher: {teacher} ==")

        # Create timetable data structure (day × time)
        table_data = []
        headers = ["Day"] + time_slots

        # Track teacher's total teaching hours and lab supervision
        total_class_hours = 0
        lab_supervision = set()  # Store unique (year, section, subject, day, time) lab supervisions

        # For each day, populate the timetable
        for day in days:
            row = [day]
            for slot in time_slots:
                # Check if the teacher has a class at this time
                class_entry = "--"
                for year in years:
                    for section in sections[year]:
                        for subject in subjects.get(year, []):
                            if teacher_assignments.get((year, section, subject)) == teacher:
                                if solver.Value(schedule.get((year, section, subject, day, slot), 0)) == 1:
                                    class_entry = f"{year}-{section} {subject}"
                                    total_class_hours += 1

                                # Check if there's a lab for this subject supervised by this teacher
                                for lab in lab_schedule:
                                    if (lab['Year'] == year and
                                        lab['Section'] == section and
                                        lab['Day'] == day and
                                        lab['Subject'] == subject):

                                        lab_time = lab['Time']
                                        lab_start = int(lab_time.split(':')[0])
                                        lab_end = int(lab_time.split(' - ')[1].split(':')[0])
                                        slot_hour = int(slot.split(':')[0])

                                        if lab_start <= slot_hour < lab_end:
                                            class_entry = f"LAB {year}-{section} {subject}"
                                            lab_key = (year, section, subject, day, lab_time)
                                            lab_supervision.add(lab_key)

                row.append(class_entry)

            table_data.append(row)

        # Print the teacher's timetable
        print(tabulate(table_data, headers=headers, tablefmt="grid"))

        # Print summary statistics for this teacher
        print(f"\nSummary for {teacher}:")
        print(f"Total teaching hours per week: {total_class_hours}")
        print(f"Total lab supervision sessions: {len(lab_supervision)}")

        # Calculate teaching load by day
        daily_load = {}
        for day in days:
            day_hours = sum(
                solver.Value(schedule.get((year, section, subject, day, slot), 0))
                for year in years
                for section in sections[year]
                for subject in subjects.get(year, [])
                for slot in time_slots
                if teacher_assignments.get((year, section, subject)) == teacher
            )
            daily_load[day] = day_hours

        print("Daily teaching load:")
        for day, hours in daily_load.items():
            print(f"  {day}: {hours} hours")

        # List all subjects taught
        subjects_taught = set()
        for (year, section, subject), assigned_teacher in teacher_assignments.items():
            if assigned_teacher == teacher:
                subjects_taught.add(f"{year} - {subject}")

        print("Subjects taught:")
        for subject in sorted(subjects_taught):
            print(f"  {subject}")

class IntegratedTimetableSolver:
    def __init__(self, lab_schedule, years_sections):
        # Time slots for regular classes (1-hour slots)
        self.time_slots = [
            '8:00-9:00', '9:00-10:00', '10:00-11:00', '11:00-12:00',
            '12:00-13:00', '13:00-14:00', '14:00-15:00', '15:00-16:00',
            '16:00-17:00'
        ]

        self.days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
        self.weekdays = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
        self.break_slot = '12:00-13:00'
        self.max_hours_per_day = 8

        # Mapping time slots to index positions
        self.time_slot_indices = {slot: i for i, slot in enumerate(self.time_slots)}

        self.lab_schedule = lab_schedule or []  # Ensure lab_schedule is not None
        self.years_sections = years_sections

        # Extract unique years and sections from lab schedule and years_sections
        self.years = []
        self.sections = {}

        # First, add all years and sections from years_sections
        for year in years_sections:
            if year not in self.years:
                self.years.append(year)
            self.sections[year] = list(years_sections[year])

        # Then add any missing from lab_schedule (if it's not empty)
        if lab_schedule:
            for entry in lab_schedule:
                year = entry['Year']
                section = entry['Section']

                if year not in self.years:
                    self.years.append(year)

                if year not in self.sections:
                    self.sections[year] = []

                if section not in self.sections[year]:
                    self.sections[year].append(section)

        # Get number of core subjects per year and calculate required teachers
        self.core_subjects_per_year = self.get_core_subjects_info()
        self.required_teachers = self.calculate_required_teachers()

        # Get classrooms from user
        self.classrooms = self.get_classroom_input()

        # Get subjects, teachers and hours required per subject per year
        self.subjects, self.teacher_assignments, self.hours_per_subject = self.get_subject_data()

        # Identify the language subject for each year
        self.lang_subject = self.identify_lang_subject()

        # Calculate continuous timeslot ranges for each section and day
        self.continuous_time_slots = self.calculate_continuous_time_slots()

        # Create the model
        self.model = cp_model.CpModel()
        self.schedule = {}

    def get_core_subjects_info(self):
        """Get the number of core subjects per year."""
        core_subjects_per_year = {}
        print("\nEnter the number of core subjects for each year:")
        for year in self.years:
            while True:
                try:
                    num_subjects = int(input(f"Enter number of core subjects for Year {year}: "))
                    if num_subjects <= 0:
                        print("Number of subjects must be positive. Please try again.")
                    else:
                        core_subjects_per_year[year] = num_subjects
                        break
                except ValueError:
                    print("Please enter a valid number.")
        return core_subjects_per_year

    def calculate_required_teachers(self):
        """Calculate required teachers based on the formula."""
        required_teachers = {}
        print("\nCalculating required teachers per year:")
        for year in self.years:
            num_sections = len(self.sections[year])
            num_subjects = self.core_subjects_per_year[year]

            # Calculate using the formula
            product = num_sections * num_subjects
            if product % 2 == 0:  # If even
                required = product // 2
            else:  # If odd
                required = (product + 1) // 2

            required_teachers[year] = required
            print(f"Year {year}: {num_sections} sections × {num_subjects} subjects = {product}")
            print(f" → {required} teachers required")

        return required_teachers

    def identify_lang_subject(self):
        """Identify the language subject for each year."""
        lang_subject = {}
        for year in self.years:
            if year in self.subjects:
                print(f"\nIdentify language subject for Year {year}")
                print(f"Available subjects: {', '.join(self.subjects[year])}")
                lang = input(f"Enter the name of the language subject for Year {year} (or 'none' if none): ")
                if lang.lower() != 'none' and lang in self.subjects[year]:
                    lang_subject[year] = lang
                    print(f"Language subject '{lang}' identified for Year {year}")
                else:
                    print(f"No language subject set for Year {year}")
        return lang_subject

    def get_classroom_input(self):
        """Get classroom information from user."""
        num_classrooms = int(input("Enter number of classrooms available: "))
        classrooms = []
        for i in range(num_classrooms):
            room_name = input(f"Enter name for classroom {i+1}: ")
            classrooms.append(room_name)
        return classrooms

    def get_subject_data(self):
        """Get subject, teacher and hours data for each year, including both core and additional subjects."""
        subjects = {}
        teacher_assignments = {}
        hours_per_subject = {}

        for year in self.years:
            subjects[year] = []

            print(f"\nEnter data for Year {year}")
            print(f"You need to assign {self.required_teachers[year]} teachers for {self.core_subjects_per_year[year]} core subjects across {len(self.sections[year])} sections")

            # Ask for core subjects
            print(f"Enter {self.core_subjects_per_year[year]} core subjects for Year {year}:")
            core_subjects = []
            for i in range(self.core_subjects_per_year[year]):
                subject_input = input(f"Core Subject {i+1} name: ")
                core_subjects.append(subject_input)
                subjects[year].append(subject_input)

                # Ask for weekly hours
                hours_input = int(input(f"Weekly hours required for {subject_input}: "))
                hours_per_subject[(year, subject_input)] = hours_input

            # Now ask for additional subjects
            additional_subjects = []
            while True:
                add_more = input("\nDo you want to add additional subjects for Year " + year + "? (yes/no): ").lower()
                if add_more != 'yes':
                    break

                subject_input = input("Additional subject name: ")
                additional_subjects.append(subject_input)
                subjects[year].append(subject_input)

                # Ask for weekly hours
                hours_input = int(input(f"Weekly hours required for {subject_input}: "))
                hours_per_subject[(year, subject_input)] = hours_input

                # Ask for teacher directly for this additional subject
                for section in self.sections[year]:
                    teacher_name = input(f"Enter teacher for {subject_input} for Section {section}: ")
                    teacher_assignments[(year, section, subject_input)] = teacher_name

            # Assign teachers to core subjects
            if core_subjects:
                print(f"\nAssign {self.required_teachers[year]} teachers for core subjects in Year {year}:")
                teacher_list = []
                for i in range(self.required_teachers[year]):
                    teacher_name = input(f"Enter name for Teacher {i+1}: ")
                    teacher_list.append(teacher_name)

                # Now assign teachers to core subjects for each section
                print("\nAssigning teachers to core subjects for each section:")
                teacher_index = 0
                for section in self.sections[year]:
                    for subject in core_subjects:
                        # Assign the next teacher in the rotation
                        teacher_assignments[(year, section, subject)] = teacher_list[teacher_index]
                        print(f"Assigned {teacher_list[teacher_index]} to {subject} for Section {section}")

                        # Move to next teacher, wrap around if needed
                        teacher_index = (teacher_index + 1) % len(teacher_list)

        return subjects, teacher_assignments, hours_per_subject

    def slot_overlaps_lab(self, year, section, day, time_slot):
        """Check if a class time slot overlaps with a lab session."""
        # Extract hour from time slot (e.g., '8:00-9:00' -> 8)
        start_hour = int(time_slot.split(':')[0])

        # Check each lab session for this section
        for lab in self.lab_schedule:
            if lab['Year'] == year and lab['Section'] == section and lab['Day'] == day:
                # Parse lab time range (e.g., '8:00 - 11:00')
                lab_start, lab_end = lab['Time'].split(' - ')
                lab_start_hour = int(lab_start.split(':')[0])
                lab_end_hour = int(lab_end.split(':')[0])

                # If class start time falls within lab session time, there's an overlap
                if lab_start_hour <= start_hour < lab_end_hour:
                    return True

        return False

    def get_lab_time_for_section(self, year, section, day):
        """Get lab start and end times for a section on a given day, or None if no lab."""
        for lab in self.lab_schedule:
            if lab['Year'] == year and lab['Section'] == section and lab['Day'] == day:
                lab_start, lab_end = lab['Time'].split(' - ')
                lab_start_hour = int(lab_start.split(':')[0])
                lab_end_hour = int(lab_end.split(':')[0])
                return (lab_start_hour, lab_end_hour)
        return None

    def calculate_continuous_time_slots(self):
        """
        Calculate continuous timeslot ranges for each section on each day.
        Based on the following rules:
        - If lab is at 8:00 AM, classes should be allocated till 4:00 PM
        - If lab is at 11:00 AM, classes should be allocated from 9:00 AM
        - If lab is at 2:00 PM, classes should be allocated from 9:00 AM
        - Otherwise, allocate continuous classes from 9:00 AM
        """
        continuous_slots = {}

        for year in self.years:
            continuous_slots[year] = {}
            for section in self.sections[year]:
                continuous_slots[year][section] = {}

                for day in self.days:
                    # Get lab time for this section on this day
                    lab_time = self.get_lab_time_for_section(year, section, day)

                    # Apply rules based on lab timing
                    if lab_time:
                        lab_start_hour, lab_end_hour = lab_time

                        if lab_start_hour == 8:
                            # If lab is at 8:00 AM, classes should be till 4:00 PM (16:00)
                            # Lab is at beginning, so classes after lab till 15:00
                            start_idx = self.time_slot_indices[f'{lab_end_hour}:00-{lab_end_hour+1}:00']
                            end_idx = self.time_slot_indices.get('16:00-17:00', len(self.time_slots)-1)
                            allowed_slots = self.time_slots[start_idx:end_idx+1]

                        elif lab_start_hour == 11:
                            # If lab is at 11:00 AM, classes should be from 9:00 AM
                            # Classes before lab from 9:00 and after lab if needed
                            before_lab = self.time_slots[self.time_slot_indices['9:00-10:00']:self.time_slot_indices[f'{lab_start_hour}:00-{lab_start_hour+1}:00']]
                            after_lab = self.time_slots[self.time_slot_indices[f'{lab_end_hour}:00-{lab_end_hour+1}:00']:] if lab_end_hour < 17 else []
                            # allowed_slots = before_lab + after_lab
                            # Add a break slot right after the lab ends
                            break_slot_after_lab = [self.break_slot]

                            # Get slots after the break (if any remaining hours)
                            break_slot_idx = self.time_slot_indices.get(f'{lab_end_hour}:00-{lab_end_hour+1}:00', None)
                            after_break = [] if break_slot_idx is None or break_slot_idx >= len(self.time_slots)-1 else self.time_slots[break_slot_idx+1:]

                            allowed_slots = before_lab + break_slot_after_lab + after_break

                        elif lab_start_hour == 14:  # 2:00 PM
                            # If lab is at 2:00 PM, classes should be from 9:00 AM
                            # Classes before lab from 9:00
                            start_idx = self.time_slot_indices['9:00-10:00']
                            end_idx = self.time_slot_indices[f'{lab_start_hour}:00-{lab_start_hour+1}:00'] - 1
                            allowed_slots = self.time_slots[start_idx:end_idx+1]

                        else:
                            # For other lab times, handle appropriately
                            before_lab = self.time_slots[self.time_slot_indices['9:00-10:00']:self.time_slot_indices[f'{lab_start_hour}:00-{lab_start_hour+1}:00']]
                            after_lab = self.time_slots[self.time_slot_indices[f'{lab_end_hour}:00-{lab_end_hour+1}:00']:] if lab_end_hour < 17 else []
                            allowed_slots = before_lab + after_lab

                    else:
                        # No lab on this day, allocate continuous classes from 9:00 AM
                        start_idx = self.time_slot_indices['9:00-10:00']
                        allowed_slots = self.time_slots[start_idx:]

                    # Remove break slot on weekdays (except for the 11:00 AM lab case where we explicitly added it)
                    if day in self.weekdays and self.break_slot in allowed_slots and lab_time and lab_start_hour != 11:
                        allowed_slots = [slot for slot in allowed_slots if slot != self.break_slot]

                # Store the allowed slots for this day
                    continuous_slots[year][section][day] = allowed_slots

                # Create a formatted output string that highlights the break slot
                    output_slots = []
                    for slot in allowed_slots:
                        if slot == self.break_slot:
                            output_slots.append(f"[BREAK: {slot}]")
                        else:
                            output_slots.append(slot)
                    print(f"For Year {year}, Section {section}, {day}: {', '.join(output_slots)}")
        return continuous_slots

    def count_lab_hours_in_day(self, year, section, day):
      """Count the number of hours spent in labs on a given day."""
      lab_hours = 0

    # Get unique lab sessions by start/end time to avoid counting duplicates
      counted_sessions = set()

      for lab in self.lab_schedule:
          if lab['Year'] == year and lab['Day'] == day and lab['Section'] == section:
              time_key = lab['Time']  # Use the time string as a key

            # Only count each time slot once
              if time_key not in counted_sessions:
                  counted_sessions.add(time_key)

                  # Parse lab time range
                  lab_start, lab_end = lab['Time'].split(' - ')
                  lab_start_hour = int(lab_start.split(':')[0])
                  lab_end_hour = int(lab_end.split(':')[0])

                  # Add the duration of this lab
                  lab_hours += (lab_end_hour - lab_start_hour)

      return lab_hours

    def create_variables(self):
        """Create decision variables for the schedule."""
        # Create schedule variables for each year, section, subject, day, and time slot
        for year in self.years:
            for section in self.sections[year]:
                for subject in self.subjects.get(year, []):
                    for day in self.days:
                        for slot in self.time_slots:
                            self.schedule[(year, section, subject, day, slot)] = self.model.NewBoolVar(
                                f'y{year}_s{section}_{subject}_{day}_{slot}')

    def add_constraints(self):
        """Add constraints to the model."""
        # 1. Each subject must be scheduled for the specified number of hours per week
        for year in self.years:
            for section in self.sections[year]:
                for subject in self.subjects.get(year, []):
                    self.model.Add(sum(self.schedule[(year, section, subject, day, slot)]
                                        for day in self.days
                                        for slot in self.time_slots) == self.hours_per_subject.get((year, subject), 0))

        # 9. No same subject allocation more than once per day for each section
        for year in self.years:
            for section in self.sections[year]:
                for subject in self.subjects.get(year, []):
                    for day in self.days:
                        self.model.Add(
                            sum(self.schedule[(year, section, subject, day, slot)]
                                for slot in self.time_slots) <= 1
                        )

        # 2. No teacher can be assigned to more than one class at the same time
        for day in self.days:
            for slot in self.time_slots:
                teacher_classes = {}
                for year in self.years:
                    for section in self.sections[year]:
                        for subject in self.subjects.get(year, []):
                            teacher = self.teacher_assignments.get((year, section, subject))
                            if teacher:
                                if teacher not in teacher_classes:
                                    teacher_classes[teacher] = []
                                teacher_classes[teacher].append((year, section, subject))

                # Add constraint for each teacher
                for teacher, assignments in teacher_classes.items():
                    self.model.Add(sum(self.schedule[(year, section, subject, day, slot)]
                                      for year, section, subject in assignments) <= 1)

        # 3. No section can have more than one class at the same time
        for year in self.years:
            for section in self.sections[year]:
                for day in self.days:
                    for slot in self.time_slots:
                        self.model.Add(sum(self.schedule[(year, section, subject, day, slot)]
                                          for subject in self.subjects.get(year, [])) <= 1)

        # 4. No class can be scheduled when a lab is already scheduled
        for year in self.years:
            for section in self.sections[year]:
                for day in self.days:
                    for slot in self.time_slots:
                        if self.slot_overlaps_lab(year, section, day, slot):
                            self.model.Add(sum(self.schedule[(year, section, subject, day, slot)]
                                              for subject in self.subjects.get(year, [])) == 0)

        # 5. No more classes than available classrooms at any time
        for day in self.days:
            for slot in self.time_slots:
                self.model.Add(sum(self.schedule[(year, section, subject, day, slot)]
                                   for year in self.years
                                   for section in self.sections[year]
                                   for subject in self.subjects.get(year, [])) <= len(self.classrooms))

        # 6. No classes on Saturday afternoon (after 12:00)
        for slot in self.time_slots:
            start_hour = int(slot.split(':')[0])
            if start_hour >= 12 and 'Saturday' in self.days:  # 12 PM or later
                self.model.Add(sum(self.schedule[(year, section, subject, 'Saturday', slot)]
                                   for year in self.years
                                   for section in self.sections[year]
                                   for subject in self.subjects.get(year, [])) == 0)

        # 7. No classes during break time (12:00-13:00) on weekdays
        # Skip this constraint if there's already a lab scheduled
        for day in self.weekdays:  # Only Monday to Friday
            for year in self.years:
                for section in self.sections[year]:
                    # Only add the break constraint if there's no lab scheduled at that time
                    if not self.slot_overlaps_lab(year, section, day, self.break_slot):
                        # Prevent any subject from being scheduled during break
                        self.model.Add(sum(self.schedule[(year, section, subject, day, self.break_slot)]
                                          for subject in self.subjects.get(year, [])) == 0)

        # 8. Limit each section to a maximum of 8 hours per day (including break)
        for year in self.years:
            for section in self.sections[year]:
                for day in self.days:
                    # Count lab hours for this section on this day
                    lab_hours = self.count_lab_hours_in_day(year, section, day)

                    # Check if the break slot is used (not overlapped by a lab)
                    break_used = 0
                    if day in self.weekdays and not self.slot_overlaps_lab(year, section, day, self.break_slot):
                        break_used = 1

                    # Total class hours (each scheduled class = 1 hour)
                    class_hours = sum(self.schedule[(year, section, subject, day, slot)]
                                     for subject in self.subjects.get(year, [])
                                     for slot in self.time_slots)

                    # Limit total hours to max_hours_per_day
                    self.model.Add(class_hours + lab_hours + break_used <= self.max_hours_per_day)

        # 10. Language subject must be scheduled at the same time for all sections of the same year
        for year in self.years:
            # Skip if this year doesn't have a language subject identified
            if year not in self.lang_subject:
                continue

            lang = self.lang_subject[year]

            # For each day and time slot
            for day in self.days:
                for slot in self.time_slots:
                    # If any section has language scheduled at this time, all other sections
                    # that don't have labs at this time must also have language

                    # Create a list of sections that don't have labs at this time
                    available_sections = []
                    for section in self.sections[year]:
                        if not self.slot_overlaps_lab(year, section, day, slot):
                            available_sections.append(section)

                    # Skip if fewer than 2 sections are available (nothing to synchronize)
                    if len(available_sections) < 2:
                        continue

                    # Create variables that indicate if any section has lang at this time
                    any_lang_scheduled = self.model.NewBoolVar(f'any_lang_{year}_{day}_{slot}')

                    # Connect the indicator variable to the actual schedules
                    self.model.AddMaxEquality(
                        any_lang_scheduled,
                        [self.schedule[(year, section, lang, day, slot)]
                         for section in available_sections]
                    )

                    # If any section has lang, all available sections must have lang
                    for section in available_sections:
                        self.model.AddImplication(
                            any_lang_scheduled,
                            self.schedule[(year, section, lang, day, slot)]
                        )

        # 11. NEW: Continuous allocation constraint - classes must be scheduled within the allowed time slots
        for year in self.years:
            for section in self.sections[year]:
                for day in self.days:
                    allowed_slots = self.continuous_time_slots[year][section][day]
                    disallowed_slots = [slot for slot in self.time_slots if slot not in allowed_slots]

                    # No classes can be scheduled in disallowed slots
                    for slot in disallowed_slots:
                        # Skip if this slot overlaps with a lab (already handled by constraint 4)
                        if not self.slot_overlaps_lab(year, section, day, slot):
                            self.model.Add(sum(self.schedule[(year, section, subject, day, slot)]
                                             for subject in self.subjects.get(year, [])) == 0)

        # 12. NEW: Try to schedule classes continuously without gaps
        for year in self.years:
            for section in self.sections[year]:
                for day in self.days:
                    allowed_slots = self.continuous_time_slots[year][section][day]

                    # Skip days with insufficient slots
                    if len(allowed_slots) <= 1:
                        continue

                    # Create variables to track if a slot is used
                    slot_used = {}
                    for slot in allowed_slots:
                        slot_used[(day, slot)] = self.model.NewBoolVar(f'slot_used_{year}_{section}_{day}_{slot}')

                        # Link slot_used to actual class schedule
                        # slot_used = 1 if any class is scheduled in this slot
                        self.model.Add(slot_used[(day, slot)] == 0).OnlyEnforceIf(
                            [self.schedule[(year, section, subject, day, slot)].Not()
                             for subject in self.subjects.get(year, [])])

                        for subject in self.subjects.get(year, []):
                            self.model.AddImplication(
                                self.schedule[(year, section, subject, day, slot)],
                                slot_used[(day, slot)]
                            )

                    # Add constraints to minimize gaps between used slots
                    # For each consecutive pair of slots, if the later slot is used, either the earlier slot
                    # is used or all slots between are used
                    for i in range(len(allowed_slots) - 1):
                        for j in range(i + 2, len(allowed_slots)):
                            # If slot j is used and some slot between i and j is not used, then slot i is not used
                            # This encourages continuous block scheduling
                            gap_exists = self.model.NewBoolVar(f'gap_{year}_{section}_{day}_{i}_{j}')

                            # Check if any slot between i+1 and j-1 is not used
                            middle_slots_all_used = self.model.NewBoolVar(f'middle_all_used_{year}_{section}_{day}_{i}_{j}')

                            if j > i + 1:  # If there are slots between i and j
                                middle_slot_vars = [slot_used[(day, allowed_slots[k])] for k in range(i+1, j)]
                                self.model.AddMinEquality(
                                    middle_slots_all_used,
                                    middle_slot_vars
                                )

                                # gap_exists is true if j is used, middle is not all used, and i is not used
                                self.model.AddBoolAnd([
                                    slot_used[(day, allowed_slots[j])],
                                    middle_slots_all_used.Not(),
                                    slot_used[(day, allowed_slots[i])].Not()
                                ]).OnlyEnforceIf(gap_exists)

                                # If gap_exists is false, then either j is not used, all middle slots are used, or i is used
                                self.model.AddBoolOr([
                                    slot_used[(day, allowed_slots[j])].Not(),
                                    middle_slots_all_used,
                                    slot_used[(day, allowed_slots[i])]
                                ]).OnlyEnforceIf(gap_exists.Not())

                                # Minimize gaps
                                self.model.Add(gap_exists == 0)

    def solve(self):
        """Solve the model and print the timetable."""
        solver = cp_model.CpSolver()
        status = solver.Solve(self.model)

        if status in (cp_model.FEASIBLE, cp_model.OPTIMAL):
            print("\nComplete Timetable Generated Successfully!")

            # Create combined timetable for each year and section
            for year in self.years:
                for section in self.sections[year]:
                    print(f"\n=== Year {year}, Section {section} Timetable ===")

                    # Create timetable data
                    table_data = []
                    headers = ["Day"] + self.time_slots

                    for day in self.days:
                        row = [day]
                        for slot in self.time_slots:
                            # Check if there's a lab session
                            lab_entry = None
                            for lab in self.lab_schedule:
                                if (lab['Year'] == year and
                                    lab['Section'] == section and
                                    lab['Day'] == day):
                                    lab_time = lab['Time']
                                    lab_start = int(lab_time.split(':')[0])
                                    lab_end = int(lab_time.split(' - ')[1].split(':')[0])
                                    slot_hour = int(slot.split(':')[0])

                                    if lab_start <= slot_hour < lab_end:
                                        batch_info = lab['Batch'].split('(')[0].strip()  # Extract "Batch 1" or "Batch 2"
                                        lab_entry = f"LAB {lab['Subject']} ({batch_info})"
                                        break

                            if lab_entry:
                                row.append(lab_entry)
                            # Check if it's break time (12:00-13:00) on weekdays
                            elif slot == self.break_slot and day in self.weekdays:
                                row.append("BREAK")  # Mark as break time
                            else:
                                # Check if there's a class scheduled
                                class_entry = "--"
                                for subject in self.subjects.get(year, []):
                                    if solver.Value(self.schedule.get((year, section, subject, day, slot), 0)) == 1:
                                        teacher = self.teacher_assignments.get((year, section, subject), "")
                                        class_entry = f"{subject} ({teacher})"
                                        break
                                row.append(class_entry)

                        table_data.append(row)

                    # Print timetable
                    print(tabulate(table_data, headers=headers, tablefmt="grid"))

                    # Calculate total hours for this section for each day
                    print("\nDaily Hours Summary:")
                    for day in self.days:
                        lab_hours = self.count_lab_hours_in_day(year, section, day)
                        class_hours = sum(
                            solver.Value(self.schedule.get((year, section, subject, day, slot), 0))
                            for subject in self.subjects.get(year, [])
                            for slot in self.time_slots
                        )
                        break_hours = 0
                        if day in self.weekdays and not self.slot_overlaps_lab(year, section, day, self.break_slot):
                            break_hours = 1

                        total_hours = lab_hours + class_hours + break_hours
                        print(f"{day}: {total_hours} hours (Lab: {lab_hours}, Class: {class_hours}, Break: {break_hours})")

            #Print language subject synchronization summary
            if any(self.lang_subject):
                print("\nLanguage Subject Synchronization Summary:")
                for year in self.lang_subject:
                    lang = self.lang_subject[year]
                    print(f"\nYear {year} - Language Subject: {lang}")

                    # Find all slots where language is scheduled
                    lang_slots = {}
                    for day in self.days:
                        for slot in self.time_slots:
                            # Check if language is scheduled for any section at this time
                            sections_with_lang = []
                            for section in self.sections[year]:
                                if solver.Value(self.schedule.get((year, section, lang, day, slot), 0)) == 1:
                                    sections_with_lang.append(section)

                            if sections_with_lang:
                                if day not in lang_slots:
                                    lang_slots[day] = {}
                                lang_slots[day][slot] = sections_with_lang

                    # Print the language schedule
                    if lang_slots:
                        for day in self.days:
                            if day in lang_slots:
                                for slot in sorted(lang_slots[day].keys()):
                                    sections = lang_slots[day][slot]
                                    print(f"  {day}, {slot}: {lang} scheduled for sections {', '.join(sections)}")

            # Print teacher assignment summary
            print("\nTeacher Assignment Summary:")
            # Group subjects into core and additional categories
            for year in self.years:
                core_subjects = self.subjects[year][:self.core_subjects_per_year[year]]
                additional_subjects = self.subjects[year][self.core_subjects_per_year[year]:]

                print(f"\nYear {year}:")
                print(f"  Required teachers for core subjects: {self.required_teachers[year]}")
                print(f"  Sections: {len(self.sections[year])}")
                print(f"  Core subjects: {self.core_subjects_per_year[year]}")
                if additional_subjects:
                    print(f"  Additional subjects: {len(additional_subjects)}")

                # Print teacher-subject-section assignments
                teachers_used = set()
                for (y, sec, subj), teacher in self.teacher_assignments.items():
                    if y == year:
                        teachers_used.add(teacher)

                print(f"  Total teachers assigned: {len(teachers_used)}")
                print("  Teacher assignments per section:")
                for section in self.sections[year]:
                    print(f"    Section {section}:")

                    # Print core subjects first
                    if core_subjects:
                        print(f"      Core Subjects:")
                        for subject in core_subjects:
                            teacher = self.teacher_assignments.get((year, section, subject), "Not assigned")
                            print(f"        {subject}: {teacher}")

                    # Then print additional subjects
                    if additional_subjects:
                        print(f"      Additional Subjects:")
                        for subject in additional_subjects:
                            teacher = self.teacher_assignments.get((year, section, subject), "Not assigned")
                            print(f"        {subject}: {teacher}")

            # Print summary statistics
            print("\nSchedule Summary:")
            total_classes = sum(
                solver.Value(self.schedule.get((year, section, subject, day, slot), 0))
                for year in self.years
                for section in self.sections[year]
                for subject in self.subjects.get(year, [])
                for day in self.days
                for slot in self.time_slots
            )
            print(f"Total scheduled classes: {total_classes}")
            print(f"Total scheduled lab sessions: {len(self.lab_schedule)}")

            # Count break slots
            break_count = sum(
                1 for day in self.weekdays
                for year in self.years
                for section in self.sections[year]
                if not any(
                    lab['Year'] == year and lab['Section'] == section and
                    lab['Day'] == day and self.slot_overlaps_lab(year, section, day, self.break_slot)
                    for lab in self.lab_schedule
                )
            )
            print(f"Total break slots: {break_count}")

            # Generate individual teacher timetables
            generate_teacher_timetables(
                self.years,
                self.sections,
                self.subjects,
                self.schedule,
                self.teacher_assignments,
                self.time_slots,
                self.days,
                self.lab_schedule,
                solver
            )
            return True
        else:
            print("\nNo feasible timetable found. Try adjusting constraints or requirements.")
            return False


def run_timetable_generation(
    years_sections,
    num_labs_per_section,
    subjects_per_year,
    classrooms,
    core_subjects_info,
    additional_subjects_info,
    teacher_names,
    lang_subjects
):
    """
    Parameters:
    - years_sections (dict): {"1": ["A", "B"], "2": ["A"]}
    - num_labs_per_section (dict): {"A": 2, "B": 4}
    - subjects_per_year (dict): {"1": ["ML", "MAD"], "2": ["Java", "DBMS"]}
    - classrooms (list): list of classroom names
    - core_subjects_info (dict): {"1": [("ML", 3), ("MAD", 2)]}
    - additional_subjects_info (dict): {"1": [("Python", 2, {"A": "T1", "B": "T2"})]}
    - teacher_names (dict): {"1": ["T1", "T2"]}
    - lang_subjects (dict): {"1": "English"}
    """
    from ortools.sat.python import cp_model
    # from app import store_timetable_in_db

    print("===== INTEGRATED TIMETABLE GENERATOR =====")
    print("\nPart 1: Lab Timetable Generation")

    # Generate and print the lab timetable
    lab_timetable = generate_lab_timetable(years_sections, num_labs_per_section, subjects_per_year)
    sorted_lab_schedule = print_lab_timetable(lab_timetable)
    print("\nLab Timetable Generated Successfully!")

    print("\n\nPart 2: Class Timetable Generation (Working Around Lab Schedule)")

    # Manually construct the solver with given inputs instead of relying on user input
    solver = IntegratedTimetableSolver(sorted_lab_schedule, years_sections)
    solver.classrooms = classrooms
    solver.core_subjects_per_year = {year: len(subjects) for year, subjects in core_subjects_info.items()}
    solver.required_teachers = {year: (len(sections) * len(core_subjects_info[year]) + 1) // 2
                                for year, sections in years_sections.items()}
    solver.subjects = {}
    solver.teacher_assignments = {}
    solver.hours_per_subject = {}

    for year in years_sections:
        solver.subjects[year] = []

        # Add core subjects
        for subject, hours in core_subjects_info.get(year, []):
            solver.subjects[year].append(subject)
            solver.hours_per_subject[(year, subject)] = hours

        # Assign core subject teachers
        core_teachers = teacher_names.get(year, [])
        teacher_idx = 0
        for section in years_sections[year]:
            for subject, _ in core_subjects_info.get(year, []):
                solver.teacher_assignments[(year, section, subject)] = core_teachers[teacher_idx % len(core_teachers)]
                teacher_idx += 1

        # Add additional subjects
        for subject, hours, section_teacher_map in additional_subjects_info.get(year, []):
            solver.subjects[year].append(subject)
            solver.hours_per_subject[(year, subject)] = hours
            for section, teacher in section_teacher_map.items():
                solver.teacher_assignments[(year, section, subject)] = teacher

    solver.lang_subject = lang_subjects
    solver.continuous_time_slots = solver.calculate_continuous_time_slots()

    solver.create_variables()
    solver.add_constraints()
    solver.solve()

    # Save to DB
    # store_timetable_in_db(
    #     sorted_lab_schedule,
    #     solver.schedule,
    #     solver.teacher_assignments
    # )


# Main program
def main(years,sections,num_labs ,subjects):
    # Need to import the CP-SAT solver at the beginning
    from ortools.sat.python import cp_model
    from tabulate import tabulate

    print("===== INTEGRATED TIMETABLE GENERATOR =====")
    print("\nPart 1: Lab Timetable Generation")

    # Get user input for lab timetable
    years_sections = {}
    # years = input("Enter years (e.g., 1,2,3): ").split(',')
    for year in years:
        # sections = input(f"Enter sections for {year.strip()} year (comma-separated): ").split(',')
        years_sections[year.strip()] = [section.strip() for section in sections]

    num_labs_per_section = {}
    for year in years_sections:
        for section in years_sections[year]:
            while True:
                try:
                    # num_labs = int(input(f"Enter number of labs for {year} - {section}: "))
                    if num_labs < 0:
                        raise ValueError("Number of labs cannot be negative.")
                    num_labs_per_section[section] = num_labs
                    break
                except ValueError as e:
                    print(f"Invalid input: {e}. Please enter a valid number.")

    # Input for subjects per year
    subjects_per_year = {}
    for year in years_sections:
        # subjects = input(f"Enter lab subjects for {year} year (comma-separated, e.g., ML,MAD,Java): ").split(',')
        subjects_per_year[year] = [subject.strip() for subject in subjects]

    # Generate and print the lab timetable
    lab_timetable = generate_lab_timetable(years_sections, num_labs_per_section, subjects_per_year)
    sorted_lab_schedule = print_lab_timetable(lab_timetable)
    print("\nLab Timetable Generated Successfully!")

    print("\n\nPart 2: Class Timetable Generation (Working Around Lab Schedule)")
    timetable_solver = IntegratedTimetableSolver(sorted_lab_schedule, years_sections)
    timetable_solver.create_variables()
    timetable_solver.add_constraints()
    timetable_solver.solve()

#     # Save to DB
#     store_timetable_in_db(
#         sorted_lab_schedule,
#         timetable_solver.schedule,
#         timetable_solver.teacher_assignments
#     )


if __name__ == "__main__":
    main()