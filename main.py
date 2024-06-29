from flask_wtf.csrf import CSRFProtect
from flask import Flask, render_template,redirect,session,request
from forms import *
import datetime
import database_methods
from flask_bootstrap import Bootstrap


#Initial the flask application, this what stores and recognises the API endpoints
app = Flask(__name__)
#Initialise Bootstrap used to help style forms.
Bootstrap(app)
#Session key used to sign session cookies, security feature to prevent cookie tampering.
app.config['SECRET_KEY'] = 'CHANGEME'
#Cross Site Request Forgery protection, declaration and initialisation. Helps prevents malicious attacks through form submission.
csrf = CSRFProtect(app)
csrf.init_app(app)

#Generate the databases if they don't already exist, if they do it will do nothing.
database_methods.table_init()

#Uses a check for a username set in the session variables, this indicates a successful login.
#Renders the homepage of the site
@app.route('/')
def home():
	if('username' in session):
		#fetch the busiest queues (max 3) to show on the home page stats
		busiest_queues = database_methods.get_busiest_queues()
		#fetch stats about the ticketing system (False Pos%, Total Tickets, Average Response time)
		stats = database_methods.get_frontpage_stats()
		#render_template takes data and passes it to HTML which can use the data to populate the template
		return render_template("Home.html",busy=busiest_queues,stats=stats)
	#If not logged in, send user to login.
	else:
		return redirect('/Login')

#Endpoint for use creation.
@app.route('/Create',methods=['POST','GET'])
def create_user():
	#initialise a database connection
	db,cur = database_methods.db_connection()
	#Create a the form in memory, ready to be passed into the template.
	form = CreateUser()
	#dynamically generates a selection of all queues available to select as primary queue
	form.queue.choices = [(queue[0], queue[1]) for queue in cur.execute('SELECT id, name FROM queue').fetchall()]
	#initialise message, used to pass information to show the user, should the form fail.
	message=""
	#if form validates (passes any validators, see forms.py to see validators)
	if form.validate_on_submit():
		#if a user doesn't already exist with that username
		if(database_methods.insert_user(form.uname.data,form.pword.data,form.email.data,form.queue.data)):
			return redirect('/')
		else:
			message = "User with this name already exists!"
	
	#render template, populate it with the form and a message, should one be needed.
	return render_template('Create.html',form=form, message=message)

#Creates the login endpoint
@app.route('/Login',methods=['POST','GET'])
def login():
	if not ('username' in session):
		#Initialise the login form
		form = Login()
		message=""
		if form.validate_on_submit():
			#check for a valid password match for the username provided
			if(database_methods.check_login(form.uname.data,form.pword.data)):
				#If password check is successful, add username to session and set logged in session variable
				session['username'] = form.uname.data
				session['loggedin'] = True
				return redirect('/')
			#Otherwise let the user know their submission was wrong.
			else:
				message="Username/Password Combo Incorrect!"
		
		#render the Log in page
		return render_template('LogIn.html',form=form,message=message)
	else:
		return redirect('/Profile')

#Api Endpoint for logging the user out
@app.route('/Logout')
def logout():
	#if user has previously successfully logged in
	if ('username' in session):
		#remove username from session
		del session['username'] 
		#unset the loggedin variable
		session['loggedin'] = False
	
	#redirect to home, which will redirect them to login again
	return redirect('/')

#API endpoint for creating a new ticket.
@app.route('/NewTicket',methods=['POST','GET'])
def create_new_ticket():
	if('username' in session):
		db,cur = database_methods.db_connection()
		#Get the user's id from the username stored in the session variable
		user = database_methods.user_id_from_name(session['username'])
		#initialise the New Ticket form
		form = NewTicket()
		#Dynamically generate the choices for a queue list, providing all options available
		form.queue.choices = [(queue[0], queue[1]) for queue in cur.execute('SELECT id, name FROM queue').fetchall()]
		if form.validate_on_submit():
			#Generate a new ticket, since this is a manually created ticket, the creator is assinged as the owner, status starts as under investigation and started time is the minute its created.
			database_methods.insert_ticket(form.name.data,form.queue.data,form.content.data,user,datetime.datetime.now())
			#Redirects to the queue that the ticket was created in.
			return redirect(f'/ViewQueue/{form.queue.data}')
		else:
			#renders the template, passing in the form initialised earlier.
			return render_template('CreateTicket.html',form=form)
	else:
		return redirect('/')

