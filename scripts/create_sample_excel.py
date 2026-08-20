from pathlib import Path

from openpyxl import Workbook

output = Path("examples/data/employees.xlsx")
output.parent.mkdir(parents=True, exist_ok=True)

wb = Workbook()
ws = wb.active
ws.title = "Employees"
ws.append(["EmployeeID", "Name", "Department", "Location"])
ws.append([101, "Raju", "Engineering", "Hyderabad"])
ws.append([102, "John", "Finance", "New York"])
ws.append([103, "Sarah", "HR", "London"])
ws.append([104, "Anil", "Engineering", "Bangalore"])

projects = wb.create_sheet("Projects")
projects.append(["ProjectID", "Project", "Status"])
projects.append([1, "RAG Engineering", "In Progress"])
projects.append([2, "Enterprise Data Platform", "Completed"])

wb.save(output)
print(f"Created: {output}")
