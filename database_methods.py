from datetime import date, datetime
import sqlite3
import hashlib
from time import sleep

def db_connection():
	#Connect to or create a database file, store connection as a variable.
	db = sqlite3.connect('./Tickets.db')
	#Create a cursor (allows commands/queries to be run)
	cur = db.cursor()
	#pass the database connection and cursor connection
	return db,cur

#Initialise tables, ready for the ticketing system to use the database.
def table_init():
	db,cur = db_connection()
	
	# Create the tickets table if it doesn't already exist.
	cur.execute('''
				CREATE TABLE IF NOT EXISTS tickets(
				id integer PRIMARY KEY,
				name text not null,
				status text not null,
				owner integer not null,
				queue integer not null,
				content text not null,
				created text not null,
				started text,
				completed text,
				determination text
				);
				''')
	
	#Create queue table if it doesn't exist already
	cur.execute('''
				CREATE TABLE IF NOT EXISTS queue(
				id integer PRIMARY KEY,
				name text not null
				);
				''')
	
	#Create users table if it doesn't exist already
	cur.execute('''
                CREATE TABLE IF NOT EXISTS users(
                    id integer PRIMARY KEY,
                    name text not null,
                    pwd text not null,
					email text not null,
                    queue integer not null
                );
                ''')
	
	#Create key info table, if it doesn't already exist
	cur.execute('''
				CREATE TABLE IF NOT EXISTS keyinfo(
				id integer PRIMARY KEY,
				ticket integer,
				infotype text,
				info text
				);
				''')
	
	#Create comments table, if it doesn't exist already.
	cur.execute('''
				CREATE TABLE IF NOT EXISTS comments(
				id integer PRIMARY KEY,
				comment text not null,
				commenter integer not null,
				post integer not null,
				datetime text not null,
				stage integer not null
				);
				''')
	
	#Create relationships table, if it doesn't already exist
	cur.execute('''
				CREATE TABLE IF NOT EXISTS relationships(
				id integer PRIMARY KEY,
				ticketone not null,
				tickettwo not null
				);
				''')
	
	#create the knowledgemap table, if it doesn't exist
	cur.execute('''
				CREATE TABLE IF NOT EXISTS knowledgemap(
				id integer PRIMARY KEY,
				title text not null,
				body text not null
				);	
				''')
	
	#create the knowledge table, if it doesn't exist
	cur.execute('''
				CREATE TABLE IF NOT EXISTS knowledge(
				id integer PRIMARY KEY,
				knowledgemap integer not null,
				title text not null,
				body text not null
				);
				''')
	#Create a default queue if none exist
	if not(cur.execute('SELECT * FROM queue').fetchone()):
		cur.execute('INSERT INTO queue(name) VALUES (?)',('Incident Response',))
	
	#Create the nobody user if it doesn't already exist.
	if not(cur.execute('SELECT * FROM users').fetchone()):
		cur.execute('INSERT INTO users(name,pwd,email,queue) VALUES (?,?,?,?)',('Nobody',"0","null@null.com",0))

	db.commit()
	

def insert_user(name,pwd,email,queue):
	db,cur = db_connection()
	#Hash the password using Sha-512 secure hashing and translate to hexadecimal
	pwd = hashlib.sha512(pwd.encode('utf-8')).hexdigest()
	#If a user with the name doesn't already exist, create user with details passed from form and hashed password
	if not (cur.execute('SELECT 1 FROM users WHERE name = ?',(name,)).fetchone()):
		cur.execute('INSERT INTO users(name,pwd,email,queue) VALUES (?,?,?,?)',(name,pwd,email,queue,))
		db.commit()
		return True
	else:
		return False

#This is used for manual ticket creation, thus the ticket status starts as under investigation
def insert_ticket(name,queue,content,owner,created,status="Under Investigation"):
	db,cur = db_connection()
	#Create ticket using values supplied from the submitted form
	cur.execute('INSERT INTO tickets (name,queue,content,owner,created,status,started) VALUES (?,?,?,?,?,?,?)',(name,queue,content,owner,created,status,created,))
	db.commit()

#Creating a new ticket queue
def insert_queue(name):
	db,cur = db_connection()
	#Create a new ticket queue if one doesn't already exist with the same name, use data supplied from form
	if not(cur.execute('SELECT 1 FROM queue WHERE name = ?',(name,)).fetchone()):
		cur.execute('INSERT INTO queue (name) VALUES (?)',(name,))
		db.commit()
		return True
	
	return False

