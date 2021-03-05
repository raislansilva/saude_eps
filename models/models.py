
# -*- coding: utf-8 -*-
from datetime import date, datetime
from jinja2 import Template
from itertools import groupby
import json
import dateutil
from psycopg2._psycopg import IntegrityError
from dateutil.relativedelta import relativedelta

from odoo import models, fields, api


class Absenteismo(models.Model):
    _name = 'saude_report.absenteismo'
    _order = 'year desc, frequencia desc'
    _sql_constraints = [
        ('cid_id_year_month_unique', 'UNIQUE(cid_id,year,month)', 'CID, year e month devem ser únicos.'),
    ]

    name = fields.Char('CID', related='cid_id.codigo', store=True)
    cid_id = fields.Many2one('saude.cid.categoria')
    month = fields.Char('Mês', size=2)
    year = fields.Char('Ano', size=4)
    frequencia = fields.Integer('Frequência')
    afastamento = fields.Integer('Dias de Afastamento', help='Quantidade de dias de afastamento')
    faixa = fields.Selection([
        ('1', 'Menos de 35 anos'), ('2', '36 a 45 anos'), ('3', '46 a 55 anos'),
        ('4', '56 a 65 anos'), ('5', 'Mais de 65 anos')
    ])
    atuacao = fields.Selection([('1', '1º Grau'), ('2', '2º Grau')], 'Atuação', size=1)
    atividade = fields.Selection([('direto', 'Judiciária'), ('indireto', 'Administrativa')], size=10)
    sexo = fields.Selection([('M', 'Masculino'), ('F', 'Feminino')], size=1)

    @api.model_cr
    def init(self):
        self.env.cr.execute("""
        SELECT 
        CASE 
            WHEN extract(year from age(partner.birthday)) <= 35 THEN '1'
            WHEN extract(year from age(partner.birthday)) BETWEEN 36 and 45 THEN '2'
            WHEN extract(year from age(partner.birthday)) BETWEEN 46 and 55 THEN '3'
            WHEN extract(year from age(partner.birthday)) BETWEEN 56 and 65 THEN '4'
            WHEN extract(year from age(partner.birthday)) >= 66 THEN '5' END AS faixa,
        subcategoria.categoria_id AS cid_id,
        CASE 
            WHEN partner.title = 3 THEN 'M'
            WHEN partner.title = 1 OR partner.title = 2 THEN 'F' END AS sexo1,
        SUM(atestado.dias) AS afastamento,
        COUNT(atestado.id) AS frequencia,
        date_part('month', consulta.create_date)::BIGINT AS month,
        date_part('year', consulta.create_date)::BIGINT AS year
        FROM saude_atendimento_atestado AS atestado 
            JOIN saude_atendimento_atestado_saude_cid_subcategoria_rel ON atestado.id = saude_atendimento_atestado_id
            JOIN saude_cid_subcategoria AS subcategoria ON subcategoria.id = saude_cid_subcategoria_id
            JOIN saude_atendimento_consulta AS consulta ON consulta.id = atestado.consulta_id 
            JOIN saude_paciente AS paciente ON paciente.id = consulta.paciente_id
            JOIN res_partner AS partner ON partner.id = paciente.partner_id
        GROUP BY 
            subcategoria.categoria_id, sexo1, faixa, month, year
        ORDER BY faixa, subcategoria.categoria_id;
         """)
        results = self.env.cr.dictfetchall()
        for line in results:

            record = self.search([
                ('cid_id', '=', line['cid_id']),
                ('year', '=', line['year']),
                ('month', '=', line['month'])])
            if record:
                record.write(line)
                # self.env.cr.commit()
            else:
                self.create(line)


