import { BrowserRouter, Routes, Route } from "react-router-dom";
import Navbar from './features/navbar/navbar';
import ChatDisplay from './features/chat/components/Chat';
import Dashboard from './features/dashboard/components/dashboard';
import '../src/style/chat.css';
import '../src/style/dashboard.css';
import './App.css';

function App() {
  return (
    <BrowserRouter>
      <div className="app-container">
        <Navbar />
        
        <main className="main-content">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/chat" element={<ChatDisplay />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  );
}

export default App;