#Create new key information and add to the database
def insert_keyinfo(value,tickno,tag):
	db,cur = db_connection()
	#If a specified ticket doesn't already have the particular key information, add it to the database.
	if not(cur.execute('SELECT 1 FROM keyinfo WHERE info = ? AND ticket = ?',(value,tickno,)).fetchone()):
		cur.execute('INSERT INTO keyinfo (info,ticket,infotype) VALUES (?,?,?)',(value,tickno,tag,))
	else:
		#If it already exists, update the infotype, which specifies what the data is
		cur.execute('UPDATE keyinfo SET infotype = ? WHERE ticket = ? AND info = ?',(tag,tickno,value,))
	db.commit()

#Generate a ticket from an email	
def generate_email_ticket(name,queue,content,owner,status):
	#Use the current time as the ticket creation time
    created = datetime.now()
    db,cur = db_connection()
	#Insert values supplied by the email body to create a new ticket in the database
    cur.execute('INSERT INTO tickets (name,queue,content,owner,created,status) VALUES (?,?,?,?,?,?)',(name,queue,content,owner,created,status,))
    db.commit()

#Check credentials passed from a login attempt
def check_login(name,pattempt):
	db,cur = db_connection()
	#If a user exists with the supplied username
	if(cur.execute('SELECT 1 FROM users WHERE name = ?',(name,)).fetchone()):
		#Fetch the hashed password of the supplied account from database
		hashed = cur.execute('SELECT pwd FROM users WHERE name = ?',(name,)).fetchone()[0]
		#Hash the password from the login attempt
		pwd = hashlib.sha512(pattempt.encode('utf-8')).hexdigest()
		#If the hash of the password attempt matches the correct password for the username supplied, return True
		if(pwd == hashed):
			return True
	
	return False

#Get a users database ID from the name supplied
def user_id_from_name(name):
	db,cur = db_connection()
	return cur.execute('SELECT id FROM users WHERE name = ?',(name,)).fetchone()[0]

#Insert a comment into the database using data supplied from the the add comment form
def insert_comment(comment,commenter,post,datetime,step):
	db,cur = db_connection()
	cur.execute('INSERT INTO comments (comment,commenter,post,datetime,stage) VALUES (?,?,?,?,?)',(comment,commenter,post,datetime,step,))
	db.commit()

#Reopen a ticket that has been closed.
def reopen_closed_ticket(ticketid):
	db,cur = db_connection()
	cur.execute(f'UPDATE tickets SET status = "Under Investigation" WHERE id = ?',(ticketid,))
	db.commit()

#Creates a new relationship in the relationships database table
def insert_relationship(t1,t2):
	db,cur = db_connection()
	#Transform the ids of the tickets passed into the function into integers
	t1 = int(t1)
	t2 = int(t2)
	#If they are for the same ticket, return false since a relationship to the same ticket is not possible
	if(t1==t2):
		return False
	#if the id supplied for both tickets exist
	if(cur.execute('SELECT 1 FROM tickets WHERE id = ?',(t1,)).fetchone() and cur.execute('SELECT 1 FROM tickets WHERE id = ?',(t2,)).fetchone()):
		#if the tickets are not already linked
		if not (cur.execute('SELECT 1 FROM relationships WHERE ticketone = ? AND tickettwo = ?',(t1,t2,)).fetchone() or cur.execute('SELECT 1 FROM relationships WHERE ticketone = ? AND tickettwo = ?',(t2,t1,)).fetchone()):
			cur.execute('INSERT INTO relationships (ticketone,tickettwo) VALUES (?,?)',(t1,t2,))
			db.commit()
			return True
	
	return False

#Set a ticket as resolved, set the completed time and update determination in the database
def resolve_ticket(post,determination):
	db,cur = db_connection()
	cur.execute('UPDATE tickets SET status = ?, completed = ?, determination = ? WHERE id = ?',('Resolved',datetime.now(),determination,post,))
	db.commit()

