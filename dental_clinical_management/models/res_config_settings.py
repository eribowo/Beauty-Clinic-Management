from odoo import models, fields

class CommissionSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    default_doctor_commission_percentage = fields.Float(
        string="Persentase Komisi Dokter Default (%)", 
        config_parameter='default_doctor_commission_percentage', 
        help="Persentase komisi default yang didapat dokter dari penjualan produk dan treatment jika tidak ditentukan secara spesifik"
    )
