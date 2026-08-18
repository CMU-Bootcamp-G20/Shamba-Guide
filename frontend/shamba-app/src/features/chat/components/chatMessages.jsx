import AdviceAction from './AdviceAction';
import { useEffect, useRef } from 'react';

function ChatMessages({ messages }) {
    const messagesEndRef = useRef(null);

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    };

    useEffect(() => {
        scrollToBottom();
    }, [messages]);

    return (
        <div className="chat-messages">
            {messages.length === 0 && (
                <div className="empty-chat-state">
                    <h2>Muraho! (Hello!) 🌾</h2>
                    <p>Baza ikibazo cy'ubuhinzi cyangwa indwara z'ibihingwa. (Ask an agricultural question or about crop diseases.)</p>
                </div>
            )}

            {messages.map((message) => (
                <div key={message.id} className={`message-wrapper ${message.role}`}>
                    <div className="message-bubble">
                        <div className="message-content">
                            {message.content}
                        </div>

                        {message.role === "assistant" && message.actions && message.actions.length > 0 && (
                            <div className="evidence-container">
                                {message.actions.map((action) => (
                                    <AdviceAction key={action.action_id} action={action} />
                                ))}
                            </div>
                        )}
                    </div>
                </div>
            ))}
            <div ref={messagesEndRef} />
        </div>
    );
}

export default ChatMessages;