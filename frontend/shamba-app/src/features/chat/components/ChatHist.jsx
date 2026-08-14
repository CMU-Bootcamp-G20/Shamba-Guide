import { useEffect, useState } from "react";
import { getChats } from "../../../services/chatApi";

function ChatHistory({onSelectChat}) {

    const [loading, setLoading] = useState([])
    const [error, setError] = useState('')

      useEffect(() => {

        async function loadChats() {

            try {

                const data = await getChats();

                setChats(data.chats);

            } catch (error) {

                setError("Unable to load chat history.");

            } finally {

                setLoading(false);
            }
        }

        loadChats();

    }, []);

    if (loading) {
        return <p>Loading chats...</p>;
    }

    if (error) {
        return <p>{error}</p>;
    }

    return (
        <aside className="chat-history">
        <div id="new-chatbtn">
            <a href="/chat">
               <span> + </span> New Chat
               </a>
               </div>
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