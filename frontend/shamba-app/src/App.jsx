import { useState } from 'react'
import {BrowserRouter, Routes, Route } from "react-router-dom"
import Navbar from './features/navbar/navbar'
import ChatDisplay from './features/chat/components/Chat'
import Dashboard from './features/dashboard/components/dashboard'

import '../src/style/chat.css'
import '../src/style/dashboard.css'
import './App.css'

function App() {
  const [count, setCount] = useState(0)

  return (
    <>
      <section id="center">
        <div className="hero">
        </div>
        <div>
          <h1>Shamba App</h1>
        </div>
         <BrowserRouter>
            <Navbar />

            <Routes>
                <Route path="/" element={<Dashboard />} />
                <Route path="/chat" element={<ChatDisplay />} />
            </Routes>
        </BrowserRouter>
      </section>

      <div className="ticks"></div>
                      
      <section id="spacer"></section>
    </>
  )
}

export default App