#API endpoint for creating a new queue
@app.route('/NewQueue',methods=['POST','GET'])
def create_new_queue():
	if('username' in session):
		#Initialise the New Queue form
		form = NewQueue()
		#initialise message, in case of an error to make the user aware of.
		message=""
		if form.validate_on_submit():
			#if queue insert succeeds.
			if(database_methods.insert_queue(form.name.data)):
				#show the list of all queues
				return redirect('/Queues')
			else:
				message="Queue Already Exists!"
		#render template, passing in the form and the message should one be set.
		return render_template('CreateQueue.html',form=form,message=message)
	else:
		return redirect('/')

#API endpoint for creating a new comment
@app.route('/NewComment/<ticketid>',methods=['POST','GET'])
def create_new_comment(ticketid):
	if('username' in session):
		#Initialise the New Comment form
		form = NewComment()
		#Dynamically generates a list of framework steps ready and populates the selection box with them
		form.frameworkstep.choices = [(framework_step[0], framework_step[1]) for framework_step in [(1,'Preparation'),(2,'Detection and Analysis'),(3,'Containment,Eradication and Recovery'),(4,'Post-Incident Activity')]]
		if form.validate_on_submit():
			#Add the comment to the database, using data from the form.
			database_methods.insert_comment(form.comment.data,database_methods.user_id_from_name(session['username']),ticketid,datetime.datetime.now(),form.frameworkstep.data)
			#render the ticket which the comment has been left on, presenting the new comment.
			return redirect(f'/ViewTicket/{ticketid}')
		#render the template that the form will be shown on and pass the form in.
		return render_template('CreateComment.html',form=form)
	else:
		return redirect('/')

#API endpoint for adding new key information
@app.route('/NewKeyinfo/<ticketid>',methods=['POST','GET'])
def create_new_keyinfo(ticketid):
	if('username' in session):
		#Initialise the key information form
		form = NewKeyInfo()
		if form.validate_on_submit():
			#Insert the key info to the database, upon a successful form validation
			database_methods.insert_keyinfo(form.value.data,ticketid,form.tag.data)
			#render the ticket the key information was added onto.
			return redirect(f'/ViewTicket/{ticketid}')
		#Render template, passing in the form so that it can be rendered.
		return render_template('CreateKeyinfo.html',form=form)
	else:
		return redirect('/')

#API endpoint for adding relationships between tickets
@app.route('/NewRelationship/<pid>',methods=['POST','GET'])
def create_new_relationship(pid):
	if('username' in session):
		message = ""
		#Initialise new relationship form
		form = NewRelationship()
		if form.validate_on_submit():
			#try to add relationship to database, using correct function
			if(database_methods.insert_relationship(pid,form.tid.data)):
			#View the primary ticket the relationships was added to.
				return redirect(f'/ViewTicket/{pid}')
			else:
				message = "Relationship Either Exists or The Linked Ticket Is Invalid!"
		
		#otherwise display the form
		return render_template('CreateRelation.html',form=form,message=message)
	else:
		return redirect('/')

#API endpoint to show the list of all queues
@app.route('/Queues')
def show_queues():
	if('username' in session):
		db,cur = database_methods.db_connection()
		#Find all queues and return them
		queues = cur.execute('SELECT * FROM queue').fetchall()
		#Pass the found queues into the template, to show all queues in a list.
		return render_template('Queues.html',queues=queues)
	
	return redirect('/')

#API endpoint to show the user's profile
@app.route('/Profile')
def show_profile():
	if('username' in session):
		#get user's database id from their username
		user_id = database_methods.user_id_from_name(session['username'])
		db,cur = database_methods.db_connection()
		#select user's open tickets to be displayed from oldest to newest (ASCENDING order)
		tickets = cur.execute('SELECT tickets.name, queue.name, tickets.queue, tickets.id FROM tickets INNER JOIN queue ON tickets.queue = queue.id WHERE owner = ? AND tickets.status != "Resolved" ORDER BY created ASC',(user_id,)).fetchall()
		#pass tickets and user id to the page and render user's account 
		return render_template('Profile.html',id=user_id,tickets=tickets)
	else:
		return redirect('/Login')

