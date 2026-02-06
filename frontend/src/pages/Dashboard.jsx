import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { FileText, Layers, FolderKanban, Upload, Plus, ArrowRight, TrendingUp, CheckCircle } from 'lucide-react';
import Card from '../components/Card.jsx';
import { documentsApi, templatesApi, projectsApi } from '../api/index.js';

function StatCard({ label, value, icon: Icon, color, to }) {
  return (
    <Link to={to} className="glass rounded-2xl p-6 flex items-center gap-4 hover:bg-slate-800/70 transition-colors group">
      <div className={`w-14 h-14 rounded-xl flex items-center justify-center ${color}`}>
        <Icon className="w-7 h-7" />
      </div>
      <div>
        <p className="text-sm text-slate-400">{label}</p>
        <p className="text-3xl font-bold text-white">{value}</p>
      </div>
      <ArrowRight className="w-5 h-5 text-slate-500 ml-auto opacity-0 group-hover:opacity-100 transition-opacity" />
    </Link>
  );
}

function QuickAction({ label, description, icon: Icon, to }) {
  return (
    <Link to={to} className="flex items-center gap-4 p-4 rounded-xl hover:bg-slate-800/50 transition-colors group">
      <div className="w-10 h-10 rounded-lg bg-primary-500/20 flex items-center justify-center">
        <Icon className="w-5 h-5 text-primary-400" />
      </div>
      <div className="flex-1">
        <p className="font-medium text-white">{label}</p>
        <p className="text-sm text-slate-500">{description}</p>
      </div>
      <ArrowRight className="w-5 h-5 text-slate-500 opacity-0 group-hover:opacity-100 transition-opacity" />
    </Link>
  );
}

function Dashboard() {
  const [stats, setStats] = useState({ documents: 0, templates: 0, projects: 0 });
  const [recentProjects, setRecentProjects] = useState([]);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [docsRes, templatesRes, projectsRes] = await Promise.all([
          documentsApi.getAll(),
          templatesApi.getAll(),
          projectsApi.getAll(),
        ]);
        setStats({
          documents: docsRes.data.documents?.length || 0,
          templates: templatesRes.data.templates?.length || 0,
          projects: projectsRes.data.projects?.length || 0,
        });
        setRecentProjects(projectsRes.data.projects?.slice(0, 5) || []);
      } catch (err) {
        console.error('Failed to fetch dashboard data:', err);
      }
    };
    fetchData();
  }, []);

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-3xl font-bold text-white mb-2">Dashboard</h1>
        <p className="text-slate-400">Welcome to Legal Tabular Review. Extract and compare fields from legal documents.</p>
      </div>

      <div className="grid grid-cols-3 gap-6">
        <StatCard label="Documents" value={stats.documents} icon={FileText} color="bg-blue-500/20 text-blue-400" to="/documents" />
        <StatCard label="Templates" value={stats.templates} icon={Layers} color="bg-emerald-500/20 text-emerald-400" to="/templates" />
        <StatCard label="Projects" value={stats.projects} icon={FolderKanban} color="bg-purple-500/20 text-purple-400" to="/projects" />
      </div>

      <div className="grid grid-cols-2 gap-6">
        <Card>
          <h2 className="text-xl font-semibold text-white mb-4">Quick Actions</h2>
          <div className="space-y-2">
            <QuickAction label="Upload Documents" description="Add PDF or DOCX files" icon={Upload} to="/documents" />
            <QuickAction label="Create Template" description="Define extraction fields" icon={Plus} to="/templates/new" />
            <QuickAction label="Start New Project" description="Begin document review" icon={FolderKanban} to="/projects" />
          </div>
        </Card>

        <Card>
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-semibold text-white">Recent Projects</h2>
            <Link to="/projects" className="text-sm text-primary-400 hover:text-primary-300">View all</Link>
          </div>
          {recentProjects.length > 0 ? (
            <ul className="space-y-3">
              {recentProjects.map(project => (
                <li key={project.id}>
                  <Link to={`/projects/${project.id}`} className="flex items-center justify-between p-3 rounded-lg hover:bg-slate-800/50 transition-colors">
                    <div>
                      <p className="font-medium text-white">{project.name}</p>
                      <p className="text-sm text-slate-500">{project.document_count} documents</p>
                    </div>
                    <span className={`text-xs px-2 py-1 rounded-full ${project.status === 'completed' ? 'bg-emerald-500/20 text-emerald-400' : 'bg-slate-600/30 text-slate-300'}`}>
                      {project.status}
                    </span>
                  </Link>
                </li>
              ))}
            </ul>
          ) : (
            <div className="text-center py-8">
              <FolderKanban className="w-12 h-12 text-slate-600 mx-auto mb-3" />
              <p className="text-slate-400">No projects yet</p>
              <Link to="/projects" className="text-sm text-primary-400 hover:text-primary-300">Create your first project</Link>
            </div>
          )}
        </Card>
      </div>

      <Card>
        <h2 className="text-xl font-semibold text-white mb-6">How It Works</h2>
        <div className="grid grid-cols-4 gap-6">
          {[
            { step: 1, icon: Upload, label: 'Upload Documents', desc: 'Add your legal PDFs and DOCX files' },
            { step: 2, icon: Layers, label: 'Select Template', desc: 'Choose or create a field template' },
            { step: 3, icon: TrendingUp, label: 'Extract Fields', desc: 'AI extracts values with citations' },
            { step: 4, icon: CheckCircle, label: 'Review & Export', desc: 'Approve values and export results' },
          ].map(({ step, icon: Icon, label, desc }) => (
            <div key={step} className="relative">
              <div className="text-center">
                <span className="absolute -top-2 left-1/2 -translate-x-1/2 w-6 h-6 rounded-full bg-primary-500 text-white text-xs flex items-center justify-center font-bold">
                  {step}
                </span>
                <div className="w-14 h-14 rounded-xl bg-slate-800 flex items-center justify-center mx-auto mb-3">
                  <Icon className="w-6 h-6 text-slate-400" />
                </div>
                <h3 className="font-medium text-white mb-1">{label}</h3>
                <p className="text-sm text-slate-500">{desc}</p>
              </div>
              {step < 4 && <ArrowRight className="absolute right-0 top-8 w-5 h-5 text-slate-600" />}
            </div>
          ))}
        </div>
      </Card>
    </div>
  );
}

export default Dashboard;