class Paciente(models.Model):
    _name = 'saude_report.paciente'

    _sql_constraints = [
        ('cpf_unique', 'unique(cpf)', 'CPF é único')
    ]

    name = fields.Char('Nome', required=True)
    cpf = fields.Char('CPF', required=True)
    categoria = fields.Selection([
        ('SERVIDOR_CARREIRA', u'Carreira/Efetivo'), ('CARGO_COMISSIONADO', u'Comissionado'),
        ('MAGISTRADO', u'Magistrado'), ('CEDIDO', u'Cedido'), ('AUXILIAR_DA_JUSTICA', u'Auxiliar da Justiça')
    ], 'Categoria')
    cargo = fields.Char()
    email = fields.Char('Email')
    nascimento = fields.Date(required=True)
    posse = fields.Date()
    month_nasc = fields.Selection([(1, u'Janeiro'), (2, u'Fevereiro'), (3, u'Março'), (4, u'Abril'), (5, u'Maio'),
                                   (6, u'Junho'), (7, u'Julho'), (8, u'Agosto'), (9, u'Setembro'), (10, u'Outubro'),
                                  (11, u'Novembro'), (12, u'Dezembro')], 'Mês Nascimento', compute='_compute_month')
    ativo = fields.Boolean(dafault=True)
    documento_ids = fields.One2many('saude_report.documento', 'paciente_id', 'Requisições')
    local_id = fields.Many2one('saude_report.local_saude', "Lotação")

    @api.multi
    @api.depends('nascimento')
    def _compute_month(self):
        for record in self:
            if record.nascimento:
                dob = fields.Datetime.from_string(record.nascimento)
                record.month_nasc = dob.month

    @api.model
    def scheduled_importar_vinculo(self):
        _Transparencia = self.env['sei.transparencia_service']
        result = _Transparencia.call_method('servidor', {})
        # [u'APOSENTADO', u'MEDIADOR_JUDICIAL', u'ESTAGIARIO', u'PRESTADOR', u'CARGO_COMISSIONADO', u'MAGISTRADO',
        #  u'PENSIONISTA DE SERVIDOR', u'PENSIONISTA', u'CEDIDO', u'AUXILIAR_DA_JUSTICA', u'MAGISTRADO INATIVO',
        #  u'SERVIDOR INATIVO', u'SERVIDOR_CARREIRA', u'TERCEIRIZADO', u'PENSIONISTA DE MAGISTRADO', u'MILITAR']
        
        for vinculo in result:
            try:
                paciente = self.search([('cpf', '=', vinculo['cpf'])])
                pessoa = _Transparencia.vinculo_by_cpf(vinculo['cpf'])
                local = self.env['saude_report.local_saude'].search([('orgao_id','=',pessoa['orgao_id'])])
                
                vals = {
                    'name': vinculo['nome'],
                    'cpf': vinculo['cpf'],
                    'nascimento': vinculo['nascimentoData'],
                    'posse': vinculo['data_posse_efetivo'],
                    'email': vinculo['email'],
                    'categoria': vinculo['categoria'],
                    'cargo': vinculo['cargo_comissionado_descricao'] or vinculo['cargo_efetivo_descricao'] or vinculo['categoria'].replace('_', ' ').title(),
                    'local_id':local.id,
                }
                if paciente:
                    paciente.sudo().write(vals)
                    self._cr.commit()
                elif vinculo['categoria'] in ['SERVIDOR_CARREIRA', 'CARGO_COMISSIONADO', 'MAGISTRADO', 'CEDIDO', 'AUXILIAR_DA_JUSTICA']:
                    self.sudo().create(vals)
                    self._cr.commit()
            except Exception:
                self._cr.rollback()


# class Consulta(models.Model):
#     _name = 'saude_report.consulta'
#     _sql_constraints = [
#         ('unique_exercicio_paciente', 'unique(exercicio, paciente_id)', 'Paciente já realizou EPS'),
#     ]

#     name = fields.Char(u'Descrição')
#     data = fields.Date(default=fields.Date.context_today, required=True, translate=False)
#     exercicio = fields.Char(u'Exercício', size=4, default=lambda self: date.today().strftime('%Y'), required=True)
#     paciente_id = fields.Many2one('saude_report.paciente', 'Paciente')
#     diagnostico = fields.Char(u'Diagnóstico')