#API endpoint to view a specified queue
@app.route('/ViewQueue/<queueid>')
def view_queue(queueid):
	if('username' in session):
		db,cur = database_methods.db_connection()
		#if a queue exists with the id specified
		if(cur.execute('SELECT 1 FROM queue WHERE id = ?',queueid)):
			#fetch the name of the queue using the id specified
			name = cur.execute('SELECT name FROM queue WHERE id = ?',(queueid,)).fetchone()[0]
			#fetch tickets from the queue and organise them by status
			new,under_investigation,on_hold = database_methods.tickets_by_status(queueid)
			#add the length of all lists to find the total amount of tickets
			amount = (len(new) + len(under_investigation) + len(on_hold))
			#Use the method for calculating averages to get the queue's average response time
			avg_pick_up = str(database_methods.get_average_response(queueid)) + " Minutes"
			#fetch the amount of tickets created in the last day
			tix_last_day = database_methods.get_queue_created_lastday(queueid)
			#render template using data gathered to fill in the statistics.
			return render_template('ViewQueue.html',name=name,amount=amount,new = new,ui = under_investigation,oh = on_hold, avg=avg_pick_up, ticksday=tix_last_day)
	return redirect("/")

#API endpoint to view a specified ticket, by id.
@app.route('/ViewTicket/<ticketid>')
def view_ticket(ticketid):
	if('username' in session):
		isOwner = False
		db,cur = database_methods.db_connection()
		#fetch the ticket data for the ticket held at the id provided
		ticket = cur.execute('SELECT name,content,created,id,status,owner FROM tickets WHERE id = ?',(ticketid,)).fetchone()
		#fetch all key information for this ticket.
		key = cur.execute('SELECT info,infotype,id FROM keyinfo WHERE ticket = ?',(ticketid,)).fetchall()
		#fetch all of the comments for the ticket
		comments = cur.execute('SELECT comment,name,datetime,stage,commenter,comments.id FROM comments INNER JOIN users ON commenter = users.id WHERE post = ? ORDER BY datetime DESC',(ticketid,)).fetchall()
		#fetch all the relationships for the ticket.
		relations = cur.execute(f'SELECT relationships.ticketone, tickets.name, relationships.id FROM relationships INNER JOIN tickets ON ticketone = tickets.id WHERE tickettwo = {ticketid} UNION SELECT relationships.tickettwo, tickets.name, relationships.id FROM relationships INNER JOIN tickets ON tickettwo = tickets.id WHERE ticketone = {ticketid}').fetchall()

		#fetch the knowledge mapping of the ticket, should it have. Other wise is false.
		knowledge_id = database_methods.has_incident_identifier(ticket[0])

		#if there is any key information
		if(key):
			#for each piece of key information (enum works like a key, value pairs loop)
			for index,value in enumerate(key):
				#fetch the amount of times this key info has been seen before
				occurances = cur.execute('SELECT COUNT(id) FROM keyinfo WHERE info = ?',(value[0],)).fetchone()[0]
				#reassign the value into the key tuple, by unpacking values and adding it onto the end, needed as tuples are immutable
				key[index] =  *value,occurances
			
			#Sort the key list based on id and reverse order
			key.sort(key=lambda x: x[2], reverse=True)
		
		#If the ticket has comments
		if(comments):
			#list to assign string value based on the integer provided as the framework step, used in lookups.
			lookup = ["Preparation","Detection and Analysis","Containment, Eradication and Recovery","Post-Incident Activity"]
			
			#for each comment
			for index,value in enumerate(comments):
				
				#reassign the current comment, to have the string value of the framework step as well as all of the original contents
				comments[index] = *value[0:3],lookup[value[3]-1],*value[3:]


				#if the user is the creator of the comment
				if (value[4] == database_methods.user_id_from_name(session['username'])):
					#unpack tuple, add a true value to the end of the tuple or reassign value
					comments[index] = *comments[index],True
				else:
					#same as abovee but with false value
					comments[index] = *comments[index],False

		#if the user is the owner of the current ticket, assign isOwner to True
		if(ticket[5] == database_methods.user_id_from_name(session['username'])):
			isOwner = True

		#render template passing the values into populate data
		return render_template('ViewTicket.html',ticket=ticket,key=key,comments=comments,relations=relations,Owner=isOwner,knowledge=knowledge_id)
	else:
		return redirect('/')

#API endpoint to View an Incident summary, organised by incident response framework step
@app.route('/ViewSummary/<ticketid>')
def view_incident_summary(ticketid):
	if('username' in session):
		#fetches comments using the summarise by framework, which uses ticketid to fetch all comments
		comments = database_methods.summarise_by_framework(ticketid)
		return render_template('ViewSummary.html',comments=comments)
	else:
		return redirect('/')

