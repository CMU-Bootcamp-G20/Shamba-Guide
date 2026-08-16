import axios from "axios";

const API_URL = "http://localhost:8000";

export async function sendMessage({
    sessionId,
    question,
    crop,
    district,
    sector,
    language = "rw",
    channel = "web"
}) {

        try {
        const payload = {
        session_id: sessionId,
        question,
        crop,
        district,
        sector,
        language,
        channel
            };

    console.log("Sending payload:", payload);


        const response = await axios.post(
            `${API_URL}/api/v1/advice`, payload
        );

        return response.data;

    } catch (error) {

        if (error.response) {

            console.error(
                "Backend responded with:",
                error.response.status,
                error.response.data
            );

        } else if (error.request) {

            console.error(
                "No response from backend"
            );

        } else {

            console.error(
                "Request failed:",
                error.message
            );
        }

        throw error;
    }
}


export async function getChats() {
    try {
        const response = await axios.get(
            `${API_URL}/api/v1/chats`
        );

        console.log("Chats:", response.data);

        return response.data;

    } catch (error) {
        console.error(
            "Failed to retrieve chats:",
            error.response?.data || error.message
        );

        throw error;
    }
}

export async function getChat(conversationId) {

    try {

        const response = await axios.get(
            `${API_URL}/api/v1/chats/${conversationId}`
        );

        console.log("Conversation:", response.data);

        return response.data;

    } catch (error) {

        console.error(
            "Failed to retrieve conversation:",
            error.response?.data || error.message
        );

        throw error;
    }
}

export async function getAnalytics() {
    try {
        const response = await axios.get(
            `${API_URL}/api/v1/analytics`
        );
        console.log("Analytics:", response.data);

        return response.data;
    } catch (error) {
        console.error(
            "Failed to retrieve analytics:",
            error.response?.data || error.message
        );
        throw error;
    }
}