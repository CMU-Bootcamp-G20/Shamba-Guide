import { useEffect, useState } from "react";
import { getChats } from "../../../services/chatApi";

function ChatHistory({ onSelectChat }) {
    const [chats, setChats] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState("");

    useEffect(() => {
        async function loadChats() {
            try {
                const data = await getChats();
                // Depending on your API, data might be the array itself or inside data.chats
                setChats(data.chats || data);
            } catch (error) {
                console.error("Error loading chats:", error);
                setError("Ntabwo bibaye gukunda kuzana amateka. (Unable to load chat history.)");
            } finally {
                setLoading(false);
            }
        }
        loadChats();
    }, []);

    if (loading) {
        return <p style={{ padding: '24px', color: '#6b7280' }}>⏳ Ndi gushaka... (Loading chats...)</p>;
    }

    if (error) {
        return <p style={{ padding: '24px', color: '#ef4444' }}>{error}</p>;
    }

    return (
        <aside className="chat-history">
            <div id="new-chatbtn">
                <a href="/chat">
                    <span>+</span> Ikiganiro Gishya (New Chat)
                </a>
            </div>
            
            <h3>Ibiganiro bya vuba (Recent chats)</h3>
            
            <ul>
                {chats && chats.map((chat) => (
                    <li
                        key={chat.conversation_id || chat.id}
                        onClick={() => onSelectChat(chat.conversation_id || chat.id)}
                    >
                        {chat.title || "Ikiganiro (Chat)"}
                    </li>
                ))}
            </ul>
        </aside>
    );
}

export default ChatHistory;