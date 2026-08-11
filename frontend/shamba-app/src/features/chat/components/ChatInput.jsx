import { useState } from "react";
function ChatInput({onSend}){
    const[text, setText] = useState("")

    const handleSubmit = (event) => {
        event.preventDefault();
        if(!text.trim()) return;
        onSend(text);
        setText("")


    }

    return(
        <>
        <div className="chatInput">
            <form className="chat-form" onSubmit={handleSubmit}>
                <input type="text" 
                name="text" 
                placeholder="Text Here" 
                value={text}  
                onChange={(event) => setText(event.target.value)}/>
                <button type="submit" arial-label="Submit">➤</button>
            </form>
        </div>
        </>
    )
}

export default ChatInput;