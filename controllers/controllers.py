# -*- coding: utf-8 -*-
import operator
from urllib2 import URLError

from odoo import http
from odoo.http import request


#class Saude(http.Controller):

    # @http.route('/saude/vinculo', type='json', auth="user")
    # def paciente_by_intranet(self, fields):
    #     field_name, field_value, found = extract_form_value(fields, 'field_name', 'field_value', 'found')
    #     # print field_name, field_value, found
    #     iws = request.env['tjpi.intranet_service']
    #     try:
    #         if field_name == 'matricula':
    #             vinculo = iws.vinculo_by_matricula(field_value)
    #         else:
    #             vinculo = iws.vinculo_by_cpf(field_value)
    #     except URLError:
    #         return {'error': 'Falha na rede!'}
    #     if vinculo is None:
    #         return {'error': 'Vinculo não encontrado'}
    #
    #     context = {'nome': vinculo.nome, 'found': 1, 'foto': vinculo.urlFoto}
    #
    #     if int(found) == 1:
    #         res_partner = request.env['res.partner']
    #         partner = res_partner.create_vinculo(vinculo)
    #         saude_paciente = request.env['saude.paciente']
    #         paciente_vals = {
    #             'partner_id': partner.id
    #         }
    #         paciente = saude_paciente.create(paciente_vals)
    #         context['paciente_id'] = paciente.id
    #
    #     return context
