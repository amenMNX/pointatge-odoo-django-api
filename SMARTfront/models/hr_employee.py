# -*- coding: utf-8 -*-
from odoo import models, fields

class HrEmployee(models.Model):
    _inherit = 'hr.employee'
    _description = 'Extension HR Employee pour SMARTfront'

    # Matricule unique pour identifier l'employé dans le pointage
    pin = fields.Char(
        string='pin',
        required=True,
        index=True,
        help='Identifiant unique utilisé pour la gestion des pointages'
    )


    django_id = fields.Integer(
        string='ID Django',
        help="ID de l'employé dans le backend Django"
    )
    # Fonction utilitaire pour afficher l’employé avec matricule
    def name_get(self):
        result = []
        for employee in self:
            name = f"{employee.name} [{employee.pin}]"
            result.append((employee.barcode, name))
        return result
