from odoo import models, fields

class HrPointage(models.Model):
    _name = 'hr.pointage'
    _description = 'Pointage Employé'

    employee_id = fields.Many2one('hr.employee', required=True)
    date = fields.Date(required=True)
    check_in = fields.Datetime()
    check_out = fields.Datetime()
    heures_sup = fields.Float()
    absence_payee = fields.Boolean(default=False)
    state = fields.Selection([
        ('draft', 'Brouillon'),
        ('validated', 'Validé RH')
    ], default='draft')