#Become the owner of a ticket with the status of New
def take_new_ticket(ticketid,user):
	db,cur = db_connection()
	#Get the users id from their name
	user = user_id_from_name(user)
	#If the ticket is owned by the Nobody user (this is a null account and can only be done on New tickets generated by server), update the user.
	if(cur.execute('SELECT users.name FROM tickets INNER JOIN users ON users.id = tickets.owner WHERE tickets.id = ?',(ticketid,)).fetchone()[0] == "Nobody"):
		cur.execute('UPDATE tickets SET status = ?,owner = ?,started=? WHERE id = ?',("Under Investigation",user,datetime.now(),ticketid,))
		db.commit()

#Fetch all of the tickets that a user owns
def view_user_tickets(user):
	db,cur = db_connection()
	return cur.execute('SELECT tickets.id,tickets.name,queue.name FROM tickets INNER JOIN queue ON tickets.queue = queue.id WHERE owner = ? AND status != "Resolved"',(user,)).fetchall()

#Update a ticket with information passed in by a successful form submission
def update_ticket(title,content,queue,status,id):
	db, cur = db_connection()
	cur.execute('UPDATE tickets SET name = ?, content = ?, queue = ?, status = ? WHERE id = ?',(title,content,queue,status,id,))
	db.commit()

#Fetch all of the tickets from a queue and organise them into lists based on their current stats
def tickets_by_status(queue):
	db,cur = db_connection()
	#New, Under Investigation, On-Hold
	new,ui,oh = [],[],[]
	tickets = cur.execute('SELECT tickets.id,tickets.name,users.name,tickets.created,tickets.status FROM tickets INNER JOIN users ON tickets.owner = users.id WHERE tickets.queue = ? AND tickets.status != "Resolved"',(queue,)).fetchall()
	#For each ticket, append ticket data to correct list based on its current status
	for ticket in tickets:
		if(ticket[4] == "New"):
			new.append(ticket)
		elif(ticket[4] == "Under Investigation"):
			ui.append(ticket)
		elif(ticket[4] == "On-Hold"):
			oh.append(ticket)
	return new,ui,oh

#Get the number of tickets created in a specified queue in the last day
def get_queue_created_lastday(id):
	db,cur = db_connection()
	lastdaystickets = cur.execute('SELECT COUNT(id) FROM tickets WHERE created > datetime("now","-1 days") AND queue = ?',(id,))
	return lastdaystickets.fetchone()[0]

#Get the total amount of tickets created in the last day for all queues combined
def get_total_created_lastday():
	db,cur = db_connection()
	lastdaystickets = cur.execute('SELECT COUNT(id) FROM tickets WHERE created > datetime("now","-1 days")')
	return lastdaystickets.fetchone()[0]

#Works out the average response time, of all queues or of a specified queue (Optional)
def get_average_response(id=0):
	db,cur = db_connection()
	#If a queue is specified, calculate the average response time of that queue
	if(id):
		lastdaystickets = cur.execute('SELECT (julianday(started) - julianday(created))*3600 FROM tickets WHERE started > datetime("now","-1 days") AND queue = ? AND started != "Null"',(id,)).fetchall()
	#Otherwise calculate the response time for all queues combined
	else:
		lastdaystickets = cur.execute('SELECT (julianday(started) - julianday(created))*3600 FROM tickets WHERE started > datetime("now","-1 days") AND started != "Null"').fetchall()
	#if any tickets have been generated in the last day, workout the average response rate based on the Mean of all response times (sum of all responses / amount of responses)
	if(lastdaystickets):
		total = 0
		for ticket in lastdaystickets:
			total += ticket[0]
		#work out mean and round value to 2 decimal places, helps with readability
		return round(total/len(lastdaystickets),2)
	else:
		return 0

#Returns tickets that have yet to be completed, but have exceeded an acceptable amount of time between being created and started.
def get_untaken_overdue():
	#SLA = Service Level Agreement, used in this case to mean how quickly tickets should be taken before it becomes a problem. The value is the amount of minutes.
	SLA = 15
	db,cur = db_connection()
	#Fetch the id and time taken for tickets that are currently exceeding the acceptable time frame as set by SLA, tickets must have been created in the last 24hrs and have been started but not finished.
	lastdaystickets = cur.execute(f'SELECT id,(julianday(started) - julianday(created))*3600 AS timetaken FROM tickets WHERE created > datetime("now","-1 days") AND timetaken > {SLA} AND started != "Null" AND completed != "Null"').fetchall()
	return lastdaystickets

