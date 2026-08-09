import React, { useState, useEffect } from 'react';
import { X, Settings, Check, AlertCircle } from 'lucide-react';
import type { PersonaResponse, PersonaUpdateRequest } from '../services/agentApi';

interface PersonaModalProps {
  isOpen: boolean;
  onClose: () => void;
  currentPersona: PersonaResponse | null;
  onSavePersona: (updated: PersonaUpdateRequest) => Promise<void>;
}

export const PersonaModal: React.FC<PersonaModalProps> = ({
  isOpen,
  onClose,
  currentPersona,
  onSavePersona,
}) => {
  const [name, setName] = useState('');
  const [domain, setDomain] = useState('');
  const [description, setDescription] = useState('');
  const [categories, setCategories] = useState('');
  const [threshold, setThreshold] = useState(0.5);

  const [isSaving, setIsSaving] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  useEffect(() => {
    if (currentPersona) {
      setName(currentPersona.persona_name || 'NOVA');
      setDomain(currentPersona.primary_domain || 'AI & Emerging Technology');
      setDescription(currentPersona.persona_description || '');
      setCategories(Array.isArray(currentPersona.preferred_categories) ? currentPersona.preferred_categories.join(', ') : '');
      setThreshold(currentPersona.min_relevance_threshold ?? 0.5);
    }
  }, [currentPersona, isOpen]);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSaving(true);
    setErrorMsg(null);
    setSuccessMsg(null);

    const categoriesArray = categories
      .split(',')
      .map((c) => c.trim())
      .filter(Boolean);

    try {
      await onSavePersona({
        persona_name: name,
        primary_domain: domain,
        persona_description: description,
        preferred_categories: categoriesArray,
        min_relevance_threshold: Number(threshold),
      });
      setSuccessMsg('Persona & Feed Configuration updated successfully!');
      setTimeout(() => {
        setSuccessMsg(null);
        onClose();
      }, 1200);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to update persona configuration';
      setErrorMsg(msg);
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 bg-slate-950/80 backdrop-blur-md flex items-center justify-center p-4">
      <div className="bg-slate-900 border border-cyan-500/40 rounded-xl max-w-xl w-full p-6 relative shadow-[0_0_40px_rgba(6,182,212,0.2)] font-sans">
        {/* Close Button */}
        <button
          onClick={onClose}
          className="absolute top-4 right-4 text-slate-400 hover:text-slate-100 p-1 rounded-lg bg-slate-800/80 hover:bg-slate-700 transition"
        >
          <X className="w-5 h-5" />
        </button>

        {/* Header */}
        <div className="flex items-center gap-2 mb-4 border-b border-slate-800 pb-3">
          <Settings className="w-5 h-5 text-cyan-400" />
          <h2 className="text-base font-bold font-mono text-slate-100 uppercase tracking-wide">
            Configure Agent Persona & Feed Rules
          </h2>
        </div>

        {errorMsg && (
          <div className="mb-4 p-3 rounded-lg bg-rose-950/80 border border-rose-800 text-rose-300 text-xs font-mono flex items-center gap-2">
            <AlertCircle className="w-4 h-4 text-rose-400 flex-shrink-0" />
            <span>{errorMsg}</span>
          </div>
        )}

        {successMsg && (
          <div className="mb-4 p-3 rounded-lg bg-emerald-950/80 border border-emerald-800 text-emerald-300 text-xs font-mono flex items-center gap-2">
            <Check className="w-4 h-4 text-emerald-400 flex-shrink-0" />
            <span>{successMsg}</span>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4 text-xs font-mono">
          <div>
            <label className="block text-slate-400 mb-1">Persona Name:</label>
            <input
              type="text"
              required
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-slate-200 focus:outline-none focus:border-cyan-500"
            />
          </div>

          <div>
            <label className="block text-slate-400 mb-1">Primary Domain Focus:</label>
            <input
              type="text"
              required
              value={domain}
              onChange={(e) => setDomain(e.target.value)}
              className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-slate-200 focus:outline-none focus:border-cyan-500"
            />
          </div>

          <div>
            <label className="block text-slate-400 mb-1">Persona Description:</label>
            <textarea
              rows={2}
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-slate-200 focus:outline-none focus:border-cyan-500 font-sans"
            />
          </div>

          <div>
            <label className="block text-slate-400 mb-1">Preferred Categories (comma-separated):</label>
            <input
              type="text"
              value={categories}
              onChange={(e) => setCategories(e.target.value)}
              placeholder="AI, Security, Robotics, Hardware"
              className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-slate-200 focus:outline-none focus:border-cyan-500"
            />
          </div>

          <div>
            <div className="flex justify-between text-slate-400 mb-1">
              <span>Minimum Relevance Threshold:</span>
              <span className="text-cyan-400 font-bold">{threshold}</span>
            </div>
            <input
              type="range"
              min="0.0"
              max="1.0"
              step="0.05"
              value={threshold}
              onChange={(e) => setThreshold(parseFloat(e.target.value))}
              className="w-full accent-cyan-500 cursor-pointer"
            />
          </div>

          <div className="pt-3 border-t border-slate-800 flex justify-end gap-2 font-sans">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs transition"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isSaving}
              className="px-4 py-2 rounded-lg bg-cyan-600 hover:bg-cyan-500 text-slate-950 font-bold text-xs transition disabled:opacity-50"
            >
              {isSaving ? 'Saving...' : 'Save Configuration'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
