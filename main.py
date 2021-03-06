import webapp2
import snippets
import json
import urllib
import os
import hashlib
from google.appengine.ext import ndb
from google.appengine.api import urlfetch

clientId = "867857451041-alogqb26a4uiusrf3ou1lc4ja3co7vr8.apps.googleusercontent.com"
clientSecret = "s6aKP4UNC15g72nKCvLJlpVZ"
redirectUri = "https://library-157519.appspot.com/oauth"
redirect2 = "https://library-157519.appspot.com/oauth"

class User(ndb.Model):
	stateXSRF = ndb.StringProperty()
	token = ndb.StringProperty(default="Null")

class Book(ndb.Model):
	title = ndb.StringProperty()
	author = ndb.StringProperty()
	checkedIn = ndb.BooleanProperty(required=True)
	isbn = ndb.StringProperty()
	genre = ndb.StringProperty(repeated=True)

class Customer(ndb.Model):
	name = ndb.StringProperty()
	balance = ndb.FloatProperty(default=0)
	checked_out = ndb.StringProperty(repeated=True)

class MainPage(webapp2.RequestHandler):

	def get(self):
		self.response.headers['Content-Type'] = 'text/plain'
		self.response.write('Hello, World!')

	def delete(self):
		bookCollection = Book.query()
		customerCollection = Customer.query()
		for iterBook in bookCollection:
			#self.response.write(json.dumps(iterBook.to_dict()))
			iterBook.key.delete()
			#REMEMBER TO IMPLEMENT THE TOTAL CUSTOMER DELETE
		for iterCust in customerCollection:
			iterCust.key.delete()

class BookListHandler(webapp2.RequestHandler):

	def get(self,id=None):
		if id:
			serveBook = ndb.Key(urlsafe=id).get()
			book_dict = serveBook.to_dict()
			book_dict['self'] = '/books/' + serveBook.key.urlsafe()
			self.response.write(json.dumps(book_dict))
		elif self.request.params:
			query = Book.query()
			for i in self.request.params:
				if i in ['genre','author','title','checkedIn','isbn']:
					valueArg = self.request.params[i]
					if i == 'checkedIn':
						if valueArg == "true":
							valueArg = True
						else:
							valueArg = False
					query = query.filter(Book._properties[i] == valueArg)
				else:
					self.response.status_int = 400
					self.response.status_message = 'Client Error'
					self.response.out.write("Client Error")
			completeSet = query.fetch()
			for result in completeSet:
				result_dict = result.to_dict()
				result_dict['self'] = '/books/' + result.key.urlsafe()
				self.response.write(result_dict)
		else:
			bookCollection = Book.query().fetch()
			for book in bookCollection:
				book_dict = book.to_dict()
				book_dict['self'] = '/books/' + book.key.urlsafe()
				self.response.write(json.dumps(book_dict))

	def post(self):
		parent_key = ndb.Key(Book, "parent_book")
		book_data = json.loads(self.request.body)
		new_book = Book(title=book_data['title'],author=book_data['author'],genre=book_data['genre'],isbn=book_data['isbn'],checkedIn=book_data['checkedIn'], parent=parent_key)
		new_book.put()
		book_dict = new_book.to_dict()
		book_dict['self'] = '/books/' + new_book.key.urlsafe()
		self.response.write(json.dumps(book_dict))

	def delete(self,id=None):
		if id:
			serveBook = ndb.Key(urlsafe=id).get()
			serveBook.key.delete()
		else:
			bookCollection = Book.query()
			for iterBook in bookCollection:
				#debug
				self.response.write(json.dumps(iterBook.to_dict()))
				iterBook.key.delete()

	def patch(self,id=None):
		#load request item from data store
		targBook = (ndb.Key(urlsafe=id)).get()
		body_vals = json.loads(self.request.body)
		for i in body_vals:
			if i == "title":
				targBook.title = body_vals[i]
			elif i == "author":
				targBook.author = body_vals[i]
			elif i == "checkedIn":
				targBook.checkedIn = body_vals[i]
			elif i == "isbn":
				targBook.isbn = body_vals[i]
			else:
				break
		targBook.put()

	def put(self,id=None):
		body_vals = json.loads(self.request.body)
		#check if all fields in body are valid
		for i in body_vals:
			if i not in ['title','author','isbn','genre']:
				self.response.status_int = 400
				self.response.status_message = 'Client Error'
				self.response.out.write("Client Error")
				return
		#if here, the put is valid and valid fields will be replaced, absent fields nulled
		targBook = (ndb.Key(urlsafe=id)).get()
		targBook.title = ""
		targBook.author = ""
		targBook.isbn = ""
		targBook.genre = [""]
		for i in body_vals:
			if i == "title":
				targBook.title = body_vals[i]
			elif i == "author":
				targBook.author = body_vals[i]
			elif i == "checkedIn":
				targBook.checkedIn = body_vals[i]
			elif i == "isbn":
				targBook.isbn = body_vals[i]
			else:
				break
		targBook.put()