#Takes the users name, finds their database id and then uses it to find their selected queue
def get_user_queue(name):
	db,cur = db_connection()
	return cur.execute('SELECT queue FROM users WHERE id = ?',(user_id_from_name(name),)).fetchone()[0]

#Updates the queue of the user of the ID that is passed, to the new queue which is also passed in.
def update_user_queue(newqueue,id):
	db,cur = db_connection()
	cur.execute('UPDATE users SET queue = ? WHERE id = ?',(newqueue,id,))
	db.commit()

#Fetch the busiest queues (max of top 3), by ticket volume in descending order (largest first). This is grouped by queue and is based on volume in the last 24hrs.
def get_busiest_queues():
	db,cur = db_connection()
	queues = cur.execute('SELECT COUNT(tickets.id),queue.name FROM tickets INNER JOIN queue ON queue.id = tickets.queue WHERE tickets.created > datetime("now", "-1 Days") GROUP BY queue ORDER BY COUNT(tickets.id) DESC LIMIT 3')
	return queues.fetchall()

#Calculates the percentage of false positives from the last 24hrs
def get_falsepos_today():
	db,cur = db_connection()
	#Grab all resolved tickets from the last day, group them by determination
	ticket_by_determ = cur.execute('SELECT COUNT(id), determination FROM tickets WHERE status = "Resolved" AND completed != "Null" AND completed > datetime("now", "-1 Days") GROUP BY determination').fetchall()
	#If no tickets
	if(not ticket_by_determ):
		return 0

	#If there isn't both True and False Positive tickets (means there is only True or False positive)
	if(len(ticket_by_determ) != 2):
		#If the only determination isn't True positive, return 100(%), else return 0% (as there is no false positives)
		if(ticket_by_determ[0][1] != "True Positive"):
			return 100
		else:
			return 0

	#All the amount of false positives to True positives to make a total
	total = ticket_by_determ[0][0] + ticket_by_determ[1][0]
	false = 0

	#iterate between the groups of results (True or False positives), once false positive is found get the amount of them that there is
	for determ in ticket_by_determ:
		if(determ[1] != "False Positive"):
			continue
		false = determ[0]
	
	#Return the percentage of false positives to true, with no decimal places
	return round(false/total*100)

#Get the stats for the front page, using three previously defined functions and returning them as a list to be accessed by index
def get_frontpage_stats():
	db,cur = db_connection()
	return get_total_created_lastday(),get_falsepos_today(),get_average_response(),average_timeto_resolution(),tickets_taken_late(),most_effective_analyst()

#Generate a summary of an incident, based on the id of the ticket.
def summarise_by_framework(ticket):
	db,cur = db_connection()
	#get all comments in order of the stage they were in, then by the date they were posted.
	comments = cur.execute('SELECT comment, commenter, datetime, stage FROM comments WHERE post = ? ORDER BY stage, datetime',(ticket,)).fetchall()
	
	#Return false and end the function if no comments
	if not(comments):
		return False

	#create a two dimensional list, with each of the inner lists being for each of the stages of the NIST framework
	sorted_comments = [[],[],[],[]]

	for comment in comments:
		#Use the the number of the stage - 1 (as Python indexes start at 0 not 1), append to the list at that value. Removes the framework stage from the value that is appened.
		sorted_comments[comment[3]-1].append(comment[0:3])
	
	return sorted_comments

#Searches the database using a value passed from the search box on the Navbar.
def search(term):
	db,cur = db_connection()
	#fetches all tickets in which the title, content,comments or key information contains the term passed as a a parameter
	results = cur.execute(f'''SELECT tickets.id, tickets.name, tickets.created, users.name FROM comments INNER JOIN tickets ON tickets.id = comments.post 
							  INNER JOIN users ON tickets.owner = users.id WHERE comments.comment LIKE "%{term}%" 
							  UNION SELECT tickets.id, tickets.name, tickets.created, users.name  FROM tickets 
							  INNER JOIN users ON tickets.owner = users.id WHERE tickets.name LIKE "%{term}%" OR content LIKE "%{term}%"
							  UNION SELECT tickets.id, tickets.name, tickets.created, users.name FROM keyinfo INNER JOIN tickets ON tickets.id = keyinfo.ticket
							  INNER JOIN users ON tickets.owner = users.id WHERE keyinfo.infotype LIKE "%{term}%" OR keyinfo.info LIKE "%{term}%"
							  ORDER BY created DESC''').fetchall()
	
	#if no results return false and end function
	if not(results):
		return False
	
	#otherwise return all of the results found
	return results

