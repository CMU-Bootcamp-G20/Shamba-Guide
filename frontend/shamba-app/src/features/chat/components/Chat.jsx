import { useState } from "react";
import ChatHistory from "./ChatHist";
import ChatInput from "./ChatInput";
import ChatMessages from "./chatMessages";
import { sendMessage } from "../../../services/chatApi";


function ChatDisplay(){
    const[messages, setMessages] = useState([])
    const [sessionId, setSessionId] = useState(null);
    const[isLoading, setIsLoading] = useState([])


     const handleSendMessage = async (question) => {

        const currentSessionId =
            sessionId || crypto.randomUUID();
        setSessionId(currentSessionId);
        console.log("Current session ID:", currentSessionId);

        const userMessage = {
            id: crypto.randomUUID(),
            role: "user",
            content: question
        };

        setMessages((previousMessages) => [
            ...previousMessages,
            userMessage
        ]);

        setIsLoading(true);

        try {

            const response = await sendMessage({
                sessionId: currentSessionId,
                question: question,
                crop: "banana",
                district: "Bugesera",
                sector: "Nyamata",
                language: "rw",
                channel: "web"
            });

            console.log("Backend response:", response);

            const assistantMessage = {
                id: response.receipt_id,
                role: "assistant",
                content: response.message,
                status: response.status,
                actions: response.actions,
                warnings: response.warnings,
                sources: response.sources
            };

            setMessages((previousMessages) => [
                ...previousMessages,
                assistantMessage
            ]);

        } catch (error) {

            console.error("Failed to send message:", error);

        } finally {

            setIsLoading(false);
        }
    };

     const handleSelectChat = async (selectedSessionId) => {

        try {

            const conversation =
                await getChat(selectedSessionId);

            setSessionId(selectedSessionId);

            setMessages(
                conversation.messages
            );

        } catch (error) {

            console.error(
                "Failed to load conversation:",
                error
            );
        }
    };

    return (
        <>
        <div className="chat-page">
        <ChatHistory  
        onSelectChat={handleSelectChat}
        />
        <div className="chat-main">
            <ChatMessages messages={messages}/>
            <ChatInput 
            onSend={handleSendMessage}
            disabled={isLoading}
            />
        </div>
        </div>
        </>
    )
}

export default ChatDisplay;