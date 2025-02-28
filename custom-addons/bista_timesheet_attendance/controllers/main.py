from odoo import http
from odoo.http import request
import json

class AttendanceController(http.Controller):
    
    @http.route('/timesheet/location_check_in_out', type='json', auth='user')
    def location_check_in_out(self, type, latitude, longitude):
        user = request.env.user
        employee = user.employee_id

        if not employee:
            return {"error": "Employee record not found for this user."}

        task = request.env["project.task"].search([("user_id", "=", user.id)], limit=1)
        if not task:
            return {"error": "No active task found for check-in/out."}

        attendance_model = request.env["project.task.attendance"]
        vals = {
            "employee_id": employee.id,
            "task_id": task.id,
            "date": fields.Date.today(),
        }

        if type == "in":
            vals.update({
                "check_in_time": fields.Datetime.now(),
                "check_in_latitude": latitude,
                "check_in_longitude": longitude,
            })
        elif type == "out":
            attendance = attendance_model.search(
                [("employee_id", "=", employee.id), ("task_id", "=", task.id)],
                order="check_in_time desc", limit=1
            )
            if not attendance:
                return {"error": "No check-in record found for check-out."}

            attendance.write({
                "check_out_time": fields.Datetime.now(),
                "check_out_latitude": latitude,
                "check_out_longitude": longitude,
            })
            return {"message": "Check-out successful"}

        attendance_model.create(vals)
        return {"message": f"Check-{type} successful"}
