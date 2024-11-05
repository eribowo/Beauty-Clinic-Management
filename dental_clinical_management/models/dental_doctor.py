from odoo import api, fields, models

class DentalDoctor(models.Model):
    """To add the doctors of the clinic"""
    _inherit = 'hr.employee'

    role_type = fields.Selection([
        ('doctor', 'Doctor'),
        ('beautician', 'Beautician'),
        ('employee', 'Employee')
    ], string="Role Type", required=True, help="Select role type: Doctor, Beautician or Employee")
    
    job_position = fields.Char(string="Designation",
                               help="To add the job position of the doctor or beautician")
    specialised_in_id = fields.Many2one('dental.specialist',
                                        string='Specialised In',
                                        help="Add the doctor specialised")
    dob = fields.Date(string="Date of Birth",
                      required=True,
                      help="DOB of the patient")
    doctor_age = fields.Integer(compute='_compute_doctor_age',
                                store=True,
                                string="Age",
                                help="Age of the patient")
    sex = fields.Selection([('male', 'Male'),
                            ('female', 'Female')],
                           string="Sex",
                           help="Sex of the patient")
    time_shift_ids = fields.Many2many('dental.time.shift',
                                      string="Time Shift",
                                      help="Time shift of the doctor")

    def unlink(self):
        """Delete the corresponding user from res.users while
        deleting the doctor"""
        for record in self:
            self.env['res.users'].search([('id', '=', record.user_id.id)]).unlink()
        res = super(DentalDoctor, self).unlink()
        return res

    @api.depends('dob')
    def _compute_doctor_age(self):
        """To calculate the age of the doctor from the DOB"""
        for record in self:
            record.doctor_age = (fields.date.today().year - record.dob.year -
                                  ((fields.date.today().month,
                                    fields.date.today().day) <
                                   (record.dob.month,
                                    record.dob.day))) if record.dob else False
