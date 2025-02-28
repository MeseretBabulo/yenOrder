from odoo import http, fields
from odoo.http import request
from odoo.addons.portal.controllers.portal import CustomerPortal
from odoo.http import content_disposition, Controller, request, route
from datetime import datetime
import pytz
import logging

_logger = logging.getLogger(__name__)

class CustomerPortal(CustomerPortal):

    def _prepare_portal_layout_values(self):
        values = super()._prepare_portal_layout_values()
        user = request.env.user
        eth_tz = pytz.timezone('Africa/Addis_Ababa')
        utc_tz = pytz.UTC

        # Check if user is linked to an employee
        employee = request.env['hr.employee'].sudo().search([
            '|',
            ('user_id', '=', user.id),
            ('work_email', '=', user.email)
        ], limit=1)

        if employee:
            last_attendance = request.env['hr.attendance'].sudo().search([
                ('employee_id', '=', employee.id)
            ], limit=1, order='check_in desc')
            
            if last_attendance and last_attendance.check_in:
                # Convert UTC to Ethiopian time
                if not last_attendance.check_in.tzinfo:
                    check_in_utc = utc_tz.localize(last_attendance.check_in)
                else:
                    check_in_utc = last_attendance.check_in
                
                # Convert to Ethiopian time
                check_in_eth = check_in_utc.astimezone(eth_tz)
                values['check_in_time'] = check_in_eth
            
            values.update({
                'is_employee': True,
                'employee': employee,
                'last_attendance': last_attendance,
                'check_in_status': bool(last_attendance and not last_attendance.check_out)
            })
            _logger.info("Employee found: %s, Last attendance: %s", employee.name, last_attendance)
        else:
            values.update({
                'is_employee': False,
                'employee': False,
                'last_attendance': False,
                'check_in_status': False
            })
            _logger.info("No employee found for user: %s", user.name)
        
        return values

    @http.route(['/my/attendance'], type='http', auth="user", website=True)
    def portal_attendance(self, **kw):
        values = self._prepare_portal_layout_values()
        user = request.env.user
        
        # Check if user is linked to an employee
        employee = request.env['hr.employee'].sudo().search([
            '|',
            ('user_id', '=', user.id),
            ('work_email', '=', user.email)
        ], limit=1)

        if employee:
            # Get last attendance
            last_attendance = request.env['hr.attendance'].sudo().search([
                ('employee_id', '=', employee.id)
            ], limit=1, order='check_in desc')

            # Get today's attendance records
            today_start = fields.Datetime.now().replace(hour=0, minute=0, second=0)
            today_attendances = request.env['hr.attendance'].sudo().search([
                ('employee_id', '=', employee.id),
                ('check_in', '>=', today_start)
            ], order='check_in desc')

            values.update({
                'user': user,
                'is_employee': True,
                'employee': employee,
                'last_attendance': last_attendance,
                'today_attendances': today_attendances,
                'page_name': 'attendance',
                'check_in_status': bool(last_attendance and not last_attendance.check_out)
            })
            _logger.info("Portal attendance values for employee %s: %s", employee.name, values)
        else:
            values.update({
                'user': user,
                'is_employee': False,
                'employee': False,
                'last_attendance': False,
                'today_attendances': False,
                'page_name': 'attendance',
                'check_in_status': False
            })
            _logger.info("No employee found for portal user: %s", user.name)

        return request.render("portal_attendance.portal_attendance_page", values)

    @http.route('/my/attendance/check', type='json', auth='user', website=True)
    def attendance_check(self, **kwargs):
        user = request.env.user
        employee = request.env['hr.employee'].sudo().search([
            '|',
            ('user_id', '=', user.id),
            ('work_email', '=', user.email)
        ], limit=1)

        if not employee:
            return {'success': False, 'error': 'No employee found for your user account'}

        try:
            # Get the last attendance record
            last_attendance = request.env['hr.attendance'].sudo().search([
                ('employee_id', '=', employee.id)
            ], limit=1, order='check_in desc')

            # Get location data
            latitude = kwargs.get('latitude')
            longitude = kwargs.get('longitude')
            
            # Convert to float and validate coordinates
            if latitude and longitude:
                try:
                    latitude = round(float(latitude), 6)
                    longitude = round(float(longitude), 6)
                    if not (-90 <= latitude <= 90 and -180 <= longitude <= 180):
                        return {'success': False, 'error': 'Invalid coordinates range'}
                except ValueError:
                    return {'success': False, 'error': 'Invalid location data format'}
            else:
                return {'success': False, 'error': 'Location data is required'}

            # Get device and network information
            user_agent = request.httprequest.user_agent
            device_info = {
                'browser': user_agent.browser,
                'platform': user_agent.platform,
                'device': user_agent.platform + ' - ' + user_agent.browser
            }
            
            # Get IP address
            ip_address = request.httprequest.remote_addr
            
            # Get location name using reverse geocoding
            attendance_obj = request.env['hr.attendance'].sudo()
            location_name = attendance_obj._get_location_name(latitude, longitude)

            # Convert current time to Ethiopian timezone
            eth_tz = pytz.timezone('Africa/Addis_Ababa')
            current_time = fields.Datetime.now()
            current_time_eth = pytz.UTC.localize(current_time).astimezone(eth_tz)
            # Convert back to naive datetime for storage
            current_time_naive = current_time_eth.replace(tzinfo=None)

            if not last_attendance or last_attendance.check_out:
                # Create check-in with location data
                vals = {
                    'employee_id': employee.id,
                    'check_in': current_time_naive,
                    'latitude': latitude,
                    'longitude': longitude,
                    'location_name': location_name,
                    'check_in_mode': 'portal',
                    'device_info': f"Device: {device_info['device']}\nBrowser: {device_info['browser']}\nPlatform: {device_info['platform']}",
                    'ip_address': ip_address,
                    'browser_info': user_agent.browser
                }
                attendance = attendance_obj.create(vals)
                action = 'check_in'
                _logger.info("Created check-in for employee %s at location %s (lat: %s, lng: %s)", 
                            employee.name, location_name, latitude, longitude)
            else:
                # Update check-out with location data
                vals = {
                    'check_out': current_time_naive,
                    'latitude': latitude,
                    'longitude': longitude,
                    'location_name': location_name,
                    'check_out_mode': 'portal',
                    'device_info': f"Device: {device_info['device']}\nBrowser: {device_info['browser']}\nPlatform: {device_info['platform']}",
                    'ip_address': ip_address,
                    'browser_info': user_agent.browser
                }
                last_attendance.write(vals)
                action = 'check_out'
                _logger.info("Created check-out for employee %s at location %s (lat: %s, lng: %s)", 
                            employee.name, location_name, latitude, longitude)

            return {
                'success': True,
                'action': action,
                'latitude': latitude,
                'longitude': longitude,
                'location_name': location_name,
                'device_info': device_info,
                'ip_address': ip_address
            }
        except Exception as e:
            _logger.error("Attendance error for employee %s: %s", employee.name, str(e))
            return {'success': False, 'error': str(e)}

    @http.route('/hr_attendance/attendance_user_data', type='json', auth='user')
    def attendance_user_data(self):
        _logger.info("attendance user data")
        employee = request.env['hr.employee'].sudo().search([('user_id', '=', request.env.user.id)], limit=1)
        if not employee:
            return {'error': 'No employee found'}

        last_attendance = request.env['hr.attendance'].sudo().search([
            ('employee_id', '=', employee.id),
        ], limit=1, order='check_in desc')

        # Calculate hours
        worked_hours = 0
        if last_attendance:
            if last_attendance.check_out:
                worked_hours = last_attendance.worked_hours
            else:
                worked_hours = (fields.Datetime.now() - last_attendance.check_in).total_seconds() / 3600.0

        return {
            'id': employee.id,
            'hours_today': worked_hours,
            'hours_previously_today': 0.0,
            'last_attendance_worked_hours': worked_hours if last_attendance and last_attendance.check_out else False,
            'last_check_in': fields.Datetime.to_string(last_attendance.check_in) if last_attendance else False,
            'attendance_state': 'checked_in' if last_attendance and not last_attendance.check_out else 'checked_out',
            'display_systray': True
        }

    @http.route('/hr_attendance/systray_check_in_out', type='json', auth='user')
    def systray_check_in_out(self, latitude=False, longitude=False):
        _logger.info("check in out")
        employee = request.env['hr.employee'].sudo().search([('user_id', '=', request.env.user.id)], limit=1)
        if not employee:
            return {'warning': 'No employee found'}

        attendance = request.env['hr.attendance'].sudo()
        last_attendance = attendance.search([
            ('employee_id', '=', employee.id),
            ('check_out', '=', False),
        ], limit=1)

        try:
            eth_tz = pytz.timezone('Africa/Addis_Ababa')
            current_time = fields.Datetime.now()
            current_time_eth = pytz.UTC.localize(current_time).astimezone(eth_tz)
            # Convert back to naive datetime for storage
            current_time_naive = current_time_eth.replace(tzinfo=None)

            if last_attendance:  # Check OUT
                last_attendance.write({
                    'check_out': current_time_naive,
                    'check_out_latitude': latitude,
                    'check_out_longitude': longitude,
                })
                return {
                    'action': 'check_out',
                    'message': 'Successfully checked out',
                    'worked_hours': last_attendance.worked_hours,
                }
            else:  # Check IN
                new_attendance = attendance.create({
                    'employee_id': employee.id,
                    'check_in': current_time_naive,
                    'check_in_latitude': latitude,
                    'check_in_longitude': longitude,
                })
                return {
                    'action': 'check_in',
                    'message': 'Successfully checked in',
                    'check_in_time': fields.Datetime.to_string(new_attendance.check_in)
                }
        except Exception as e:
            _logger.error('Attendance error: %s', str(e))
            return {'warning': str(e)}