class CustomerHandler(webapp2.RequestHandler):

	def get(self,id=None):
		if id:
			serveCustomer = ndb.Key(urlsafe=id).get()
			customer_dict = serveCustomer.to_dict()
			customer_dict['self'] = '/customers/' + serveCustomer.key.urlsafe()
			self.response.write(json.dumps(customer_dict))
		else:
			customerCollection = Customer.query()
			for cust in customerCollection:
				cust_dict = cust.to_dict()
				cust_dict['self'] = '/customers/' + cust.key.urlsafe()
				self.response.write(json.dumps(cust_dict))

	def post(self):
		parent_key = ndb.Key(Customer, "parent_customer")
		cust_data = json.loads(self.request.body)
		new_cust = Customer(name=cust_data['name'],balance=cust_data['balance'],checked_out=cust_data['checked_out'], parent=parent_key)
		new_cust.put()
		cust_dict = new_cust.to_dict()
		cust_dict['self'] = '/customers/' + new_cust.key.urlsafe()
		self.response.write(json.dumps(cust_dict))

	def delete(self,id=None):
		if id:
			serveCust = ndb.Key(urlsafe=id).get()
			for link in serveCust.checked_out:
				if link.startswith('/books/'):
					bookkey = link[7:]
					self.response.write(link)
					targBook = ndb.Key(urlsafe=bookkey).get()
					targBook.checkedIn = True
					targBook.put()
			serveCust.key.delete()
		else:
			customerCollection = Customer.query()
			for iterCust in customerCollection:
				#debug
				for link in iterCust.checked_out:
					if link.startswith('/books/'):
						bookkey = link[7:]
						targBook = ndb.Key(urlsafe=bookkey).get()
						targBook.checkedIn = true
						targBook.put()
				iterCust.key.delete()

	def patch(self,id=None):
		#load request item from data store
		targCust = (ndb.Key(urlsafe=id)).get()
		body_vals = json.loads(self.request.body)
		for i in body_vals:
			if i == "name":
				targCust.name = body_vals[i]
			elif i == "balance":
				targCust.balance = body_vals[i]
			else:
				break
		targCust.put()

	def put(self,id=None):
		#check if all fields in body are valid
		body_vals = json.loads(self.request.body)
		for i in body_vals:
			if i not in ['name','balance']:
				self.response.status_int = 400
				self.response.status_message = 'Client Error'
				self.response.out.write("Client Error")
				return
		#if here, the put is valid and valid fields will be replaced, absent fields nulled
		targCust = (ndb.Key(urlsafe=id)).get()
		targCust.name = ""
		targCust.balance = 0
		for i in body_vals:
			if i == "name":
				targCust.name = body_vals[i]
			elif i == "balance":
				targCust.balance = body_vals[i]
			else:
				break
		targCust.put()

