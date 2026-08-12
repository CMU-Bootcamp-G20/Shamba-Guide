## ShambaGuide: An AI Powered Agri-tech System for localized farming insights

## Description

Shamba Guide is a react.js appplication that provides a chatbot for farmers to interract and get AI-based agriculture advisories and recommendations. 
The application also provides a dashboard for agriculture stakeholders to understand what are the main pain-points that farmers are experiencing based on the frequency of questions asked. 

## Features
##### 1. Dashboard
##### 2. AI Chatbot
<img src="./frontend/shamba-app/src/assets/Screen1.png"/>

## Project Structure
<img src="./frontend/shamba-app/src/assets/DirectoryStructure.png"/>

## Prerequisites

<code>node version >= 22.0.1</code>


## Installation
To execute the react application follow the steps below: 

###### Step 1. git clone https://github.com/CMU-Bootcamp-G20/Shamba-Guide.git

###### Step 2. cd frontend/shamba-app

###### Step 3. npm install

###### Step 4. npm run dev 

## Dependencies
We expect the data below and endpoints from the backend

### A. Chat/AI endpoint

An endpoint that accepts a user's agricultural question and returns an AI-generated response.

POST /api/chat

The endpoint should:

<ul>
<li>Receive the user's message.</li>
<li>Accept a conversation_id when continuing an existing conversation.</li>
<li>Retrieve relevant conversation history if required.</li>
<li>Pass the question and required context to the AI model.</li>
<li>Receive the model response.</li>
<li>Store the user message and AI response.</li>
<li>Return the response to the frontend.</li>
</ul>

### B. Chat history endpoint

An endpoint for retrieving previous conversations for use on the ChatHistory component.

GET /api/chats

The endpoint should return:

<ul>
<li>Conversation_id</li>
<li>Conversation title or summary</li>
<li>Date/time of the latest message</li>
<li>Last message preview</li>
<li>Number of messages</li>
<li>Optional metadata such as crop, location, or topic</li>
</ul>

### C. Conversation endpoint

An endpoint for retrieving the messages belonging to a specific conversation.

GET /api/chats/{conversation_id}

The response should contain the messages in chronological order.

This allows the frontend to load an existing conversation when the user selects it from the sidebar.

### D. Dashboard analytics endpoint

An endpoint for aggregated chatbot analytics.


GET /api/chat/analytics

The endpoint should provide aggregated data such as:

<ul>
<li>Total number of questions</li>
<li>Number of active conversations</li>
<li>Most frequently asked questions/topics</li>
<li>Questions grouped by topic</li>
<li>Questions over time</li>
</ul>


## Sample Data Formats 
#### Conversation Input from user
{ "conversation_id": "conv_12345", "message": "What fertilizer should I use for maize?" }

#### Response 
{ "conversation_id": "conv_12345", "message": { "id": "msg_67890", "role": "assistant", "content": "AI-generated agricultural advisory...", "created_at": "2026-08-12T10:20:00Z" } }

## Next Steps

<ul>
<li>Design the data model for chats and messages</li>
<li>Design the APIs with all required fields</li>
</ul>