#API endpoint used to display a particular piece of keyinfo and show all instances of it, using the value (ie the IP address)
@app.route('/ViewKeyInfo/<keyinfovalue>')
def present_key_info(keyinfovalue):
	if('username' in session):
		db,cur = database_methods.db_connection()
		#initialise ticket_id_list, used to pass a list of just ticket ids into the template
		ticket_id_list = []
		#fetch all information about the specified piece of key info
		related = cur.execute('SELECT info,ticket,infotype FROM keyinfo WHERE info = ?',(keyinfovalue,)).fetchall()
		#if related tickets are found
		if(related):
			#create a list, by taking just the second value (ticket id) from related, leaving only ticket ids
			ticket_id_list = list(map(lambda a: a[1],related))
		
		#fetch stats about selected key info
		stats = database_methods.key_info_stats(keyinfovalue)
		return render_template('ViewKeyinfo.html',related=related,ids=ticket_id_list,stats=stats)
	else:
		return redirect("/")

#API endpoint to resolve/close down a ticket.
@app.route('/Resolve/<id>',methods=['POST','GET'])
def resolve_ticket(id):
	if('username' in session):
		db,cur = database_methods.db_connection()
		#initialise the set determination form
		form = SetDetermination()
		#upon successful submission
		if form.validate_on_submit():
			#resolve the ticket, using the value of the determination form to specify if true/false positive.
			database_methods.resolve_ticket(id,form.determination.data)
			#View the ticket that has been resolved.
			return redirect(f"/ViewTicket/{id}")
		
		return render_template('SetDetermination.html',form=form)

#API endpoint to re-open a closed ticket.	
@app.route('/Reopen/<ticketid>')
def reopen_ticket(ticketid):
	if('username' in session):
		#use the reopen function and pass the specified id to it.
		database_methods.reopen_closed_ticket(ticketid)
		return redirect(f'/ViewTicket/{ticketid}')
	else:
		return redirect('/')

#API endpoint to take an unowned ticket
@app.route('/TakeTicket/<ticketid>')
def take_tickets(ticketid):
	if('username' in session):
		#use the take new ticket function, specify ticketid and the name of user taking the ticket.
		database_methods.take_new_ticket(ticketid,session['username'])
		#view the newly taken ticket.
		return redirect(f'/ViewTicket/{ticketid}')
	else:
		redirect('/')

#API endpoint to Update the values of a ticket (title,body,etc)
@app.route('/UpdateTicket/<ticketid>',methods=['POST','GET'])
def update_ticket(ticketid):
	#Initialise update ticket form
	form = UpdateTicket()
	db,cur = database_methods.db_connection()
	#fetch the current values of the ticket, so they can be placed into the form to be edited.
	current_values = cur.execute('SELECT name,content,queue,status FROM tickets WHERE id = ?',(ticketid,)).fetchone()
	#for id,queue name in the queue database table - This is used to populate a select field.
	form.queue.choices = [(queue[0], queue[1]) for queue in cur.execute('SELECT id, name FROM queue').fetchall()]
	#populate status select field with values
	form.status.choices = [ status for status in ["Under Investigation","On-Hold"]]
	#Set Values to the Current Values
	if(request.method == 'GET'):
		form.title.default = current_values[0]
		form.content.default = current_values[1]
		form.queue.default = current_values[2]
		form.status.default = current_values[3]
		#pass the data into form, ready for rendering.
		form.process()
	if form.validate_on_submit():
		#Update the content of the ticket in the database.
		database_methods.update_ticket(form.title.data,form.content.data,form.queue.data,form.status.data,ticketid)
		#view the updated ticket.
		return redirect(f'/ViewTicket/{ticketid}')
	return render_template('EditTicket.html',form=form)

#API endpoint to get the user's queue and redirect them to it
@app.route('/FindMyQueue')
def find_my_queue():
	if('username' in session):
		#use the current user's queue from user name
		queue_to_show = database_methods.get_user_queue(session['username'])
		#view the user's queue, found using the above function
		return redirect(f'/ViewQueue/{queue_to_show}')
	else:
		return redirect('/')