#Lookup a ticket a comment (comment id is passed as parameter) was posted on
def post_from_comment(id):
	db,cur = db_connection()
	return cur.execute('SELECT post FROM comments WHERE id = ?',(id,)).fetchone()[0]

#Updates a comment, to its new value as specified by the submission of a form
def update_comment(id,new_value):
	db,cur = db_connection()
	cur.execute('UPDATE comments SET comment = ? WHERE id = ?',(new_value,id,))
	db.commit()

#Delete a relationship from a database, based on the supplied relationship id
def remove_relationship(id):
	db,cur = db_connection()
	cur.execute('DELETE FROM relationships WHERE id = ?',(id,))
	db.commit()

#Delete a piece of Key Information based on the key information id
def remove_keyinfo(keyinfoid):
	db,cur = db_connection()
	cur.execute('DELETE FROM keyinfo WHERE id = ?',(keyinfoid,))
	db.commit()

#Remove a comment from database, based on the id of the comment supplied.
def remove_comment(commentid):
	db,cur = db_connection()
	cur.execute('DELETE FROM comments WHERE id = ?',(commentid,))
	db.commit()

#Update a piece of key info, based on values supplied from a submitted form
def update_keyinfo(keyinfoid,infotype,info):
	db,cur = db_connection()
	ticket = cur.execute('SELECT ticket FROM keyinfo WHERE id = ?',(keyinfoid,)).fetchone()[0]
	print(ticket)
	if not(cur.execute('SELECT 1 FROM keyinfo WHERE info = ? AND ticket = ?',(info,ticket,)).fetchone()):
		cur.execute('UPDATE keyinfo SET infotype = ?, info = ? WHERE id = ?',(infotype,info,keyinfoid,))
		db.commit()
		return True
	
	else:
		return False

#Find a ticket using an exact match of title and body, this is used to find the ticket created from an email and return the id of the ticket, so that key information can be attributed to the correct ticket.
def find_email_ticket(title,body):
	db,cur = db_connection()
	return cur.execute('SELECT id FROM tickets WHERE name = ? AND content = ? ORDER BY created DESC',(title,body,)).fetchone()[0]

#Add key information found at ticket generation to the database, takes in a list of found key info
def auto_key_info(ticket_id,findings):
	db,cur = db_connection()

	if not(findings):
		return False

	for finding in findings:
		#checks that the key information isn't a duplicate for this ticket, no duplicates are added
		if not(cur.execute('SELECT 1 FROM keyinfo WHERE ticket = ? AND info = ?',(ticket_id,finding,)).fetchone()):
			#insert key information to database, the infotype helps to show it was an automatic finding
			cur.execute('INSERT INTO keyinfo (ticket,info,infotype) VALUES (?,?,?)',(ticket_id,finding,"extracted key info",))

	db.commit()

#Closes linked tickets, leaving a comment to explain why
def close_linked_tickets(ticket_id,user):
	db,cur = db_connection()
	#Fetch all of the related tickets to the selected Root ticket, that haven't been reolved yet.
	related_tickets = cur.execute(f'SELECT ticketone FROM relationships INNER JOIN tickets on ticketone = tickets.id WHERE tickettwo = {ticket_id} AND status != "Resolved" UNION SELECT tickettwo FROM relationships INNER JOIN tickets ON tickets.id = tickettwo WHERE ticketone = {ticket_id} AND status != "Resolved"').fetchall()
	
	#if tickets that haven't been resolved are found
	if(related_tickets):
		#update each of them to be resolved and set the closing time as now. This statement is like a for loop.
		cur.executemany(f'UPDATE tickets SET status = "Resolved", completed = "{str(datetime.now())}" WHERE id = ?',related_tickets)
		#Comment to be left on closed tickets.
		comment = f"This ticket has been deemed to be related to another ticket and as such has been closed and linked to a Root Ticket. Visit the root ticket for further investigation."
		#Iterate the results of the related_tickets and leave a comment on each that is closed to explain why.
		cur.executemany(f'INSERT INTO comments (comment,commenter,post,datetime,stage) VALUES ("{comment}","{user}",?,"{datetime.now()}",1)',related_tickets)
	
	db.commit()

