# -*- coding: utf-8 -*-

{
    'name': "Saúde Relatorio",

    'summary': """
    Departamento de Saúde
    """,

    'description': """
    Secretaria de Tecnologia da Informação e Comunicação
    """,

    'author': "STIC",
    'website': "http://www.tjpi.jus.br",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/openerp/addons/base/module/module_data.xml
    # for the full list
    'category': 'Medical',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['saude_atendimento','saude'],
    # always loaded
    'data': [
        #'security/ir.model.access.csv',
        # 'security/saude_atendimento_security.xml',
        'views/views.xml',
        'report/eps_custom_report.xml',
        'report/actions_report.xml',
        'views/paciente_views.xml',
        'data/email_eps_data.xml',
        'views/eps_report_wizard.xml',
        'data/cron.xml',
    ],
    # 'qweb': ['static/src/xml/template.xml'],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
    'installable': True,
    'application': True
}