#API endpoint used to change a user's queue
@app.route('/ChangeQueue',methods=['GET','POST'])
def change_queue():
	if('username' in session):
		#initialise the form for changing queues
		form = ChangeQueue()
		db,cur = database_methods.db_connection()
		#get user id from using the username, found in session.
		user = database_methods.user_id_from_name(session['username'])
		#populate a select field using all of the values of the queue table in the database.
		form.queue.choices = [(queue[0], queue[1]) for queue in cur.execute('SELECT id, name FROM queue').fetchall()]

		#if the page is being retrieve and is not form submission, populate page with the current information.
		if(request.method == 'GET'):
			current_value = cur.execute('SELECT queue FROM users WHERE id = ?',(user,)).fetchone()[0]
			form.queue.default = current_value
			form.process()

		if form.validate_on_submit():
			#update user queue using function, passing in the new queue id and the user's name
			database_methods.update_user_queue(form.queue.data,user)
			#redirect to user's profile
			return redirect('/Profile')
		else:
			return render_template('ChangeQueue.html',form=form)
	return('/')

#API endpoint used for updating a comment
@app.route('/UpdateComment/<commentid>',methods=['GET','POST'])
def update_comment(commentid):
	if('username' in session):
		db,cur = database_methods.db_connection()
		#initialise the form for updating comments
		form = UpdateComment()
		
		if form.validate_on_submit():
			#using the comment id and new comment value, pass it into function to be updated
			database_methods.update_comment(commentid,form.comment.data)
			#view ticket that comment was left on
			return redirect(f'/ViewTicket/{database_methods.post_from_comment(commentid)}')
		#if the form is being retrieved (not POST request)
		if(request.method == 'GET'):
			#grab the comments current value and populate the text box on form with it.
			current_value = cur.execute('SELECT comment FROM comments WHERE id = ?',(commentid,)).fetchone()[0]
			form.comment.default = current_value
			form.process()
		return render_template('UpdateComment.html',form=form,id=commentid)
	else:
		return redirect('/')

#API endpoint used to search database.
@app.route("/Search")
def search():
	if('username' in session):
		#Fetch the search query string, passed in as a form submission under the name search.
		term = request.args.get('search')
		#Initialise results and id_list, prevent issues should no results be returned
		results = ""
		id_list = ""
		#if the search term is not blank
		if not(term.isspace() or term == ""):
			#search database using term, with function.
			results = database_methods.search(term)
			#if any results are returned
			if(results):
				#return a list of just ticket ids taken from the search results
				id_list = list(map(lambda a: a[0],results))
		return render_template('Search.html',results=results,ids=id_list)
	else:
		return redirect('/')

#API endpoint to remove relationship between two tickets specified
@app.route("/RemoveRelationship/<previousticket>/<tickettoremove>")
def remove_relationship(previousticket,tickettoremove):
	if('username' in session):
		#remove the specified relationship, using function by passing the id of the ticket of the relationship.
		database_methods.remove_relationship(tickettoremove)
		#use the previous ticket to return to it after removal.
		return redirect(f'/ViewTicket/{previousticket}')
	else:
		return('/')

#API endpoint used to update key information
@app.route('/UpdateKeyInfo/<keyinfoid>',methods=['GET','POST'])
def update_key_information(keyinfoid):
	if('username' in session):
		message = ""
		#initialise form for updating key information
		form = UpdateKeyInfo()
		db,cur = database_methods.db_connection()
		if form.validate_on_submit():
			#update key information using information provided from form.
			if(database_methods.update_keyinfo(keyinfoid,form.infotype.data,form.info.data)):
				#find the ticket the key info is on and open it
				ticket = cur.execute('SELECT ticket FROM keyinfo WHERE id = ?',(keyinfoid,)).fetchone()[0]
				return redirect(f"/ViewTicket/{ticket}")
			else:
				message = "Key Information With This Title Already Exists"
		if(request.method == 'GET'):
			#find the current values of the key information and set the form's fields values to it.
			current_value = cur.execute('SELECT infotype,info FROM keyinfo WHERE id = ?',(keyinfoid,)).fetchone()
			form.infotype.default = current_value[0]
			form.info.default = current_value[1]
			form.process()	
		return render_template('UpdateKI.html',form=form,id=keyinfoid,message=message)
	else:
		return('/')

#API endpoint to Remove a piece of key information
@app.route('/RemoveKeyInfo/<keyinfoid>')
def remove_key_information(keyinfoid):
	db,cur = database_methods.db_connection()
	#find the ticket that the key information relates to
	ticket = cur.execute('SELECT ticket FROM keyinfo WHERE id = ?',(keyinfoid,)).fetchone()[0]
	#remove the key information using id
	database_methods.remove_keyinfo(keyinfoid)
	#return to the ticket the keyinformation was used on.
	return redirect(f'/ViewTicket/{ticket}')

