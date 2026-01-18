# -*- coding: utf-8 -*-
{
    'name': "SMARTfront",
    'summary': "SMARTfront – Réception de pointages depuis Django",
    'description': """
        Module Odoo SMARTfront passif pour recevoir les pointages IN/OUT,
        stocker les heures sup et absences payées, et permettre la validation RH.
        Toute la logique de calcul est effectuée côté Django.
    """,
    'author': "DAKOTA",
    'category': 'Human Resources/Employee',
    'version': '1.0',
    'license': 'LGPL-3',
    'depends': ['base', 'hr', 'website', 'web', 'web_editor'],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'views/hr_employee_views.xml',
        'views/page_dg_template.xml',
        'views/page_employe_template.xml',
        'views/templates.xml',
        'data/menu.xml',
    ],
    
    'installable': True,
    'application': True,
    'auto-install': False,
}
