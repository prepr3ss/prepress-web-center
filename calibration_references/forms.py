from flask_wtf import FlaskForm
from wtforms import (
    StringField, SelectField, DecimalField, SubmitField, 
    HiddenField, ValidationError
)
from wtforms.validators import (
    DataRequired, Length, NumberRange, Optional
)
from models import CalibrationReference

class CalibrationReferenceForm(FlaskForm):
    """Form for creating and editing calibration references"""
    
    # Hidden field for ID (used in edit mode)
    id = HiddenField()
    
    # Basic Information
    print_machine = SelectField(
        'Print Machine*', 
        choices=[
            ('SM2', 'SM2'),
            ('SM3', 'SM3'), 
            ('SM4', 'SM4'),
            ('SM5', 'SM5'),
            ('SM6', 'SM6'),
            ('VLF', 'VLF')
        ],
        validators=[DataRequired(message="Print machine is required")]
    )
    
    calib_group = StringField(
        'Calibration Group*', 
        validators=[
            DataRequired(message="Calibration group is required"),
            Length(max=100, message="Group name must be less than 100 characters")
        ]
    )
    
    calib_code = StringField(
        'Calibration Code*', 
        validators=[
            DataRequired(message="Calibration code is required"),
            Length(max=100, message="Code must be less than 100 characters")
        ]
    )
    
    calib_name = StringField(
        'Calibration Name*',
        validators=[
            DataRequired(message="Calibration name is required"),
            Length(max=255, message="Name must be less than 255 characters")
        ]
    )
    
    # Additional Filter Fields
    paper_type = StringField(
        'Paper Type',
        validators=[
            Optional(),
            Length(max=100, message="Paper type must be less than 100 characters")
        ]
    )
    
    ink_type = StringField(
        'Ink Type',
        validators=[
            Optional(),
            Length(max=100, message="Ink type must be less than 100 characters")
        ]
    )
    
    calib_standard = SelectField(
        'Calibration Standard*',
        choices=[
            ('G7', 'G7 - GRACoL 7'),
            ('ISO', 'ISO - ISO Standard'),
            ('NESTLE', 'NESTLE - Nestle Standard'),
            ('GMI', 'GMI - GMI Standard'),
            ('EXISTING', 'EXISTING - Existing Standard')
        ],
        validators=[Optional()]  # Made optional for standard-specific forms
    )
    
    # Cyan Values
    c20 = DecimalField(
        'Cyan 20%', 
        places=2, 
        validators=[
            Optional(),
            NumberRange(min=0, max=100, message="Value must be between 0 and 100")
        ]
    )
    c25 = DecimalField('Cyan 25%', places=2, validators=[Optional(), NumberRange(min=0, max=100)])
    c40 = DecimalField('Cyan 40%', places=2, validators=[Optional(), NumberRange(min=0, max=100)])
    c50 = DecimalField('Cyan 50%', places=2, validators=[Optional(), NumberRange(min=0, max=100)])
    c75 = DecimalField('Cyan 75%', places=2, validators=[Optional(), NumberRange(min=0, max=100)])
    c80 = DecimalField('Cyan 80%', places=2, validators=[Optional(), NumberRange(min=0, max=100)])
    
    # Magenta Values
    m20 = DecimalField('Magenta 20%', places=2, validators=[Optional(), NumberRange(min=0, max=100)])
    m25 = DecimalField('Magenta 25%', places=2, validators=[Optional(), NumberRange(min=0, max=100)])
    m40 = DecimalField('Magenta 40%', places=2, validators=[Optional(), NumberRange(min=0, max=100)])
    m50 = DecimalField('Magenta 50%', places=2, validators=[Optional(), NumberRange(min=0, max=100)])
    m75 = DecimalField('Magenta 75%', places=2, validators=[Optional(), NumberRange(min=0, max=100)])
    m80 = DecimalField('Magenta 80%', places=2, validators=[Optional(), NumberRange(min=0, max=100)])
    
    # Yellow Values
    y20 = DecimalField('Yellow 20%', places=2, validators=[Optional(), NumberRange(min=0, max=100)])
    y25 = DecimalField('Yellow 25%', places=2, validators=[Optional(), NumberRange(min=0, max=100)])
    y40 = DecimalField('Yellow 40%', places=2, validators=[Optional(), NumberRange(min=0, max=100)])
    y50 = DecimalField('Yellow 50%', places=2, validators=[Optional(), NumberRange(min=0, max=100)])
    y75 = DecimalField('Yellow 75%', places=2, validators=[Optional(), NumberRange(min=0, max=100)])
    y80 = DecimalField('Yellow 80%', places=2, validators=[Optional(), NumberRange(min=0, max=100)])
    
    # Black Values
    k20 = DecimalField('Black 20%', places=2, validators=[Optional(), NumberRange(min=0, max=100)])
    k25 = DecimalField('Black 25%', places=2, validators=[Optional(), NumberRange(min=0, max=100)])
    k40 = DecimalField('Black 40%', places=2, validators=[Optional(), NumberRange(min=0, max=100)])
    k50 = DecimalField('Black 50%', places=2, validators=[Optional(), NumberRange(min=0, max=100)])
    k75 = DecimalField('Black 75%', places=2, validators=[Optional(), NumberRange(min=0, max=100)])
    k80 = DecimalField('Black 80%', places=2, validators=[Optional(), NumberRange(min=0, max=100)])
    
    submit = SubmitField('Save Calibration Reference')
    
    def validate_calib_name(self, field):
        """Validate that calibration name is unique"""
        if field.data:
            existing = CalibrationReference.query.filter_by(calib_name=field.data).first()
            if existing and (not self.id.data or existing.id != int(self.id.data)):
                raise ValidationError('Calibration name must be unique')