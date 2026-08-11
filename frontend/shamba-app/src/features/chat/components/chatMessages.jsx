function ChatMessages({messages}){
    return(
     <div className="chat-messages">
        {messages.map((message) => (
             <div
              key={message.id}
              className={`message ${message.role}`}>
                {message.content}
            </div>

        ))}
        </div>
      
    )
}

export default ChatMessages;