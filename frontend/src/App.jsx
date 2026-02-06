import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { Toaster } from 'react-hot-toast';
import { ThemeProvider } from './contexts/ThemeContext.jsx';
import Layout from './components/Layout.jsx';
import Dashboard from './pages/Dashboard.jsx';
import Documents from './pages/Documents.jsx';
import Templates from './pages/Templates.jsx';
import TemplateEditor from './pages/TemplateEditor.jsx';
import Projects from './pages/Projects.jsx';
import ProjectView from './pages/ProjectView.jsx';
import ReviewTable from './pages/ReviewTable.jsx';

function App() {
  return (
    <ThemeProvider>
      <Toaster
        position="top-right"
        toastOptions={{
          duration: 3000,
          style: {
            background: '#1e293b',
            color: '#f1f5f9',
            border: '1px solid #475569',
            borderRadius: '12px',
          },
          success: {
            iconTheme: { primary: '#10b981', secondary: '#f1f5f9' },
          },
          error: {
            iconTheme: { primary: '#ef4444', secondary: '#f1f5f9' },
          },
        }}
      />
      <BrowserRouter>
        <Layout>
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/documents" element={<Documents />} />
            <Route path="/templates" element={<Templates />} />
            <Route path="/templates/new" element={<TemplateEditor />} />
            <Route path="/templates/:id" element={<TemplateEditor />} />
            <Route path="/projects" element={<Projects />} />
            <Route path="/projects/:id" element={<ProjectView />} />
            <Route path="/projects/:id/review" element={<ReviewTable />} />
          </Routes>
        </Layout>
      </BrowserRouter>
    </ThemeProvider>
  );
}

export default App;