#API endpoint to remove comments
@app.route('/RemoveComment/<commentid>')
def remove_comment(commentid):
	db,cur = database_methods.db_connection()
	#use the specified comment id to find the ticket it was left on
	ticket = cur.execute('SELECT post FROM comments WHERE id = ?',(commentid,)).fetchone()[0]
	#remove the comment by specifying id to the function
	database_methods.remove_comment(commentid)
	#return to the ticket the comment was left on
	return redirect(f'/ViewTicket/{ticket}')

#API endpoint used to link multiple tickets to a select "root" (primary) ticket
@app.route('/LinkToRoot/<idlist>',methods=['GET','POST'])
def link_many_to_root(idlist):
	if('username' in session):
		message = ""
		#processes the list, removing the square brace, any spaces and whitespace. Leaving a comma seperated value list, which is then split to make a python list, with one entry per ticket it
		idlist = idlist.replace("[","").replace("]","").replace(" ","").strip().split(",")
		#initialise bulk relation root form
		form = BulkRelationRoot()
		if(form.validate_on_submit()):
			#pass the list of ids to be linked as well as the root, to the function that will link them.
			if(database_methods.bulk_relate_to_root(idlist,form.root.data)):
			#go to the root ticket
				return redirect(f'/ViewTicket/{form.root.data}')
			else:
				message = "Invalid Root Ticket or All Are Already Related!"
		
		return render_template('RelationSetRoot.html',form=form,message=message)

	return redirect('/')

#API endpoint to recursively relate tickets (ie each ticket specified is related to each other)
@app.route('/RecursiveRelate/<idlist>',methods=['GET','POST'])
def add_recursive_relationships(idlist):
	if('username' in session):
		#processes the list, removing the square brace, any spaces and whitespace. Leaving a comma seperated value list, which is then split to make a python list, with one entry per ticket it
		idlist = idlist.replace("[","").replace("]","").replace(" ","").strip().split(",")
		#if there's atleast two ticket ids provided.
		if(len(idlist) >= 2):
			#use the recursive relation function to link each ticket to every other
			database_methods.recursive_relate(idlist)
			#go to the user's queue
			return redirect(f'/FindMyQueue')

	return redirect('/')

#API endpoint used to close any open tickets linked to the current ticket.
@app.route('/CloseLinked/<ticketid>')
def close_all_linked_tickets(ticketid):
	if('username' in session):
		#pass the ticket of the relationships you want to close, along with username to bulk close related tickets
		database_methods.close_linked_tickets(ticketid,database_methods.user_id_from_name(session['username']))
		#go to the ticket that had its related tickets closed.
		return redirect(f'/ViewTicket/{ticketid}')
	else:
		return redirect('/')

#API Endpoint to view any knowledge mappings that exist in the database.
@app.route('/Knowledge')
def display_knowledge_base():
	if('username' in session):
		db,cur = database_methods.db_connection()
		knowledge = cur.execute('SELECT id, title FROM knowledgemap ORDER BY id ASC')

		return render_template('Knowledge.html',knowledge=knowledge)
	else:
		return redirect('/')

#API endpoint to serve the form used to add new knowledge mappings to database.
@app.route('/CreateKnowledge',methods=['GET','POST'])
def create_knowledge_entry():
	if('username' in session):
		#initialise form
		form = CreateKnowledge()
		message = ""
		
		if(form.validate_on_submit()):
			#if knowledge added successfully
			if(database_methods.add_knowledgebase_entry(form.title.data,form.body.data)):
				return redirect('/Knowledge')
			else:
				#otherwise return error to display on page
				message = "Knowledge with this title already exists!"

		return render_template('CreateKnowledge.html',form=form,message=message)
	else:
		return redirect('/')