class Grupo(models.Model):
    _name = 'saude_report.grupo'
    _sql_constraints = [
        ('unique_exercicio_month', 'unique(exercicio, month)', 'Existe um documento associado.')
    ]

    name = fields.Char(u'Descrição', compute='_compute_grupo_fields')
    exercicio = fields.Char(u'Exercício', size=4, default=lambda self: date.today().strftime('%Y'), required=True)
    mes = fields.Selection([(1, u'Janeiro'), (2, u'Fevereiro'), (3, u'Março'), (4, u'Abril'), (5, u'Maio'),
                            (6, u'Junho'), (7, u'Julho'), (8, u'Agosto'), (9, u'Setembro'), (10, u'Outubro'),
                            (11, u'Novembro'), (12, u'Dezembro')], 'Més', required=True)
    ref = fields.Char('Referência')
    documento_ids = fields.One2many('saude_report.documento', 'grupo_id', 'Requisições')
    procedimento = fields.Char('N. do Processo', help=u'Número do processo no SEI')
    id_proc = fields.Char('ID do Processo')
    link_procedimento = fields.Char(compute='_compute_grupo_fields')
    external_link_procedimento = fields.Char()

    @api.multi
    def _compute_grupo_fields(self):
        _Sei = self.env['sei.service']
        for record in self:
            record.name = u'{}/{} {}'.format(record.exercicio, record.mes, record.ref or '')
            record.link_procedimento = _Sei.link_procedimento(record.id_proc)
    
    def _return_month_or_year(self,value,prox=0):
        if value == 'month':    
            if prox == 0:
                return datetime.today().month 
            else:
                return datetime.today().month == 12 and 1 or datetime.today().month+prox
        elif value == 'year':
            if prox == 0:
                return datetime.today().year
            else:
                return datetime.today().month == 12 and datetime.today().year+prox or datetime.today().year
                
    @api.model    
    def scheduled_action_send_email(self):
        _SWS = self.env['sei.service']
        documentos = self.env['saude_report.documento'].search(['|','&',('grupo_id.exercicio','=',self._return_month_or_year('year',0)),('grupo_id.mes','=',self._return_month_or_year('month',0)),
        '&',('grupo_id.exercicio','=',self._return_month_or_year('year',1)),('grupo_id.mes','=',self._return_month_or_year('month',1))])
        for doc in documentos:
            if doc.status_eps == u'unrealized':
                #consultar se o documento dessa requisição já foi assinado
                #doc_sei = _SWS.consultar_documento(1433813)
                if True:
                    if not doc.prazo_eps:
                        template_id = self.env.ref('saude_report.email_template_eps').id
                        template =  self.env['mail.template'].browse(template_id)
                        template.write({
                            'email_to': 'raislan6@gmail.com',
                            'email_from':'raislan@live.com',
                            'subject':'Requisição Para Realização dos Exames Periódicos de Saúde - EPS'
                        })
                        message_id = template.send_mail(self.id, force_send=True)
                        mail = self.env['mail.mail'].search([('id','=',message_id)])
                        if not mail or mail and mail.state == 'sent':
                            doc.write({
                                'prazo_eps': datetime.today().date()+relativedelta(days=60)
                            })
                            self._cr.commit()
                                
                                
    def template(self):
        return Template(
            u'''<html>
            <p> Convocação para Exames Periódicos de Saúde - EPS</p>
            <p style="text-indent: 10%">Com determinação pela <a href="http://transparencia.tjpi.jus.br/uploads/legislacao_lei/file/2054/Diario.pdf" target="_blank">Portaria (Presidência) Nº 1502/2019 - PJPI/TJPI/SECPRE</a>. Segue abaixo a lista de {{ categoria }} convocados para a realização dos Exames Periódicos de Saúde - EPS.</p>
            <br>
            <ul>
                {% for paciente in grupos_paciente %}
                    <li>{{paciente['name']}}</li>
                {% endfor %}
            </ul>
            </html>'''
        )
        
    def _check_doenca_cronica(self,cpf):
        paciente = self.env['saude.paciente'].search([('partner_id.cpf','=',cpf)])
        if paciente.portador_doenca_cronica:
            return True
        else:
            return False
        
    def _check_exame_pre_admissional(self,cpf):
        consultas = self.env['saude_atendimento.consulta'].search([('paciente_id.cpf','=',cpf)])#cid Z021 pré-admissional 
        if consultas:
            for consulta in consultas:
                for cid in consulta.diagnostico_ids:
                    if cid.codigo == 'Z021':
                        return True    
        else:
            return False
        
    def _local_exposto_risco(self, cpf):
        paciente = self.env['saude_report.paciente'].search([('cpf','=',cpf )])
        local_exposto_risco = self.env['saude_report.local_exposto_risco'].search([('local_id.orgao_id','=',paciente.local_id.orgao_id)])
        return len(local_exposto_risco)
    
    def _idade_prox_mes(self,nsc):
        num_months = (datetime.now().date().year - nsc.year) * 12 + (datetime.now().date().month - nsc.month)+1
        idade_month = num_months/12
        return idade_month
    
    def _meses_eps(self,consulta_eps):
        month_eps = 0
        if consulta_eps:
            ultima_consulta_eps = consulta_eps.sorted(key="data",reverse=True)[0]
            dt_ultima_consulta_eps = dateutil.parser.parse(ultima_consulta_eps.data).date()
            month_eps = (((datetime.now().date().year - dt_ultima_consulta_eps.year) * 12) + 
                         (datetime.now().date().month - dt_ultima_consulta_eps.month)+1)
        return month_eps
    
    def _criar_grupos(self,pessoa,paciente):
        if pessoa['grauJudicial'] ==  1:
            if pessoa['categoria'] == 'MAGISTRADO':
                paciente.update({"group": "magistrados1grau"})
                return paciente
            elif (pessoa['categoria'] == 'SERVIDOR_CARREIRA' or
                pessoa['categoria'] == 'CARGO_COMISSIONADO' or 
                pessoa['categoria'] == 'CEDIDO'  or 
                pessoa['categoria'] == 'AUXILIAR_DA_JUSTICA'):
                
                if pessoa['cidade_lotacao'] == "Teresina":
                    paciente.update({"group": "servidores1graucapital"})
                    return paciente
                else:
                    if pessoa['sexo'] == 'M':
                        paciente.update({"group": "servidores1grauinterior"})
                        return paciente
                    elif pessoa['sexo'] == 'F':
                        paciente.update({"group": "servidoras1grauinterior"})
                        return paciente    
        elif pessoa['grauJudicial'] ==  2:
            if pessoa['categoria'] == 'MAGISTRADO':
                paciente.update({"group": "magistrados2grau"})
                return paciente
            elif (pessoa['categoria'] == 'SERVIDOR_CARREIRA' or 
                pessoa['categoria'] == 'CARGO_COMISSIONADO' or
                pessoa['categoria'] == 'CEDIDO'  or
                pessoa['categoria'] == 'AUXILIAR_DA_JUSTICA'):
                
                paciente.update({"group": "servidores2grau"})
                return paciente
        
                


    def _grupos_habilitados_eps(self):
        _TS = self.env['sei.transparencia_service']
        query = self.env.cr.execute("""select *from saude_report_paciente where EXTRACT(MONTH FROM nascimento ) = 3 limit 8""")
        pacientes = self.env.cr.dictfetchall()
        grupos = []
        for paciente in pacientes:
            try:
                if paciente['nascimento']:
                    nsc = dateutil.parser.parse(paciente['nascimento']).date()
                    month = datetime.today().month == 12 and 1 or datetime.today().month+1
                    if nsc.month == month:
                        pessoa = _TS.vinculo_by_cpf(paciente['cpf'])
                        if pessoa:
                            if (dateutil.parser.parse(pessoa['dataInicio']).date().year != datetime.now().year or
                                not self._check_exame_pre_admissional(pessoa['cpf'])):
                                #consulta os magistrados e servidores habilitados para o eps do mês subsequente
                                consultas_eps = self.env['saude_atendimento.consulta'].search([('eps','=',True)])
                                consulta_eps = consultas_eps.filtered(lambda c: c.paciente_id.cpf == paciente['cpf'])
                                print self._meses_eps(consulta_eps) 
                                print paciente['name']
                                print "==========================================="                
                                if (self._idade_prox_mes(nsc) <= 45 and self._meses_eps(consulta_eps) >= 24 or 
                                    self._idade_prox_mes(nsc) > 45 and self._meses_eps(consulta_eps) >=12 or 
                                    self._local_exposto_risco(pessoa['cpf']) > 0 and self._meses_eps(consulta_eps) >=12 or 
                                    self._check_doenca_cronica(pessoa['cpf']) and self._meses_eps(consulta_eps) >=12 or 
                                    len(consulta_eps) == 0):
                                    
                                    grupos.append(self._criar_grupos(pessoa,paciente))
                                     
                                            
            except AttributeError as ex:
                print "----------- ERROR START ------------"
                print ex, r, nsc
                print "----------- ERROR END------------"

        return grupos

    def _gerar_requisicao(self, procedimento,unidade, group_id):
        _SWS = self.env['sei.service']
        
        orderna = lambda item:item['group']
        grupos = self._grupos_habilitados_eps()
        grupos.sort(key=orderna)
        pacientes_agrupados = groupby(grupos,orderna)

        for agrupamento, valores_agrupados in pacientes_agrupados:
            grupo_paciente=list()
            for value in valores_agrupados:
                grupo_paciente.append(value)
            
            grupo_string = json.dumps(grupo_paciente)
            #gerar documentos no sei agrupados por categorias    
            doc_sei = _SWS.incluir_documento(procedimento, unidade, 
                                    self.template().render({'grupos_paciente':json.loads(grupo_string),
                                        'categoria':self._retorna_grupo(grupo_paciente[0]['group']) }).encode('utf8'), '295')
            
            ## gerar requisições(documentos)-eps
            for grupo in grupo_paciente:
                paciente = self.env['saude_report.paciente'].search([('cpf','=',grupo['cpf'])])
                documento = self.env['saude_report.documento']
                documento.create({
                    'id_documento': doc_sei.DocumentoFormatado,
                    'paciente_id': paciente.id,
                    'grupo_id':group_id
                })
                


    def _retorna_grupo(self,grupo):
        if grupo == 'magistrados1grau':
            return 'Magistrados de 1.º'.decode("utf8")
        elif grupo == 'servidores1graucapital':
            return 'Servidores 1.ª Grau Capital'.decode("utf8")
        elif grupo == 'servidores1grauinterior':
            return 'Servidores 1.ª Grau Interior'.decode("utf8")
        elif grupo == 'servidoras1grauinterior':
            return 'Servidoras 1.ª Grau Interior'.decode("utf8")
        elif grupo == 'magistrados2grau':
            return 'Magistrados de 2.º'.decode("utf8")      
        elif grupo == 'servidores2grau':
            return 'Servidores 2.º Grau'.decode("utf8")
    
    
    def criar_procedimento_requisicao(self):
        unidade = '110001744'
        month = datetime.today().month == 12 and 1 or datetime.today().month+1
        year = datetime.today().month == 12 and datetime.today().year+1 or datetime.today().year
        vals = {
            'id_proc': '',
            'procedimento': '',
            'external_link_procedimento':'',
            'mes':month,
            'exercicio':year
        }
        grupo = self.create(vals)
        self._gerar_requisicao(grupo.procedimento,unidade, grupo.id)
        

    @api.model
    def create(self, vals):
        unidade = '110001744'
        tipo_procedimento = '100000190'
        especificacao = u'Requisição para realização de Exame Periódico de Saúde - EPS'
        assuntos = [{u'CodigoEstruturado': u'02.21.13', u'Descricao': u'Guia para consulta / exame laboratorial'}]
        _Sei = self.env['sei.service']  # :type _Sei : int
        base_procedimento = _Sei.criar_procedimento(tipo_procedimento, especificacao, assuntos)

        procedimento = _Sei.gerar_procedimento(unidade, base_procedimento)
        if procedimento and procedimento['IdProcedimento']:
            vals['id_proc'] = procedimento['IdProcedimento']
            vals['procedimento'] = procedimento['ProcedimentoFormatado']
            vals['external_link_procedimento'] = procedimento['LinkAcesso']
            return super(Grupo, self).create(vals)
        else:
            raise models.ValidationError('Error ao tentar criar o procedimento no SEI.')
        

