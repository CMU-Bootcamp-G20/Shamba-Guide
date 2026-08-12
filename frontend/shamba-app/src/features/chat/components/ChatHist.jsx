function ChatHistory() {

    const chats = [
        "Wilting in Tomato plants",
        "Yellowing of maize leaves",
        "What's the best season for beans planting ",
    ];

    return (
        <aside className="chat-history">
            <button className="new-chat">
               <span> + </span>New Chat
            </button>

            <h3>Recent chats</h3>

            <ul>
                {chats.map((chat, index) => (
                    <li key={index}>
                        {chat}
                    </li>
                ))}
            </ul>

        </aside>
    );
}

export default ChatHistory;