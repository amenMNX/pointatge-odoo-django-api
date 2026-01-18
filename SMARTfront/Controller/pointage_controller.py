from odoo import http
from odoo.http import request

class PointageController(http.Controller):

    @http.route('/api/odoo/pointage', type='json', auth='none', csrf=False, methods=['POST'])
    def receive_pointage(self, **kwargs):
        api_key = kwargs.get('api_key')
        expected_key = request.env['ir.config_parameter'].sudo().get_param('smartfront.api_key')
        if api_key != expected_key:
            return {'status': 'error', 'message': 'Invalid API Key'}

        pin = kwargs.get('pin')
        employee = request.env['hr.employee'].sudo().search([('pin','=',pin)], limit=1)
        if not employee:
            return {'status':'error','message':'Employee not found'}

        pointage = request.env['hr.pointage'].sudo().create({
            'employee_id': employee.barcode,
            'date': kwargs.get('date'),
            'check_in': kwargs.get('check_in'),
            'check_out': kwargs.get('check_out'),
            'heures_sup': kwargs.get('heures_sup',0),
            'absence_payee': kwargs.get('absence_payee',False),
        })
        return {'status':'success','id':pointage.id}
