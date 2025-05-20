import streamlit as st
import random
import names
import pandas as pd
import io

# ------------ Data Model & Generation Logic ------------
class Employee:
    def __init__(self, emp_id, first_name, last_name, job_band, position_id, generic_job_title, manager_id=None, manager_position_id=None):
        self.emp_id = emp_id
        self.first_name = first_name
        self.last_name = last_name
        self.full_name = f"{first_name} {last_name}"
        self.job_band = job_band
        self.position_id = position_id
        self.manager_id = manager_id
        self.manager_position_id = manager_position_id
        self.generic_job_title = generic_job_title

# Please adjust distribution percentages as needed
def generate_employee_list(num_employees):
    band_distribution = {
        1: int(0.005 * num_employees),
        2: int(0.03 * num_employees),
        3: int(0.05 * num_employees),
        4: int(0.07 * num_employees),
        5: int(0.08 * num_employees),
        6: int(0.1 * num_employees),
        7: int(0.12 * num_employees),
        8: int(0.15 * num_employees),
        9: int(0.25 * num_employees),
    }
    remaining = num_employees - sum(band_distribution.values())
    band_distribution[10] = remaining

    band_generic_job_titles = {
        0: "CEO",
        1: "CXO",
        2: "Head of Department",
        3: "Director / Vice President",
        4: "Associate Director/AVP",
        5: "Senior Manager/Manager",
        6: "Team Lead",
        7: "Professional / SME",
        8: "Associate",
        9: "Coordinator, Specialist",
        10: "Assistant, Associate Assistant",
        11: "Trainee, Intern"
    }
    employees = []

    for i in range(num_employees):
        if i == 0:
            # Top-level CEO
            emp = Employee(
                emp_id=10000001,
                first_name=names.get_first_name(),
                last_name=names.get_last_name(),
                job_band=0,
                position_id=20000001,
                generic_job_title=band_generic_job_titles[0],
                manager_id=10000000,
                manager_position_id=20000000
            )
            employees.append(emp)
        else:
            # pick a band weighted by remaining slots
            band_choices = list(band_distribution.keys())
            weights = [band_distribution[b] for b in band_choices]
            band = random.choices(band_choices, weights)[0]
            band_distribution[band] -= 1

            emp = Employee(
                emp_id=10000001 + i,
                first_name=names.get_first_name(),
                last_name=names.get_last_name(),
                job_band=band,
                position_id=random.randint(20000002, 20000001 + num_employees),
                generic_job_title=band_generic_job_titles[band]
            )
            employees.append(emp)
    return employees

# Assign managers so each employee reports up the chain to the CEO
def assign_managers(employees):
    supervisors = {band: [] for band in range(0, 11)}
    for emp in employees:
        supervisors.setdefault(emp.job_band, []).append(emp)

    for emp in employees:
        if emp.job_band == 0:
            continue
        # look for possible managers in higher bands
        possible = []
        for b in range(emp.job_band):
            possible.extend(supervisors.get(b, []))
        # favor immediate band-up by higher weight
        weights = [0.95 if m.job_band == emp.job_band - 1 else 0.05 for m in possible]
        mgr = random.choices(possible, weights)[0]
        emp.manager_id = mgr.emp_id
        emp.manager_position_id = mgr.position_id

# Validate that all employees can trace up to the CEO
def check_org_chart(employees):
    def trace(emp, visited):
        if emp.manager_id == 10000000:
            return True
        if emp.emp_id in visited:
            return False
        visited.add(emp.emp_id)
        mgr = next((e for e in employees if e.emp_id == emp.manager_id), None)
        return trace(mgr, visited) if mgr else False

    return all(trace(emp, set()) for emp in employees)

# ------------ Streamlit App ------------
st.title("Org Hierarchy Generator")

num = st.number_input(
    "Number of Employees (max 20000)", min_value=1, max_value=20000, value=1000, step=1
)

if st.button("Generate Org Chart"):
    with st.spinner("Generating..."):
        try:
            emps = generate_employee_list(num)
            assign_managers(emps)
            if not check_org_chart(emps):
                st.error("Validation failed: some employees cannot trace up to the CEO.")
            else:
                # build a DataFrame
                records = []
                for e in emps:
                    if e.manager_id != 10000000:
                        m = next(x for x in emps if x.emp_id == e.manager_id)
                        m_name, m_band, m_pos = m.full_name, m.job_band, m.position_id
                    else:
                        m_name, m_band, m_pos = "Top Node", 0, 20000000
                    records.append({
                        "emp_id": e.emp_id,
                        "full_name": e.full_name,
                        "job_band": e.job_band,
                        "generic_job_title": e.generic_job_title,
                        "position_id": e.position_id,
                        "manager_id": e.manager_id,
                        "manager_full_name": m_name,
                        "manager_job_band": m_band,
                        "manager_position_id": m_pos
                    })
                df = pd.DataFrame(records)

                # convert to CSV in-memory
                csv_buffer = io.StringIO()
                df.to_csv(csv_buffer, index=False)

                st.success("Org chart ready for download!")
                st.download_button(
                    label="Download CSV",
                    data=csv_buffer.getvalue(),
                    file_name="org_chart.csv",
                    mime="text/csv"
                )
        except Exception as ex:
            st.error(f"Error: {ex}")