class Documento(models.Model):
    _name = 'saude_report.documento'
    _sql_constraints = [
        ('unique_paciente_id_grupo_id', 'unique(paciente_id,grupo_id)', 'Existe um documento associado.')
    ]
    _rec_name="paciente_id"
    

    name = fields.Char('Nome')
    documento = fields.Char('Número do documento')
    id_documento = fields.Char('ID Documento')
    paciente_id = fields.Many2one('saude_report.paciente', 'Paciente')
    grupo_id = fields.Many2one('saude_report.grupo', 'Grupo')
    status_eps = fields.Selection([
        ('accomplished', 'Realizado'),
        ('unrealized', 'Não Realizado'),
        ('justfied', 'Recusa')],'Status do EPS', default="unrealized")
    justificativa = fields.Html("Motivo da Recusa")
    prazo_eps = fields.Date("Prazo EPS")
    
        

class Consulta(models.Model):
    _inherit = 'saude_atendimento.consulta'     
    
    paciente_report = fields.Many2one('saude_report.paciente', string="Paciente Report")
    requisicoes_ids = fields.One2many(related="paciente_report.documento_ids",string="Requisições EPS")


    @api.model
    def create(self,vals):
        paciente = self.env['saude.paciente'].search([('id','=',vals.get('paciente_id'))])
        paciente_report = self.env['saude_report.paciente'].search([('cpf','=',paciente.cpf)])
        consulta = super(Consulta, self).create(vals) 
        consulta.write({'paciente_report':paciente_report.id})
        return consulta
    
    @api.multi
    def write(self,vals):
        paciente_report = self.env['saude_report.paciente'].search([('cpf','=',self.paciente_id.cpf)])
        vals['paciente_report'] = paciente_report.id
        return super(Consulta, self).write(vals)
    
    
    
class PacienteSaude(models.Model):
    _inherit = 'saude.paciente'     
    
    portador_doenca_cronica = fields.Boolean("Portador de Doença Crônica")
    
    
class LocalExpostoRisco(models.Model):
    _name = 'saude_report.local_exposto_risco'  
    _rec_name="local_id"
    
    #local = fields.Char("Local")
    local_id = fields.Many2one('saude_report.local_saude','Local exposto a risco')
    #paciente_ids = fields.One2many('local.saude', 'local_id', 'Pacientes')