class CheckoutHandler(webapp2.RequestHandler):

	def put(self,custID=None,bookID=None):
		if custID and bookID:
			targBook = (ndb.Key(urlsafe=bookID)).get()
			targCust = (ndb.Key(urlsafe=custID)).get()
			if targBook.checkedIn == True:
				targBook.checkedIn = False
				link = '/books/' + targBook.key.urlsafe()
				targCust.checked_out.append(link)
				targCust.put()
				targBook.put()
			else:
				self.response.status_int = 400
				self.response.status_message = 'Client Error'
				self.response.out.write("Client Error")
		else:
			self.response.status_int = 400
			self.response.status_message = 'Client Error'
			self.response.out.write("Client Error")

	def delete(self,custID=None,bookID=None):
		if custID and bookID:
			targBook = (ndb.Key(urlsafe=bookID)).get()
			targCust = (ndb.Key(urlsafe=custID)).get()
			#construct search link
			searchURL = '/books/' + targBook.key.urlsafe()
			errorFlag = True
			for i in range(0,len(targCust.checked_out),1):
				if targCust.checked_out[i] == searchURL:
					targCust.checked_out.remove(searchURL)
					targBook.checkedIn = True
					targBook.put()
					targCust.put()
					errorFlag = False
			if errorFlag:
				self.response.status_int = 400
				self.response.status_message = 'Client Error'
				self.response.out.write("Client Error 1")
		else:
			self.response.status_int = 400
			self.response.status_message = 'Client Error'
			self.response.out.write("Client Error 2")

class LoginHandler(webapp2.RequestHandler):
	def get(self):
		#if user exists, wipe it out and start with one user (single user system)
		testquery = User.query().fetch()
		if len(testquery) >= 1 :
			for user in testquery:
				user.key.delete()
		#construct onetime state secret
		state = hashlib.sha256(os.urandom(1024)).hexdigest()
		new_user = User(stateXSRF=state)
		new_user.put()
		#url = "https://www.google.com"
		url = "https://accounts.google.com/o/oauth2/v2/auth?response_type=code&client_id=" + clientId + "&redirect_uri=" + redirectUri + "&scope=email&state=" + state
		#result = urlfetch.fetch(url)
		#self.response.write(url)
		return self.redirect(url)

class OAuthHandler(webapp2.RequestHandler):
	def get(self):
		#pull the user out of the bin to gain crossreference to XSRF statement access
		userCollection = User.query().fetch()
		user_dict = userCollection[0].to_dict()
		if (userCollection[0].token == "Null"):
			#check that secrets match
			if (user_dict['stateXSRF'] == self.request.get('state')):
				data = {'code': self.request.get('code'),'client_id': clientId,'client_secret': clientSecret,'redirect_uri' : redirect2,'grant_type': 'authorization_code'}
				result = urlfetch.fetch(url='https://www.googleapis.com/oauth2/v4/token', payload=urllib.urlencode(data),method=urlfetch.POST,headers={"Content-Type":"application/x-www-form-urlencoded"})
				if (result.status_code == 200):
					result = json.loads(result.content)
					userCollection[0].token = result['access_token']
					userCollection[0].put()
				else:
					self.response.write(result.content)
			else:
				self.response.write("XSRF Detected. Authorization failed<br>")
				self.response.write(user_dict['stateXSRF'])
				self.response.write("<br>")
				self.response.write(self.request.get('state'))
		paramstring = "Bearer " + userCollection[0].token
		param = {"Authorization" : paramstring}
		response = urlfetch.fetch(url='https://www.googleapis.com/plus/v1/people/me',headers=param)
		if (response.status_code == 200):
			respField = json.loads(response.content)
			self.response.write("First name: ")
			self.response.write(respField['name']['givenName'])
			self.response.write("<br>Last name: ")
			self.response.write(respField['name']['familyName'])
			link = "<br>Link: <a href=" + respField['url'] + ">" + respField['url'] + "</a><br>"
			statestring = "State secret: " + userCollection[0].stateXSRF
			self.response.write(link)
			self.response.write(statestring)
		else:
			self.response.write(response.content)

class CustomerBooklistHandler(webapp2.RequestHandler):
	def get(self,id=None):
		targCust = (ndb.Key(urlsafe=id)).get()
		self.response.write(json.dumps(targCust.checked_out))


allowed_methods = webapp2.WSGIApplication.allowed_methods
new_allowed_methods = allowed_methods.union(('PATCH',))
webapp2.WSGIApplication.allowed_methods = new_allowed_methods
app = webapp2.WSGIApplication([
    ('/' , MainPage),
    ('/login',LoginHandler),
    ('/oauth', OAuthHandler),
    ('/customers/(.*)/books/(.*)' , CheckoutHandler),
    ('/customers/(.*)/books', CustomerBooklistHandler),
    ('/customers' , CustomerHandler),
    ('/customers/(.*)' , CustomerHandler),
    ('/books' , BookListHandler),
    ('/books/(.*)' , BookListHandler)
], debug=True)
