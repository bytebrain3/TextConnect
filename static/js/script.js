
$(document).ready(function() {
	const socket = io();
	let typing = false;
	let typingTimeout;
	let is_room = false;
	let cname = $("#current_name").text();
	const user = $("#user").text();

	let new_user = ""
	let in_room = false

	const skip_button = 'https://firebasestorage.googleapis.com/v0/b/dipxplore.appspot.com/o/App%2Fskip.svg?alt=media&token=21539720-dcff-46d2-8c57-2e1f2be611f1';
	const loading_button = 'https://firebasestorage.googleapis.com/v0/b/dipxplore.appspot.com/o/App%2Fb4d657e7ef262b88eb5f7ac021edda87.gif?alt=media&token=b085235a-5886-4a7f-a849-95367299a3f4';
	
	
	
	$("textarea").on('input', function() {
		$(this).css('height', 'auto');
		$(this).css('height', Math.min(this.scrollHeight, 96) + 'px'); // Adjust 96px to your max-height
	});

	$("#send_message").on("click", function() {
		let message = $("#messageinput").val();
		if (message !== "") {
			socket.emit('message', { message: message, uid: $("#current_uid").text(), name: $("#current_name").text() });
			$("#messageinput").val('');
			scrollToBottom();
		}
	});
	
	function scrollToBottom() {
		const messagesContainer = $('#messages-container');
		messagesContainer.scrollTop(messagesContainer[0].scrollHeight);
	}

	socket.on('message', function(data) { 
		let htmlname = $("#current_name").text();

		let message_html = 
			data.name === htmlname 
			? `<li class="self-end bg-white dark:bg-white dark:text-black  p-2 max-w-xs max-h-auto rounded-tl-xl rounded-tr-xl rounded-bl-xl text-black">
					<span class="message-content">${data.message}</span>
				</li>`
			: `<li class="self-start bg-white text-black p-2 max-w-xs max-h-auto rounded-tl-xl rounded-tr-xl rounded-br-xl dark:bg-white dark:text-black">
					<span class="message-content">${data.message}</span>
				</li>`;
				
		$('#message_ul').append(message_html);
	});
	
	
	
	
	
	
	
	$('#message_input').on('input', function() {
			if (!typing) {
				typing = true;
				socket.emit("typing");
				clearTimeout(typingTimeout);
			}
			typingTimeout = setTimeout(stopTyping, 2000); // 2 seconds
		});

		function stopTyping() {
			typing = false;
			socket.emit("stop typing");
		}

		socket.on('display', function(data) {
			if (data.typing) {
				if ($("#ul").hasClass("hidden")) {
					$("#ul").removeClass("hidden");
				}
			} else {
				$('#ul').addClass('hidden');
			}
		});














	socket.on('connect', () => {
		alert("welcome")
		$("#img").attr('src', "https://firebasestorage.googleapis.com/v0/b/dipxplore.appspot.com/o/App%2Fglass%20(1).png?alt=media&token=2f4ff206-9f76-4a69-b1e5-6542a36a95b3");
	});

	socket.on('disconnect', () => {
		connect = false;
	});

	socket.on("join_room", function(data) {
		if (data.data) {
			if (data.data === "error") {
				alert("No users Online to create any room");
				$('#buttonImage').attr('src', skip_button);
				$('#toggleButton').prop('disabled', false);
			}
		}
	});
/*
	socket.on("user_leave_room", function(data) {
		in_room = data.in_room;
		if (data.data) {
			alert(data.data);
		}
		leaveRoom(); // Ensure the client leaves the room
	});*/
	
	socket.on("distroy", function(){
		leaveRoom()
	})

	socket.on("no_user", function(data) {
		alert(data.error);
	});

	socket.on('chat_started', function(data) {
		in_room = true
	
		if ($("#current_uid").text() === data.uid) {
			$('#friend_name').text(data.second_username);
			new_user = data.username
			
			
		} else {
			$('#friend_name').text(data.username);
			new_user = data.second_username
		}
		
		

		const notificationPanel = $('#notifications');
		$('#notification-message').html(`<strong>${new_user}</strong> has joined the room`);
		notificationPanel.removeClass('hidden');
		notificationPanel.addClass('animate-slideIn');
		setTimeout(() => {
			notificationPanel.removeClass('animate-slideIn');
			notificationPanel.addClass('hidden');
		}, 3000); // Duration to display the notification (3 seconds)

		$('#buttonImage').attr('src', skip_button);
		$('#toggleButton').prop('disabled', false); // Re-enable the button
	});

	function joinRoom() {
		$('#friend_name').text("")
		
		socket.emit('join', {name : cname});
	}

	function leaveRoom() {
		socket.emit("leave", {name : cname});
	}
	
	$("#toggleButton").click(function (){
		$('#buttonImage').attr('src', loading_button);
		$('#toggleButton').prop('disabled', true);
		if (in_room)
		{
			socket.emit("kick_all_user")
			in_room = false;
			
		}
		joinRoom()
		
	});
	/*

	let isOn = false;

	$('#toggleButton').click(function() {
		alert("burr")
		if (!isOn) {
			alert("search")
			isOn = true;
			$('#buttonImage').attr('src', loading_button);
			$('#toggleButton').prop('disabled', true); // Disable the button
			joinRoom();
		} else {
			isOn = false;
			leaveRoom();
			$('#buttonImage').attr('src', skip_button);
		}
	});*/
});
