import { useState, useRef } from "react";

function ChatInput({ onSend }) {
    const [text, setText] = useState("");
    const [isRecording, setIsRecording] = useState(false);
    const [isTranscribing, setIsTranscribing] = useState(false);

    const mediaRecorderRef = useRef(null);
    const audioChunksRef = useRef([]);

    const handleSubmit = (event) => {
        event.preventDefault();
        if (!text.trim()) return;
        onSend(text);
        setText("");
    };

    const startRecording = async () => {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            const mediaRecorder = new MediaRecorder(stream);
            mediaRecorderRef.current = mediaRecorder;
            audioChunksRef.current = [];

            mediaRecorder.ondataavailable = (event) => {
                if (event.data.size > 0) {
                    audioChunksRef.current.push(event.data);
                }
            };

            mediaRecorder.onstop = async () => {
                const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm' });
                await handleTranscribe(audioBlob);
            };

            mediaRecorder.start();
            setIsRecording(true);
        } catch (error) {
            console.error("Error accessing microphone:", error);
            alert("Ntabwo bibaye gukunda gukoresha mikoro. (Microphone access denied.)");
        }
    };

    const stopRecording = () => {
        if (mediaRecorderRef.current && isRecording) {
            mediaRecorderRef.current.stop();
            setIsRecording(false);
            mediaRecorderRef.current.stream.getTracks().forEach(track => track.stop());
        }
    };

    const handleTranscribe = async (audioBlob) => {
        setIsTranscribing(true);
        try {
            console.log("Audio blob ready to send:", audioBlob);
            alert("Ijwi ryafashwe neza! (Audio recorded successfully!)");
        } catch (error) {
            console.error("Transcription error:", error);
            alert("Habaye ikibazo mu kwandika ijwi. (There was a problem transcribing the audio.)");
        } finally {
            setIsTranscribing(false);
        }
    };

    return (
        <div className="chatInput">
            <form className="chat-form" onSubmit={handleSubmit}>
                <button
                    type="button"
                    className={`mic-btn ${isRecording ? 'recording' : ''}`}
                    onClick={isRecording ? stopRecording : startRecording}
                    disabled={isTranscribing}
                    title={isRecording ? "Hagarika (Stop)" : "Vuga (Record)"}
                >
                    {isTranscribing ? "⏳" : "🎙️"}
                </button>

                <input
                    type="text"
                    name="text"
                    placeholder={isRecording ? "Ndi kumva... (Recording...)" : isTranscribing ? "Ndi kwandika... (Transcribing...)" : "Andika hano... (Type here...)"}
                    value={text}
                    onChange={(event) => setText(event.target.value)}
                    disabled={isRecording || isTranscribing}
                />

                <button
                    type="submit"
                    aria-label="Submit"
                    disabled={isRecording || isTranscribing || !text.trim()}
                ></button>
            </form>
        </div>
    );
}

export default ChatInput;