#API Endpoint to view a particular knowledge mapping
@app.route('/ViewKnowledge/<knowledgeid>')
def view_knowledge_entry(knowledgeid):
	if('username' in session):
		db,cur = database_methods.db_connection()
		#fetch each piece of guidance for one mapping
		knowledge = cur.execute('SELECT title, body, id FROM knowledge WHERE knowledgemap = ?',(knowledgeid,)).fetchall()
		#title and description for the knowledge mapping
		title,description = cur.execute('SELECT title,body FROM knowledgemap WHERE id = ?',(knowledgeid,)).fetchone()
		#fetches a tuple of stats
		stats = database_methods.stats_by_knowledge(knowledgeid)
		return render_template('ViewKnowledge.html',id=knowledgeid,title=title,description=description,knowledge=knowledge,stats=stats)
	else:
		return redirect('/')

#API endpoint to remove a particular mapping from the database
@app.route('/RemoveKnowledge/<knowledgeid>')
def remove_knowledge_entry(knowledgeid):
	if('username' in session):
		database_methods.remove_knowledgebase_entry(knowledgeid)
		return redirect('/Knowledge')
	else:
		return redirect('/')

#Create a piece of guidance for a specified mapping
@app.route('/CreateGuidance/<mapid>',methods=["GET","POST"])
def create_knowledge_guidance(mapid):
	if('username' in session):
		message = ""
		db,cur = database_methods.db_connection()
		form = CreateGuidance()

		if(form.validate_on_submit()):
			#if the data is successfully added to the database
			if(database_methods.create_knowledge_guidance(form.title.data,form.body.data,mapid)):
				#go to the page for the mapping that it has been added to
				return redirect(f'/ViewKnowledge/{mapid}')
			else:
				#upon failure display a message stating why
				message = "Guidance already exists with this title"
		
		return render_template('CreateGuidance.html',form=form,message=message)
	else:
		return redirect('/')

#API endpoint to remove a piece of guidance from a knowledge mapping
@app.route('/RemoveGuidance/<guidanceid>')
def remove_guidance_entry(guidanceid):
	if('username' in session):
		db,cur = database_methods.db_connection()
		#find the mapping that the guidance exists on
		knowledge = cur.execute('SELECT knowledgemap FROM knowledge WHERE id = ?',(guidanceid,)).fetchone()[0]
		db.close()
		#remove the guidance from database using the right function to do so
		database_methods.remove_guidance_entry_fromdb(guidanceid)
		return redirect(f'/ViewKnowledge/{knowledge}')
	else:
		return redirect('/')

#API Endpoint to update the values kept inside the guidance for a knowledge mapping
@app.route('/UpdateGuidance/<guidanceid>',methods=['GET','POST'])
def update_guidance(guidanceid):
	if('username' in session):
		form = UpdateGuidance()
		message = ""
		db,cur = database_methods.db_connection()
		#fetch the existing data for the mapping, plus the mapping it is for.
		curtitle,curbody,knowledgeid = cur.execute('SELECT title,body,knowledgemap FROM knowledge WHERE id = ?',(guidanceid,)).fetchone()
		if(form.validate_on_submit()):
			#if the guidance is updated successfully.
			if(database_methods.update_guidance_entry_fromdb(guidanceid,form.title.data,form.body.data)):
				return redirect(f'/ViewKnowledge/{knowledgeid}')
			else:
				message = "Guidance with this name already exists"
		#set the value of form boxes to the existing values, so they can be updated.
		if(request.method == 'GET'):
			form.title.default = curtitle
			form.body.default = curbody
			form.process()

		return render_template('UpdateGuidance.html',form=form,message=message)
	else:
		return redirect('/')

#API endpoint to update a knowledge mapping
@app.route('/UpdateKnowledge/<mapid>',methods=['GET','POST'])
def update_knowledge_mapping(mapid):
	if('username' in session):
		db,cur = database_methods.db_connection()
		message = ""
		form = UpdateKnowledge()
		#get current values of the knowledge mapping
		curtitle,curbody = cur.execute('SELECT title,body FROM knowledgemap WHERE id = ?',(mapid,)).fetchone()

		if(form.validate_on_submit()):
			#update mapping via database
			if(database_methods.update_knowledge_mapping_fromdb(mapid,form.title.data,form.body.data)):
			#show the map that the guidance is on
				return redirect(f'/ViewKnowledge/{mapid}')
			else:
				message = "Knowledge with This Title Already Exists!"
		#default form values to current values
		if(request.method == 'GET'):
			form.title.default = curtitle
			form.body.default = curbody
			form.process()

		#render form
		return render_template('UpdateKnowledge.html',form=form,message=message)
	else:
		return redirect('/')

#if the script is run as it self and not as a dependancy
if __name__ == "__main__":
	#use the flask built in server
    app.run(debug=True)