#Takes a series of ticket ids and links them to one selected ticket, if it isn't already.			
def bulk_relate_to_root(tickets,root):
	total = 0
	if(root):
		for ticket in tickets:
			if(insert_relationship(root,ticket)):
				total += 1
	
	#if at least one was added to database.
	if total >= 1:
		return True
	else:
		False

#Takes a series of tickets and recursively relates them to one another, each ticket will be related to every other one by the end.
def recursive_relate(tickets):
	for ticket in tickets:
		for other in tickets:
			insert_relationship(ticket,other)

#Takes a tickets title and finds if it has a knowledge mapping ID in it, returning it if so
def has_incident_identifier(title):
	identifier_prefix = "INC"
	identifier = 0

	#splits the title into words looking for the prefix that indicates a knowledge mapping. replaces the prefix with a blank character to get the ID
	for string in title.split(" "):
		if(identifier_prefix in string):
			identifier = string.replace(identifier_prefix,"")

	db,cur = db_connection()
	#if an identifier is found, return it
	if(identifier_prefix in title and identifier != 0):
		if(cur.execute('SELECT 1 FROM knowledgemap WHERE id = ?',(identifier,)).fetchone()):
			return identifier

	return False

#Add a knowledge mapping to the database, if one with the same name doesn't already exist
def add_knowledgebase_entry(title,body):
	db,cur = db_connection()
	if not (cur.execute('SELECT 1 FROM knowledgemap WHERE title = ?',(title,)).fetchone()):
		cur.execute('INSERT INTO knowledgemap (title,body) VALUES (?,?)',(title,body,))
		db.commit()
		return True
	else:
		return False

#removes a knowledge mapping from the database if it exists		
def remove_knowledgebase_entry(knowledgeid):
	db,cur = db_connection()
	if not(cur.execute('SELECT 1 FROM knowledgemap WHERE id = ?',(knowledgeid,))):
		return False
	
	cur.execute('DELETE FROM knowledgemap WHERE id = ?',(knowledgeid,))
	db.commit()
	remove_all_guidance(knowledgeid)
	return True

#Gets stats about a knowledge mapping, including the total seen (ever), false positive ratio and volume seen in the last seven days
def stats_by_knowledge(knowledgeid):
	db,cur = db_connection()
	search_string = "INC" + str(knowledgeid)
	false_pos_percentage = 0

	#All stats use a LIKE search (works like a contains function) the occurance must have a space after to prevent finding 100 when looking for 1 or 10, etc

	total = cur.execute(f'SELECT COUNT(id) FROM tickets WHERE name LIKE "%{search_string} %"').fetchone()[0]

	false_pos = cur.execute(f'SELECT COUNT(id) FROM tickets WHERE name LIKE "%{search_string} %" AND determination = "False Positive" AND determination != "NULL"').fetchone()[0]

	volume = cur.execute(f'SELECT COUNT(id) FROM tickets WHERE name LIKE "%{search_string} %" AND created > datetime("now", "-7 Days")').fetchone()[0]

	if(false_pos):
		false_pos_percentage = round((false_pos / total)*100)

	return total,false_pos_percentage,volume


#Creates a guidance entry for a particular knowledge mapping
def create_knowledge_guidance(title,body,knowledgemap):
	db,cur = db_connection()
	#if guidance for this mapping exists with the same name, stop. Else enter values to database
	if(cur.execute('SELECT 1 FROM knowledge WHERE knowledgemap = ? AND title = ?',(knowledgemap,title,)).fetchone()):
		return False

	cur.execute('INSERT INTO knowledge (title,body,knowledgemap) VALUES (?,?,?)',(title,body,knowledgemap,))
	db.commit()
	return True

#removes a piece of guidance from the database, if it exists.
def remove_guidance_entry_fromdb(guidanceid):
	db,cur = db_connection()
	if not(cur.execute('SELECT 1 FROM knowledge WHERE id = ?',(guidanceid,)).fetchone()):
		return False
	
	cur.execute('DELETE FROM knowledge WHERE id = ?',(guidanceid,))
	db.commit()
	return True

