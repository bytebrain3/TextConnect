import firebase_admin
from firebase_admin import credentials, auth, db
import random, hashlib, requests
from flask import Flask, render_template, jsonify, redirect, url_for, session, request
from flask_session import Session
from flask_socketio import SocketIO, send, emit, join_room, leave_room
import os

app = Flask(__name__)
app.config["SECRET_KEY"] = "aj Ami sob harano"
app.config['SESSION_TYPE'] = 'filesystem'
Session(app)

socketio = SocketIO(app)
databaseurl = os.getenv('url')

room_id = None
second_uid=None
second_sid=None 
first_user_sid=None

cred = credentials.Certificate("cred.json")
firebase_admin.initialize_app(cred, {
	"databaseURL": databaseurl
})

@app.route("/")
def index():
	if "user" in session:
		return redirect(url_for("chat_page"))
	return render_template("index.html")


@app.route('/ip_info/01100100_01100101_01110110_01101001_01101100')
def get_public_ip_info():
	if request.headers.getlist("X-Forwarded-For"):
		user_ip = request.headers.getlist("X-Forwarded-For")[0]
	else:
		user_ip = request.remote_addr
		api_url = f'http://ipinfo.io/{user_ip}/json'
		response = requests.get(api_url)
		ip_info = response.json()
		city = ip_info.get("city", "")
		country = ip_info.get("country", "")
		loc = ip_info.get("loc", "")
		
		return jsonify({"ip": user_ip, "city": city, "country": country, "loc": loc}), 200



@app.route('/submit-username', methods=['POST'])
def submit_username():
	data = request.get_json()
	username = data.get('username')

	try:
		user = auth.create_user(display_name=username)
	except Exception as e:
		return jsonify({"error": str(e)}), 400

	uid = user.uid

	try:
		response = requests.get(request.url_root + "ip_info/01100100_01100101_01110110_01101001_01101100")
		ip_info = response.json()
		ip = ip_info.get("ip", "")
		city = ip_info.get("city", "")
		country = ip_info.get("country", "")
		loc = ip_info.get("loc", "")
		
	except Exception as e:
		print(e)
		ip, city, country, loc = "", "", "", ""

	session["user"] = {
		"username": username,
		"uid": uid,
		"room_id" : None
	}

	ref = db.reference(f"Random_user_chat/user/{uid}")
	data = {
		"name": username,
		"ip": ip,
		"city": city,
		"country": country,
		"loc": loc,
		
		}
	ref.update(data)

	return jsonify({'message': f'{username} received successfully'})
	
	
@app.route("/chat_page")
def chat_page():
	if "user" not in session:
		return redirect(url_for('index'))
	uid = session["user"]["uid"]
	name = session["user"]["username"]
	return render_template('chat.html',uid = uid,name = name)




#_________________________ROUTE FINISH __________________________
def try_to_match(waiting_users, waiting_user_len):
	global room_id,second_uid,first_user_sid,second_sid
	try:
		uid = session["user"]["uid"]
		if not isinstance(waiting_users, dict):
			raise ValueError("waiting_users should be a dictionary")
			#handel_leave_room()
	
		user_list = list(waiting_users.values())
		if waiting_user_len <= 1:
			#handel_leave_room()
			emit("no_user", {
				"error": "No user online to talk with them"
		}, to=request.sid) #""
			raise IndexError("Not enough users to match")
			
	
		second_user = user_list[waiting_user_len - 1]
	
		if uid == second_user['uid']:
			second_user = user_list[waiting_user_len - 2]
		if uid == second_user:
			emit("no_user", {
				"error": "No user online to talk with them"
		}, to=request.sid) #"
	
		second_sid = second_user["sid"]

		second_uid = second_user["uid"]
		
			
		db.reference(f"Random_user_chat/waiting_user/{second_uid}").delete()
		db.reference(f"Random_user_chat/waiting_user/{uid}").delete()
	
		room_id = hashlib.sha256(f"{uid}{second_uid}".encode()).hexdigest()
	
		db.reference("Random_user_chat/").update({
			"active_rooms": {
				room_id: {
					"users": [uid, second_uid]
				}
			}
		})
		#session["active_rooms"][room_id]["users"] = [uid, session_uid]
			
			
		first_user_sid = waiting_users[uid]["sid"]
		
		join_room(room_id, sid=first_user_sid)
		join_room(room_id, sid=second_sid)
		update_both_ref ={
			"is_room": True,
			"room_id": room_id,
		}
		
		
		sec_ref = db.reference(f"Random_user_chat/user/{second_uid}")
		fir_ref = db.reference(f"Random_user_chat/user/{uid}")
		sec_ref.update(update_both_ref)
		fir_ref.update(update_both_ref)
		
		
		
		second_user_info = db.reference(f"Random_user_chat/user/{second_uid}").get()
		if second_user_info and "name" in second_user_info:
			pass
		return second_user_info["name"], room_id
	except Exception as e:
		print(f"An error occurred: {e}")


#_________________________FUNCTION FINISH _________________________
@socketio.on("connect")
def build_connection():
	if "user" in session:
		uid = session["user"]["uid"]
		username = session["user"]["username"]
		data = {"uid": uid}
		ref = db.reference(f"Random_user_chat/online/{uid}")
		ref.set(data)
		waiting_user = db.reference(f"Random_user_chat/waiting_user/{uid}")
				
		waiting_user.set(
			{
			"uid": session["user"]["uid"],
			"sid": request.sid
			}
		)
