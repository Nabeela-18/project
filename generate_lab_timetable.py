from datetime import time
import itertools
from ortools.sat.python import cp_model
from tabulate import tabulate

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


def main(years_sections, num_labs_per_section, subjects_per_year):
    days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
    time_slots = [(8, 11), (11, 14), (14, 17)]  # Available time slots (Monday to Friday)
    saturday_slots = [(8, 11), (11, 14)]  # Saturday has only morning slots

    # Create lab pairs
    labs = [1, 2, 3, 4, 5, 6]  # Available labs
    lab_pairs = [(1, 2), (3, 4), (5, 6)]  # Using fixed pairs to ensure consistent rotation

    lab_schedule = []
    # years_sections=years_sections.split(",")
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
