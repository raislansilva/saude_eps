from odoo import models, fields, api
from datetime import datetime



class EpsReportWizard(models.TransientModel):
    _name = 'eps_report.wizard'

    date_start = fields.Date(string="Data Inicial", required=True, default=fields.Date.today)
    date_end = fields.Date(string="Data Final", required=True, default=fields.Date.today)
    grupo_id = fields.Many2one('saude_report.grupo', 'Grupo')
    
    @api.multi
    def print_report(self):
        data = {
            'ids': self.ids,
            'model': self._name,
            'form': {
                'date_start': self.date_start,
                'date_end': self.date_end,
            }
        }
        
        return self.env['report'].get_action(self, 'saude_report.eps_custom_pdf_report', data=data)
        

    
class ReportEps(models.AbstractModel):
    """Abstract Model for report template.
    """
    _name = 'report.saude_report.eps_custom_pdf_report'
    
    @api.model
    def render_html(self, docids, data=None):
        params = self.env['eps_report.wizard'].search([('id','=',docids[0])])
        # date_start = params.date_start
        # date_end = params.date_end
        
        dt = datetime.now().date()
        docs = self.env['saude_report.documento'].search(['&','&',('prazo_eps','<',datetime.strftime(dt,'%Y-%m-%d')),('status_eps','=','unrealized'),('grupo_id','=',params.grupo_id.id)])
          
        docargs = {
            'doc_ids': self.ids,
            'doc_model': self._name,
            'docs': docs,
        }
        
        return self.env['report'].render('saude_report.eps_custom_pdf_report', docargs)