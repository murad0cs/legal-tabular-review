import { useState, useEffect } from 'react';
import { X, Settings, Zap, Bell, Save } from 'lucide-react';
import { settingsApi } from '../api/index.js';
import Skeleton from './Skeleton.jsx';
import toast from 'react-hot-toast';

function ProjectSettings({ projectId, onClose, onSave }) {
  const [settings, setSettings] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    fetchSettings();
  }, [projectId]);

  const fetchSettings = async () => {
    try {
      setLoading(true);
      const response = await settingsApi.getProjectSettings(projectId);
      setSettings(response.data);
    } catch (err) {
      toast.error('Failed to load settings');
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    try {
      setSaving(true);
      await settingsApi.updateProjectSettings(projectId, {
        auto_approve_enabled: settings.auto_approve_enabled,
        auto_approve_threshold: settings.auto_approve_threshold,
        notify_on_extraction_complete: settings.notify_on_extraction_complete,
        notify_on_low_confidence: settings.notify_on_low_confidence,
        low_confidence_threshold: settings.low_confidence_threshold,
      });
      toast.success('Settings saved');
      onSave?.();
      onClose();
    } catch (err) {
      toast.error('Failed to save settings');
    } finally {
      setSaving(false);
    }
  };

  const updateSetting = (key, value) => {
    setSettings(prev => ({ ...prev, [key]: value }));
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
      <div className="bg-slate-800 dark:bg-slate-800 light:bg-white rounded-xl shadow-2xl w-full max-w-lg border border-slate-700 dark:border-slate-700 light:border-slate-200">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-slate-700 dark:border-slate-700 light:border-slate-200">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-indigo-600/20 rounded-lg flex items-center justify-center">
              <Settings className="w-5 h-5 text-indigo-400" />
            </div>
            <div>
              <h2 className="text-lg font-semibold text-white dark:text-white light:text-slate-900">
                Project Settings
              </h2>
              <p className="text-sm text-slate-400">Configure extraction behavior</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-2 text-slate-400 hover:text-white hover:bg-slate-700 rounded-lg transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content */}
        <div className="p-6 space-y-6">
          {loading ? (
            <div className="space-y-4">
              <Skeleton className="h-20 w-full" />
              <Skeleton className="h-20 w-full" />
            </div>
          ) : (
            <>
              {/* Auto-approve section */}
              <div className="space-y-4">
                <div className="flex items-center gap-3 text-amber-400">
                  <Zap className="w-5 h-5" />
                  <h3 className="font-medium">Auto-Approve</h3>
                </div>
                
                <label className="flex items-center justify-between p-4 bg-slate-700/30 dark:bg-slate-700/30 light:bg-slate-100 rounded-lg cursor-pointer">
                  <div>
                    <p className="text-sm font-medium text-white dark:text-white light:text-slate-900">
                      Enable auto-approve
                    </p>
                    <p className="text-xs text-slate-400">
                      Automatically approve values above confidence threshold
                    </p>
                  </div>
                  <input
                    type="checkbox"
                    checked={settings?.auto_approve_enabled || false}
                    onChange={(e) => updateSetting('auto_approve_enabled', e.target.checked)}
                    className="w-5 h-5 rounded border-slate-500 bg-slate-600 text-indigo-600 focus:ring-indigo-500"
                  />
                </label>

                {settings?.auto_approve_enabled && (
                  <div className="p-4 bg-slate-700/30 dark:bg-slate-700/30 light:bg-slate-100 rounded-lg">
                    <label className="block">
                      <span className="text-sm font-medium text-white dark:text-white light:text-slate-900">
                        Confidence Threshold
                      </span>
                      <div className="flex items-center gap-4 mt-2">
                        <input
                          type="range"
                          min="0.5"
                          max="1"
                          step="0.05"
                          value={settings?.auto_approve_threshold || 0.9}
                          onChange={(e) => updateSetting('auto_approve_threshold', parseFloat(e.target.value))}
                          className="flex-1 h-2 bg-slate-600 rounded-lg appearance-none cursor-pointer accent-indigo-500"
                        />
                        <span className="w-16 text-center text-white font-mono bg-slate-600 px-2 py-1 rounded">
                          {Math.round((settings?.auto_approve_threshold || 0.9) * 100)}%
                        </span>
                      </div>
                      <p className="text-xs text-slate-400 mt-2">
                        Values with confidence ≥ {Math.round((settings?.auto_approve_threshold || 0.9) * 100)}% will be auto-approved
                      </p>
                    </label>
                  </div>
                )}
              </div>

              {/* Low confidence alerts */}
              <div className="space-y-4">
                <div className="flex items-center gap-3 text-red-400">
                  <Bell className="w-5 h-5" />
                  <h3 className="font-medium">Low Confidence Alerts</h3>
                </div>
                
                <label className="flex items-center justify-between p-4 bg-slate-700/30 dark:bg-slate-700/30 light:bg-slate-100 rounded-lg cursor-pointer">
                  <div>
                    <p className="text-sm font-medium text-white dark:text-white light:text-slate-900">
                      Flag low confidence values
                    </p>
                    <p className="text-xs text-slate-400">
                      Highlight values that need extra attention
                    </p>
                  </div>
                  <input
                    type="checkbox"
                    checked={settings?.notify_on_low_confidence || false}
                    onChange={(e) => updateSetting('notify_on_low_confidence', e.target.checked)}
                    className="w-5 h-5 rounded border-slate-500 bg-slate-600 text-indigo-600 focus:ring-indigo-500"
                  />
                </label>

                {settings?.notify_on_low_confidence && (
                  <div className="p-4 bg-slate-700/30 dark:bg-slate-700/30 light:bg-slate-100 rounded-lg">
                    <label className="block">
                      <span className="text-sm font-medium text-white dark:text-white light:text-slate-900">
                        Low Confidence Threshold
                      </span>
                      <div className="flex items-center gap-4 mt-2">
                        <input
                          type="range"
                          min="0.1"
                          max="0.7"
                          step="0.05"
                          value={settings?.low_confidence_threshold || 0.5}
                          onChange={(e) => updateSetting('low_confidence_threshold', parseFloat(e.target.value))}
                          className="flex-1 h-2 bg-slate-600 rounded-lg appearance-none cursor-pointer accent-red-500"
                        />
                        <span className="w-16 text-center text-white font-mono bg-slate-600 px-2 py-1 rounded">
                          {Math.round((settings?.low_confidence_threshold || 0.5) * 100)}%
                        </span>
                      </div>
                      <p className="text-xs text-slate-400 mt-2">
                        Values with confidence &lt; {Math.round((settings?.low_confidence_threshold || 0.5) * 100)}% will be flagged
                      </p>
                    </label>
                  </div>
                )}
              </div>
            </>
          )}
        </div>

        {/* Footer */}
        <div className="flex items-center justify-end gap-3 p-4 border-t border-slate-700 dark:border-slate-700 light:border-slate-200">
          <button
            onClick={onClose}
            className="px-4 py-2 text-slate-400 hover:text-white hover:bg-slate-700 rounded-lg transition-colors"
          >
            Cancel
          </button>
          <button
            onClick={handleSave}
            disabled={loading || saving}
            className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed text-white rounded-lg flex items-center gap-2 transition-colors"
          >
            <Save className="w-4 h-4" />
            {saving ? 'Saving...' : 'Save Settings'}
          </button>
        </div>
      </div>
    </div>
  );
}

export default ProjectSettings;