#Update the values of a piece of guidance, if it exists.
def update_guidance_entry_fromdb(guidanceid,newtitle,newbody):
	db,cur = db_connection()
	if not(cur.execute('SELECT 1 FROM knowledge WHERE id = ?',(guidanceid,)).fetchone()) or cur.execute('SELECT 1 FROM knowledge WHERE id != ? AND title = ?',(guidanceid,newtitle,)).fetchone():
		return False
	
	cur.execute('UPDATE knowledge SET title = ?, body = ? WHERE id = ?',(newtitle,newbody,guidanceid,))
	db.commit()
	return True

#checks that a knowledge map exists and updates it with values sent from a form, after the title is validated to not already exist
def update_knowledge_mapping_fromdb(mapid,newtitle,newbody):
	db,cur = db_connection()
	if not(cur.execute('SELECT 1 FROM knowledgemap WHERE id = ?',(mapid,)).fetchone()) or (cur.execute('SELECT 1 from knowledgemap WHERE title = ? AND id != ?',(newtitle,mapid,)).fetchone()):
		return False
	
	cur.execute('UPDATE knowledgemap SET title = ?, body = ? WHERE id = ?',(newtitle,newbody,mapid,))
	db.commit()
	return True

#removes all guidance for a mapping from the database, used when removing a mapping to prevent guidance being inherited.
def remove_all_guidance(mapid):
	db,cur = db_connection()
	cur.execute('DELETE FROM knowledge WHERE knowledgemap = ?',(mapid,))
	db.commit()

#Fetch stats about a specified piece of key information
def key_info_stats(keyinfovalue):
	db,cur = db_connection()
	false_positive = 0
	#get all occurences of the key info
	tickets = cur.execute('SELECT ticket FROM keyinfo WHERE info = ?',(keyinfovalue,)).fetchall()
	#find how many occurances there has been
	total = len(tickets)
	#Fetch only the amount of tickets that have been resolved, to giver better indication to how many are false positive if lots came in at once.
	total_resolved = cur.execute('SELECT COUNT(tickets.id) FROM keyinfo INNER JOIN tickets on tickets.id = keyinfo.ticket WHERE info = ? AND status = "Resolved"',(keyinfovalue,)).fetchone()[0]
	#if there is any occurances, find out how many have been False Positive
	if(tickets):
		#find out the percentage that have been false positive, if none have been found will default to zero
		try:
			false_positive = round((cur.execute('SELECT COUNT(tickets.id) FROM keyinfo INNER JOIN tickets on tickets.id = keyinfo.ticket WHERE status = "Resolved" AND info = ? AND determination = "False Positive"',(keyinfovalue,)).fetchone()[0] / total_resolved) * 100)
		except ZeroDivisionError:
			pass
		
	#get the amount of occurences from the last 7 days
	volume = cur.execute('SELECT COUNT(tickets.id) FROM keyinfo INNER JOIN tickets on keyinfo.ticket = tickets.id WHERE info = ? AND created > datetime("now", "-7 Days")',(keyinfovalue,)).fetchone()[0]

	#return stats as a tuple to be accessed by index
	return total,false_positive,volume

#Fetches the three most active analysts (By the amount of tickets they've resolved) Last day only.
def most_effective_analyst():
	db,cur = db_connection()
	analysts = cur.execute('SELECT users.name,COUNT(tickets.id) FROM tickets INNER join users on owner=users.id WHERE created > datetime("now","-1 Days") AND status = "Resolved" ORDER BY COUNT(tickets.id) DESC LIMIT 3').fetchall()
	if analysts[0][1]==0:
		return False
	else:
		return analysts

#Gets the average time to resolve a ticket, from the last day.
def average_timeto_resolution():
	db,cur = db_connection()
	average = cur.execute('SELECT AVG((julianday(completed) - julianday(created))*24*60) FROM tickets WHERE status="Resolved" AND created > datetime("now","-1 Days")').fetchone()[0]
	if not(average):
		return 0
	return round(average)

#How many tickets have been taken over acceptable limits in  the last day
def tickets_taken_late():
	acceptable = 15
	db,cur = db_connection()
	tickets = cur.execute('SELECT COUNT(id) FROM tickets WHERE started > datetime("now","-1 Days") AND (julianday(started) - julianday(created))*24*60 > ?',(acceptable,)).fetchone()[0]
	return tickets