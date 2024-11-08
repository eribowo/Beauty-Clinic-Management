from odoo import fields, models

class DentalMedicine(models.Model):
    """For creating the medicines used in the dental clinic"""
    _inherit = 'product.template'

    is_medicine = fields.Boolean('Is Medicine',
                                 default=True,
                                 help="If the product is a Medicine")
    generic_name = fields.Char(string="Generic Name",
                               required=True,
                               help="Generic name of the medicament")
    dosage_strength = fields.Integer(string="Dosage Strength",
                                     required=True,
                                     help="Dosage strength of medicament")
    doctor_commission_percentage = fields.Float(string="Persentase Komisi Dokter (%)",
                                                help="Persentase komisi yang didapat dokter dari penjualan produk ini")