@socketio.on("disconnect")
def break_connention():
	global room_id,second_uid
	if "user" in session:
		uid = session["user"]["uid"]
		ref = db.reference(f"Random_user_chat/online/{uid}")
		ref.delete()
				
		waiting_user = db.reference(f"Random_user_chat/waiting_user/{uid}")
		if waiting_user:
			waiting_user.delete()
				
				
		ref = db.reference(f"Random_user_chat/active_rooms/{room_id}")
		ref.delete()
		room_id = ""
		second_uid = ""
		print("Client disconnected",room_id)
		update_both_ref ={
			"is_room": False,
			"room_id": None,
		}
		
		
		sec_ref = db.reference(f"Random_user_chat/user/{second_uid}")
		fir_ref = db.reference(f"Random_user_chat/user/{uid}")
		sec_ref.update(update_both_ref)
		fir_ref.update(update_both_ref)

@socketio.on("join")
def join(data):
	try:
		username = session["user"]["username"]
		uid = session["user"]["uid"]
		
		
		waiting_users = db.reference("Random_user_chat/waiting_user").get()
		
		waiting_user_len = len(waiting_users)
		
		if waiting_user_len >= 2:
			
			try:
				second_username, room_id = try_to_match(waiting_users, waiting_user_len)

				
				if second_username:
					print(second_username)
					
					emit('chat_started',
						{
							"room": room_id,
							"second_username": second_username,
							"username": username,
							"uid": uid,
							"in_room" : True,
						}, to=room_id)
					return
			except Exception as e:
				print(e)
		else:
			emit("join_room", {"data": "error", "message": "User not in session"}, to=request.sid)
	except Exception as e:
		print(f"Error in join: {e}")  # Replace with proper logging in production
		emit("join_room", {"data": "error", "message": "An unexpected error occurred"}, to=request.sid)





@socketio.on("leave")
def handel_leave_room(data):
	global room_id, second_uid,first_user_sid,second_sid
	if "user" in session:
		uid = session["user"]["uid"]
		
		waiting_user = db.reference(f"Random_user_chat/waiting_user/{uid}").update({
			"uid": uid,
			"sid": first_user_sid
		})
		
		waiting_user = db.reference(f"Random_user_chat/waiting_user/{second_uid}").update({
			"uid": second_uid,
			"sid": second_sid
		})
		
		
		
		print("leave the room \n\n", room_id,"\n\n\n")
		
		
		
		
		leave_room(room_id)
		update_both_ref ={
			"is_room": False,
			"room_id": None,
		}
		
		
		sec_ref = db.reference(f"Random_user_chat/user/{second_uid}")
		fir_ref = db.reference(f"Random_user_chat/user/{uid}")
		sec_ref.update(update_both_ref)
		fir_ref.update(update_both_ref)
		
		
		
		
		
		
		emit("user_leave_room", {"in_room": False,"data": f'{data["name"]} has left the room.'}, to=room_id)
		ref = db.reference(f"Random_user_chat/active_rooms/{room_id}")
		ref.delete()
		print("leave")

		# Clear global variables after use
		room_id = ""
		second_uid = ""
		first_user_sid,second_sid = "" ,""



@socketio.on('typing')
def handle_typing():
	global room_id
	print("typing ..... ")
	emit('display', {'typing': True}, room=room_id)

@socketio.on('stop typing')
def handle_stop_typing():
	global room_id
	print("typing stop")
	emit('display', {'typing': False}, room=room_id)


"""

@socketio.on("typing")
def handle_typing():
	global room_id
	emit('display', True, to=room_id)

@socketio.on("stop typing")
def handle_stop_typing():
	global room_id
	emit('display', False, to=room_id)

"""
@socketio.on("kick_all_user")
def kick_all():
	emit("distroy",to=room_id)

@socketio.on("message")
def handle_message(data):
	global room_id,second_sid
	
	try:
		message = data["message"]
		uid = data["uid"]
		name = data["name"]
		
		send_back = {
			"message" : message,
			"uid" : uid,
			"name": name,
			
		}
		print("NAME : ",send_back)
	
		sec_ref = db.reference(f"Random_user_chat/user/{second_uid}"). get()
		fir_ref = db.reference(f"Random_user_chat/user/{second_uid}").get()
		
		if sec_ref["is_room"] and fir_ref["is_room"]:
			send(send_back, room = sec_ref["room_id"])
		else:
			if uid == session["user"]["uid"]:
				send("no user in room to talk " , to = request.sid)
			else:
				send("no user in room to talk " , to = second_sid)
	except Exception as e :
		print(e)





def listener(event):
	data = event.data
	print(f"Data: {event.data}")

	# Check if data is a dictionary and iterate over items
	if isinstance(data, dict):
		keys_to_remove = [key for key, value in data.items() if value == ""]
		
		# Handle nested dictionaries
		for key, value in data.items():
			if isinstance(value, dict):
				# Check nested dictionaries for empty values
				for nested_key, nested_value in value.items():
					if nested_value == "":
						keys_to_remove.append(key)
						break

		# Remove the identified keys from the database
		for key in keys_to_remove:
			ref.child(key).delete()
		if list(data.items())[0][0] == "sid" or "uid":
			ref.child(key).delete()


ref = db.reference("Random_user_chat/waiting_user/")
ref.listen(listener)


if __name__ == "__main__":
	socketio.run(app,port="8080",host="0.0.0.0")
