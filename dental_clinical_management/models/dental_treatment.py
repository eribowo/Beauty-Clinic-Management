from odoo import fields, models

class DentalTreatment(models.Model):
    """For adding Dental treatment details of the patients"""
    _name = 'dental.treatment'
    _description = "Dental Treatment"
    _inherit = ['mail.thread']

    name = fields.Char(string='Treatment Name', help="Date of the treatment")
    treatment_categ_id = fields.Many2one('treatment.category', string="Category", help="name of the treatment")
    cost = fields.Float(string='Cost', help="Cost of the Treatment")
    doctor_commission_percentage = fields.Float(string="Persentase Komisi Dokter (%)", help="Persentase komisi yang didapat dokter dari treatment ini")
