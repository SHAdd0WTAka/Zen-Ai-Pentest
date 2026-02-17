import { Routes, Route } from 'react-router-dom'
import { Layout } from './components/Layout'
import { Dashboard } from './pages/Dashboard'
import { Scans } from './pages/Scans'
import { ScanDetails } from './pages/ScanDetails'
import { NewScan } from './pages/NewScan'
import { Tools } from './pages/Tools'
import { Reports } from './pages/Reports'
import { Settings } from './pages/Settings'
import { Login } from './pages/Login'
import { useAuthStore } from './store/authStore'

function App() {
  const { isAuthenticated } = useAuthStore()

  if (!isAuthenticated) {
    return <Login />
  }

  return (
    <Layout>
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/scans" element={<Scans />} />
        <Route path="/scans/new" element={<NewScan />} />
        <Route path="/scans/:id" element={<ScanDetails />} />
        <Route path="/tools" element={<Tools />} />
        <Route path="/reports" element={<Reports />} />
        <Route path="/settings" element={<Settings />} />
      </Routes>
    </Layout>
  )
}

export default App