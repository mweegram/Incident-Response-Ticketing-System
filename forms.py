from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, SelectField, IntegerField, DateTimeLocalField, PasswordField, TextAreaField
from wtforms.validators import DataRequired, NumberRange, Optional

#Creates the Create User form, validating specified data as required.
class CreateUser(FlaskForm):
    uname = StringField('Enter your desired username:',validators=[DataRequired()])
    pword = PasswordField('Enter a valid password:',validators=[DataRequired()])
    email = StringField('Enter a valid email address:',validators=[DataRequired()])
	#Creates an empty select field (values added dynamically at runtime), coerce takes the value and makes it an integer type. The select box takes a string to show user but returns a the database id potentially in string form, this makes sure its an integer
    queue = SelectField(u'Queue:', coerce=int)
    submit = SubmitField('Submit')

#Creates the Login form, validating specified data as required.
class Login(FlaskForm):
	uname = StringField('Enter your desired username:',validators=[DataRequired()])
	pword = PasswordField('Enter a valid password:',validators=[DataRequired()])
	submit = SubmitField('Submit')

#Creates the New Queue form, validating specified data as required. Used to create a new queue to the database.
class NewQueue(FlaskForm):
	name = StringField('Enter new queue\'s name:',validators=[DataRequired()])
	submit = SubmitField('Submit')

#Creates the New Ticket form, validating specified data as required. Used to created a new ticket in a speicfied queue.
class NewTicket(FlaskForm):
	name = StringField('Enter ticket name:',validators=[DataRequired()])
	content = StringField('Enter ticket information:',validators=[DataRequired()])
	queue = SelectField(u'Queue:', coerce=int)
	submit = SubmitField('Submit')

#Creates the New Comment form, validating specified data as required. Used to add a comment to specified ticket.
class NewComment(FlaskForm):
    comment = StringField('Enter Comment: ',validators=[DataRequired()])
    frameworkstep = SelectField(u'Incident Response Framework Step:', coerce=int)
    submit = SubmitField('Submit')

#Creates the New Key Info form, validating specified data as required. Used to add a piece of Key info to a ticket.
class NewKeyInfo(FlaskForm):
	value = StringField('Enter Key Info (IP etc): ',validators=[DataRequired()])
	tag = StringField('Enter Comment: ',validators=[DataRequired()])
	submit = SubmitField('Submit')

#Creates New Relationship form. Used to add a relationship between tickets.
class NewRelationship(FlaskForm):
	tid = IntegerField('Enter The ID of the Related Ticket: ',validators=[DataRequired(),NumberRange(min=0)])
	submit = SubmitField('Submit')

#Creates the Set Determination form. Used to complete a ticket, specifying the validity of the alert.
class SetDetermination(FlaskForm):
	determination = SelectField(u'Determination:', choices = [("True Positive"),("False Positive")])
	submit = SubmitField('Submit')

#Creates the Update Ticket form, validating specified data as required.
class UpdateTicket(FlaskForm):
	title = StringField('Ticket Title: ', validators=[DataRequired()])
	content = StringField('Ticket Description: ', validators=[DataRequired()])
	queue = SelectField('Ticket Queue: ', coerce=int)
	status = SelectField('Ticket Status: ',validators=[DataRequired()])
	submit = SubmitField('Submit')

#Creates the Change Queue form. Used for changing a user's primary queue
class ChangeQueue(FlaskForm):
	queue = SelectField(u'Queue:', coerce=int)
	submit = SubmitField('Submit')

#Creates the Update Comment form, validating specified data as required. Used to change the content of a comment.
class UpdateComment(FlaskForm):
	comment = StringField('Enter Updated Comment ',validators=[DataRequired()])
	submit = SubmitField()

#Creates the Update Key Info, validating specified data as required. Used to chage the data held in a piece of Key Information.
class UpdateKeyInfo(FlaskForm):
	infotype = StringField('Enter Updated Descriptor: ',validators=[DataRequired()])
	info = StringField('Enter Updated Info (IP,etc): ',validators=[DataRequired()])
	submit = SubmitField()

#Creates the Bulk Relation form which specifies a root ticket for others to be linked to.
class BulkRelationRoot(FlaskForm):
	root = IntegerField('Select a Root Ticket: ',validators=[DataRequired(),NumberRange(min=0)])
	submit = SubmitField()

#Create the Create Knowledge form which takes the values needed to make a new knowledge base entry
class CreateKnowledge(FlaskForm):
	title = StringField('Enter the title of the new knowledge mapping: ',validators=[DataRequired()])
	body = TextAreaField('Enter the description of the new knowledge mapping: ',validators=[DataRequired()])
	submit = SubmitField()

#Create the Update Knowledge form which is used to update a knowledge mapping
class UpdateKnowledge(FlaskForm):
	title = StringField('Enter the new title of the knowledge mapping: ',validators=[DataRequired()])
	body = TextAreaField('Enter the new description of the knowledge mapping: ',validators=[DataRequired()])
	submit = SubmitField()	

#Create the Create Guidance form which makes a new piece of guidance for a knowledge base entry
class CreateGuidance(FlaskForm):
	title = StringField('Enter the title of the new guidance: ',validators=[DataRequired()])
	body = TextAreaField('Enter the description of the new guidance: ',validators=[DataRequired()])
	submit = SubmitField()

#Create the form Update guidance which is used to update a knowledge base entry
class UpdateGuidance(FlaskForm):
	title = StringField('Enter the new title of the  guidance: ',validators=[DataRequired()])
	body = TextAreaField('Enter the new description of the  guidance: ',validators=[DataRequired()])
	submit = SubmitField()