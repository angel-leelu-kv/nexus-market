import { Routes, Route } from 'react-router-dom'
import { AnimatePresence } from 'framer-motion'
import Navbar from './components/Navbar'
import Footer from './components/Footer'
import AIChatbox from './components/AIChatbox'
import Home from './pages/Home'
import Browse from './pages/Browse'
import ListingDetail from './pages/ListingDetail'
import Compare from './pages/Compare'

function App() {
  return (
    <div className="app">
      <Navbar />
      <main className="main-content">
        <AnimatePresence mode="wait">
          <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/browse" element={<Browse />} />
            <Route path="/listing/:id" element={<ListingDetail />} />
            <Route path="/compare" element={<Compare />} />
          </Routes>
        </AnimatePresence>
      </main>
      <Footer />
      <AIChatbox />
    </div>
  )
}

export default App

