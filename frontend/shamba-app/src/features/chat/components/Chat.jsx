import { useState } from "react";
import ChatHistory from "./ChatHist";
import ChatInput from "./ChatInput";
import ChatMessages from "./chatMessages";


function ChatDisplay(){
     const handleSendMessage = (text) => {

        const newMessage = {
            id: Date.now(),
            role: "user",
            content: text
        };

        setMessages((previousMessages) => [
            ...previousMessages,
            newMessage
        ]);
    };
    const[messages, setMessages] = useState([])
    return (
        <>
        <div className="chat-page">
        <ChatHistory/>
        <div className="chat-main">
            <ChatMessages messages={messages}/>
            <ChatInput onSend={handleSendMessage}/>
        </div>
        </div>
        </>
    )
}

export default ChatDisplay;