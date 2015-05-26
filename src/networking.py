#!python
print("Importing and configuring base modules (datetime,sys)..."),
from datetime import datetime
import sys
def log(text):
	text2="[%s - server] %s" % ((str(datetime.now())),text)
	sys.stdout.write(text2)
print("Done!")
log("Loading twisted.internet.reactor,protocol,endpoints...\n")
from twisted.internet import reactor, protocol, endpoints
log("Done!\n")
log("Loading twisted.protocols.basic...\n")
from twisted.protocols import basic
log("Done!\n")
log("Loading game libraries...\n")
import libadventure
import libgameloader
import libitems
log("Done!\n")
log("Loading json...\n")
import json
log("Done!\n")
log("Loading usercontrol.json...\n")
userfp=open("usercontrol.json","r+")
usercontrol_json=json.load(userfp)
userfp.seek(0)
print(usercontrol_json)
log("Done!\n")
room1=libadventure.Room("Spawn","You are in a plain nondescript room with a single bare lightbulb hanging from the ceiling. A dark and forbidding hallway leads west out of the room.",west="Dark Hallway",contents={"a nasty-looking stiletto knife":libitems.Item("a nasty-looking stiletto knife","A well-crafted but nasty-looking blade with an ivory handle. It is about five inches long, very thin, and tapers to a wickedly sharp point.",properties={"type":"weapon","stance":"dagger","damage":"10"})})
world=libadventure.World(room1)
roomloader=libgameloader.RoomLoader("rooms.list",world)
class GameProtocol(basic.LineReceiver):
	def __init__(self, factory):
		self.factory = factory
		self.state=""
	def connectionMade(self):
		self.factory.clients.add(self)
		self.state="MENU"
		self.sendLine("""
Welcome to the incredible PyMuddy!\r
1) If you have been here before, log in!\r
2) Otherwise, register an account!\r
Enter your choice > \r
		""".encode('utf8'))
		self.peer=self.transport.getPeer()
		log("Connection recieved from %s\n" % str(self.transport.getPeer()))
		log("Sent menu to %s\n" % str(self.transport.getPeer()))
	def connectionLost(self, reason):
		try:
			world.remove_player(self.username)
		except:
			log('Warning - error removing disconnected player!\n')
		log("Connection lost from %s\n" % str(self.peer))
		for c in self.factory.clients:
			if c!=self:
				c.sendLine(b'%s has left the game\r' % self.username.encode('utf8'))
		try:
			del self.player
		except:
			pass
		self.factory.clients.remove(self)
	def saytoeveryone(self,text):
		for c in self.factory.clients:
				if c!=self:
					c.sendLine(text.encode('utf8'))
	def lineReceived(self, line):
		log("Recieved line \n%s\n from client %s" % (line.decode('utf8'),str(self.transport.getPeer())))
		if self.state=="MENU":
			if line.decode('utf8')=="1":
				self.sendLine("Username > ")
				self.state="USERLOGIN1"
				return
			if line.decode('utf8')=="2":
				self.sendLine("\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n")
				self.sendLine("Please enter a username > ".encode('utf8'))
				self.state="CREATEACCOUNT1"
				return
		if self.state=="PLAYING":
			if line.decode('utf8')[0:3]=="say":
				for c in self.factory.clients:
					if c!=self:
						c.sendLine(("%s>%s" % (self.username,line.decode('utf8')[3:])).encode('utf8'))
			else:
				self.sendLine(world.process_command(line.decode('utf8'),self.username,self.factory,self.username).encode('utf8'))
		if self.state=="USERLOGIN1":
			usercontrol_json=json.load(userfp)
			userfp.seek(0)
			data=usercontrol_json[u'logins']
			if line.decode('utf8') in world.players:
				self.sendLine("That user is already logged in!\n\r")
				self.state="MENU"
				self.sendLine("""
Welcome to the incredible PyMuddy!\r
1) If you have been here before, log in!\r
2) Otherwise, register an account!\r
Enter your choice (1,2) >\r
				""".encode('utf8'))
				return
			for i,x in enumerate(data):
				if x[u'username']==unicode(line.decode('utf8')):
					self.username=x[u'username'.encode('utf8')]
					self.password_correct=x[u'password']
					log(self.password_correct+"\n")
					self.i=i
					self.username=line.decode('utf8')
					self.sendLine(b'Password > ')
					self.state="USERLOGIN2"
					return
			self.sendLine("Bad username")
			self.state="MENU"
			self.sendLine("""
Welcome to the incredible PyMuddy!\r
1) If you have been here before, log in!\r
2) Otherwise, register an account!\r
Enter your choice (1,2) >\r
		""".encode('utf8'))
			return
		if self.state=="USERLOGIN2":
			usercontrol_json=json.load(userfp)
			userfp.seek(0)
			data=usercontrol_json[u'logins']
			if line.decode('utf8')==self.password_correct:
				self.sendLine(b"Login sucessful. Please press enter to continue.\r\n")
				self.state="PLAYING"
				self.sendLine(b'Welcome, %s\r\n!' % self.username.encode('utf8'))
				for c in self.factory.clients:
					if c!=self:
						c.sendLine(b'%s has joined the game\r!' % self.username.encode('utf8'))
				log("Client at %s gave username %s, logged in\n" % (self.peer,self.username))
				new_player=libadventure.Player(self.username)
				new_player.thing=self
				self.player=new_player
				world.add_player(new_player)
				self.sendLine(world.process_command('look',self.username,self.factory).encode('utf8'))
				self.state="PLAYING"
				return
			else:
				self.sendLine(b"Bad password\r\n")
				self.state="MENU"
				self.sendLine(b'''
Welcome to the incredible PyMuddy!\r
1) If you have been here before, log in!\r
2) Otherwise, register an account!\r
Enter your choice (1,2) > \r
				''')
		if self.state=="CREATEACCOUNT1":
			usercontrol_json=json.load(userfp)
			userfp.seek(0)
			data=usercontrol_json[u'logins']
			for x in data:
				test=x[u'username']
				check=line.decode('utf8')
				check2=unicode(check)
				if test==check2:
					self.sendLine(b"Username taken already, sorry :(\r\n")
					self.state="MENU"
					self.sendLine(b'''
Welcome to the incredible PyMuddy!\r
1) If you have been here before, log in!\r
2) Otherwise, register an account!\r
Enter your choice (1,2) > \r
					''')
					return
				if test=="\n" or test=="\n\r" or test==" " or " " in test:
					self.sendLine(b"Bad username. Spaces are not allowed\r\n")
					self.state="MENU"
					self.sendLine(b'''
Welcome to the incredible PyMuddy!\r
1) If you have been here before, log in!\r
2) Otherwise, register an account!\r
Enter your choice (1,2) > \r
					''')
					return
			self.create_name=unicode(line.decode('utf8'))
			self.sendLine("\n\rPlease enter your password below\n\rThis will be sent as unencrypted plaintext, so make sure it's something new that isn't important\n\rPassword > \n\r")
			self.state="CREATEACCOUNT2"
			return
		if self.state=="CREATEACCOUNT2":
			self.create_password=line
			usercontrol_json=json.load(userfp)
			userfp.seek(0)
			usercontrol_json[u'logins'].append({"username":unicode(self.create_name),"password":unicode(self.create_password)})
			self.sendLine("\n\rThanks for creating an account.\n\rNow log in at the main menu\n\r")
			self.state="MENU"
			self.sendLine(b'''
Welcome to the incredible PyMuddy!\r
1) If you have been here before, log in!\r
2) Otherwise, register an account!\r
Enter your choice (1,2) > \r
			''')
			json.dump(usercontrol_json,userfp)
			userfp.seek(0)
			return

class GameFactory(protocol.Factory):
	def __init__(self):
		self.clients = set()

	def buildProtocol(self, addr):
		return GameProtocol(self)

endpoints.serverFromString(reactor, "tcp:1234").listen(GameFactory())
reactor.run()