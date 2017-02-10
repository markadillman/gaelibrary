import webapp2
import snippets
import json
import urllib2
import os
import hashlib
from google.appengine.ext import ndb
from google.appengine.api import urlfetch

clientId = "867857451041-alogqb26a4uiusrf3ou1lc4ja3co7vr8.apps.googleusercontent.com"
clientSecret = "s6aKP4UNC15g72nKCvLJlpVZ"
redirectUri = "https://www.library-157519.appspot.com/showuser"

class User(ndb.Model):
	fName = ndb.StringProperty()
	lName = ndb.StringProperty()
	stateXSRF = ndb.StringProperty()
	token = ndb.StringProperty()

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

class OAuthHandler(webapp2.RequestHandler):
	def get(self):
		#construct onetime state secret
		state = hashlib.sha256(os.urandom(1024)).hexdigest()
		new_user = User(stateXSRF=state)
		new_user.put
		url = 'https://www.accounts.google.com/o/oauth2/v2/auth?response_type=code&client_id=' + clientId + '&redirect_uri=' + redirectUri + '&scope=email&state=' + state
		result = UrlFetchApp.fetch(url)
		self.response.write(result)

class UserHandler(webapp2.RequestHandler):
	def post(self):
		#pull the user out of the bin to gain crossreference to XSRF statement access
		userCollection = User.query()
		user_dict = userCollection[1].to_dict
		self.response.write(user_dict['stateXSRF'])

class CustomerBooklistHandler(webapp2.RequestHandler):
	def get(self,id=None):
		targCust = (ndb.Key(urlsafe=id)).get()
		self.response.write(json.dumps(targCust.checked_out))


allowed_methods = webapp2.WSGIApplication.allowed_methods
new_allowed_methods = allowed_methods.union(('PATCH',))
webapp2.WSGIApplication.allowed_methods = new_allowed_methods
app = webapp2.WSGIApplication([
    ('/' , MainPage),
    ('/oauth', OAuthHandler),
    ('/showuser', UserHandler),
    ('/customers/(.*)/books/(.*)' , CheckoutHandler),
    ('/customers/(.*)/books', CustomerBooklistHandler),
    ('/customers' , CustomerHandler),
    ('/customers/(.*)' , CustomerHandler),
    ('/books' , BookListHandler),
    ('/books/(.*)' , BookListHandler)
], debug=True)
