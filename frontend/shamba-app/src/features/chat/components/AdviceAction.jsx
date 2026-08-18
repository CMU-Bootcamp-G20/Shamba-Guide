import { useState } from 'react';

export default function AdviceAction({ action }) {
    const [loadingAudio, setLoadingAudio] = useState(false);

    const handlePlayAudio = async () => {
        setLoadingAudio(true);
        try {
            const response = await fetch('http://127.0.0.1:8002/api/v1/tts', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Accept': 'audio/wav',
                },
                body: JSON.stringify({
                    text: action.text,
                    speaker_id: 0 
                }),
            });

            if (!response.ok) {
                throw new Error("Failed to fetch audio from the server.");
            }

            const blob = await response.blob();
            const audioUrl = URL.createObjectURL(blob);
            const audio = new Audio(audioUrl);
            audio.play();

        } catch (error) {
            console.error("Audio playback error:", error);
            alert("Habaye ikibazo mu gucuranga ijwi. Ndagusabye wongere ugerageze. (There was a problem playing the audio. Please try again.)");
        } finally {
            setLoadingAudio(false);
        }
    };

    return (
        <div className="advice-action-card">
            <p className="advice-text">{action.text}</p>
            
            <button 
                className={`audio-btn ${loadingAudio ? 'loading' : ''}`}
                onClick={handlePlayAudio}
                disabled={loadingAudio}
            >
                {loadingAudio ? (
                    <><span className="spinner">⏳</span> Itegeka ijwi... (Preparing voice...)</>
                ) : (
                    <><span className="icon">🔊</span> Umva Amagambo (Listen to Audio)</>
                )}
            </button>
        </div>
    );
}