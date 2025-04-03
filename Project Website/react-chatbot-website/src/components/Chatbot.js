import React, { useState } from 'react';
import axios from "axios";
import './Chatbot.css';

function Chatbot() {
    // state objects

    // messageHistory will store items of the format {user: 'some_user', message: 'some_text'}
    // 2 users: user and chatBot
    const [messageHistory, setMessageHistory] = useState([]);

    // userInput will just be text of the user messages 'some_text'
    const [userInput, setUserInput] = useState("")

    const sendUserMessage = async () => {
        const userMessage = {user: "You", message: userInput};

        // append message to history
        setMessageHistory([...messageHistory, userMessage]);
        
        // do REST API request with user input
        const response = await axios.post("http://localhost:5005/webhooks/rest/webhook", userMessage);

        //response will be an array of messages; add them to message history
        response.data.forEach((response) => {
            // receive response in the form of {recipient_id: 'default, text: 'bot_response_text'}
            setMessageHistory((prev) => [...prev, { user: "ScheduleFlyBot", message: response.text}]);
            console.log(messageHistory)
        });
    };

    return (
        <div>
            <div className = "chatWindow">
                {messageHistory.map((message) => (
                    <div>
                        <p><strong>{message.user}</strong>: {message.message} </p>
                    </div>
                ))}
            </div>

            <br></br>

            <input value={userInput} onChange={(e) => setUserInput(e.target.value)} />
            <button onClick={sendUserMessage}>Send Message</button>
        </div>
    );
}

export default Chatbot;