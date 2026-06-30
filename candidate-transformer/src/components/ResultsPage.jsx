import { useState, useEffect, useRef } from 'react';
import CandidateCard from './CandidateCard';

// ── Pipeline steps ─────────────────────────────────────────────────────────
const PIPELINE_STEPS = [
  { label: 'Parsing files',             duration: 600 },
  { label: 'Extracting candidate data', duration: 700 },
  { label: 'Matching records',          duration: 600 },
  { label: 'Normalizing fields',        duration: 500 },
  { label: 'Deduplicating records',     duration: 500 },
  { label: 'Merging sources',           duration: 600 },
  { label: 'Resolving conflicts',       duration: 500 },
  { label: 'Scoring confidence',        duration: 400 },
];

// ── Pipeline component ─────────────────────────────────────────────────────
function PipelineAnimation({ onComplete }) {
  const [currentStep, setCurrentStep] = useState(0);
  const [doneSteps, setDoneSteps] = useState([]);
  const timerRef = useRef(null);

  useEffect(() => {
    let step = 0;
    function advance() {
      if (step >= PIPELINE_STEPS.length) {
        onComplete();
        return;
      }
      setCurrentStep(step);
      timerRef.current = setTimeout(() => {
        setDoneSteps(prev => [...prev, step]);
        step++;
        advance();
      }, PIPELINE_STEPS[step].duration);
    }
    advance();
    return () => clearTimeout(timerRef.current);
  }, [onComplete]);

  return (
    <div className="mt-2 rounded-xl border border-gray-200 bg-white p-6">
      <p className="text-xs font-bold text-[#1a2b6b] uppercase tracking-widest mb-5">
        Processing Pipeline
      </p>
      <div className="flex flex-col gap-3">
        {PIPELINE_STEPS.map((step, i) => {
          const done   = doneSteps.includes(i);
          const active = currentStep === i && !done;
          return (
            <div key={i} className="flex items-center gap-3">
              {/* Status indicator */}
              <div
                className={[
                  'w-6 h-6 rounded-full flex items-center justify-center flex-shrink-0 transition-all duration-300',
                  done   ? 'bg-[#1a2b6b]'
                  : active ? 'bg-blue-100 border-2 border-[#1a2b6b]'
                           : 'bg-gray-100 border-2 border-gray-200',
                ].join(' ')}
              >
                {done && (
                  <svg className="w-3.5 h-3.5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={3}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M4.5 12.75l6 6 9-13.5" />
                  </svg>
                )}
                {active && (
                  <svg className="w-3.5 h-3.5 text-[#1a2b6b] animate-spin" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v4l3-3-3-3v4a8 8 0 00-8 8h4z" />
                  </svg>
                )}
              </div>

              {/* Label */}
              <span
                className={[
                  'text-sm font-medium transition-all duration-300',
                  done   ? 'text-[#1a2b6b] font-semibold'
                  : active ? 'text-[#1a2b6b]'
                           : 'text-gray-600',
                ].join(' ')}
              >
                {step.label}
              </span>

              {active && (
                <span className="text-xs text-blue-400 animate-pulse ml-1">…</span>
              )}
              {done && (
                <span className="text-xs text-[#1a2b6b]/60 ml-auto">✓</span>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}

// ── Results Page ───────────────────────────────────────────────────────────
export default function ResultsPage({ sources, onBack }) {
  const [pipelineDone, setPipelineDone] = useState(false);
  const [candidates, setCandidates] = useState([]);
  const [error, setError] = useState('');
  const [apiLoading, setApiLoading] = useState(true);

  // Per-candidate state
  const [schemas, setSchemas] = useState({});
  const [customFields, setCustomFields] = useState({});
  const [generating, setGenerating] = useState({});
  const [profiles, setProfiles] = useState({});
  const [genErrors, setGenErrors] = useState({});
  const [validationNotices, setValidationNotices] = useState({}); // { idx: [msg,...] }

  // Fire the API call immediately on mount
  useEffect(() => {
    let cancelled = false;
    async function fetchData() {
      try {
        const res = await fetch('http://localhost:5000/process', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ sources }),
        });
        const data = await res.json();
        if (!cancelled) {
          setCandidates(data.candidates || []);
          if (!data.candidates?.length) {
            setError(data.errors?.[0] || 'No candidates found.');
          }
        }
      } catch {
        if (!cancelled) {
          setError('Could not reach the backend. Make sure Flask is running on port 5000.');
        }
      } finally {
        if (!cancelled) setApiLoading(false);
      }
    }
    fetchData();
    return () => { cancelled = true; };
  }, [sources]);

  const handlePipelineComplete = () => {
    setPipelineDone(true);
  };

  const toggleField = (idx, field) => {
    setCustomFields(prev => {
      const cur = prev[idx] || [];
      return {
        ...prev,
        [idx]: cur.includes(field) ? cur.filter(f => f !== field) : [...cur, field],
      };
    });
  };

  const handleGenerate = async (candidate, idx) => {
    const schema = schemas[idx] || '';
    const rawFields = customFields[idx] || [];
    const notices = [];

    // ── Validation 1: No schema selected ────────────────────────────────
    if (!schema) {
      setGenErrors(p => ({ ...p, [idx]: 'Please select an output schema before generating the profile.' }));
      return;
    }

    // ── Validation 2: Custom schema with no fields selected ──────────────
    if (schema === 'custom' && rawFields.length === 0) {
      setGenErrors(p => ({ ...p, [idx]: 'Please select at least one field to generate the custom schema.' }));
      return;
    }

    let finalFields = rawFields;

    if (schema === 'custom') {
      // ── Validation 3: Remove duplicates ───────────────────────────────
      const uniqueFields = [...new Set(rawFields)];
      if (uniqueFields.length < rawFields.length) {
        notices.push('Duplicate fields detected. Duplicate entries have been removed automatically.');
      }

      // ── Validation 4: Remove invalid/unsupported fields ───────────────
      const ALL_FIELDS = [
        'Candidate ID','Full Name','Email','Phone','Current Company',
        'Skills','Education','Experience','Projects','Certifications',
        'Overall Confidence','Status',
      ];
      const validFields   = uniqueFields.filter(f => ALL_FIELDS.includes(f));
      const invalidFields = uniqueFields.filter(f => !ALL_FIELDS.includes(f));
      if (invalidFields.length > 0) {
        notices.push('Invalid field(s) detected in the custom schema. Unsupported fields have been ignored.');
      }

      // ── Validation 5: Fields with no data in candidate ────────────────
      const FIELD_KEY_MAP = {
        'Candidate ID':      'candidate_id',
        'Full Name':         'name',
        'Email':             'email',
        'Phone':             'phone',
        'Current Company':   'current_company',
        'Skills':            'skills',
        'Education':         'education',
        'Experience':        'experience',
        'Projects':          'projects',
        'Certifications':    'certifications',
        'Overall Confidence': null,  // computed from confidence object
        'Status':            null,
      };
      const emptyFields = validFields.filter(f => {
        const key = FIELD_KEY_MAP[f];
        if (!key) return false;  // confidence/status always available
        const val = candidate[key];
        if (val === null || val === undefined || val === '') return true;
        if (Array.isArray(val) && val.length === 0) return true;
        return false;
      });
      if (emptyFields.length > 0) {
        notices.push('Some selected fields contain no data. The final profile includes only the available information.');
      }

      // Use only valid fields that have data (empty ones excluded by backend naturally)
      finalFields = validFields;

      if (finalFields.length === 0) {
        setGenErrors(p => ({ ...p, [idx]: 'No valid fields with data found. Please select different fields.' }));
        setValidationNotices(p => ({ ...p, [idx]: notices }));
        return;
      }
    }

    // ── Proceed with generation ──────────────────────────────────────────
    setValidationNotices(p => ({ ...p, [idx]: notices }));
    setGenerating(p => ({ ...p, [idx]: true }));
    setProfiles(p => ({ ...p, [idx]: null }));
    setGenErrors(p => ({ ...p, [idx]: '' }));

    try {
      const res = await fetch('http://localhost:5000/generate-profile', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ candidate, schema_type: schema, selected_fields: finalFields }),
      });
      const data = await res.json();
      if (!res.ok) {
        setGenErrors(p => ({ ...p, [idx]: data.error || 'Generation failed.' }));
      } else {
        setProfiles(p => ({ ...p, [idx]: data }));
      }
    } catch {
      setGenErrors(p => ({ ...p, [idx]: 'Could not connect to the backend.' }));
    } finally {
      setGenerating(p => ({ ...p, [idx]: false }));
    }
  };

  return (
    <div className="min-h-screen w-full bg-[#0f1a45] px-4 py-8">

      {/* Top bar */}
      <div className="w-full max-w-2xl mx-auto mb-6 flex items-center gap-4">
        <button
          onClick={onBack}
          className="flex items-center gap-2 text-white text-sm font-medium hover:text-blue-200 transition-colors"
        >
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M10.5 19.5L3 12m0 0l7.5-7.5M3 12h18" />
          </svg>
          Back
        </button>
        <h1 className="text-white font-bold text-base leading-tight">
          Candidate Data Transformer
        </h1>
      </div>

      {/* Main card */}
      <div className="w-full max-w-2xl mx-auto">
        <div className="bg-white rounded-2xl shadow-2xl p-8">

          {/* Pipeline always shows first */}
          {!pipelineDone && (
            <div>
              <p className="text-xs font-bold text-[#1a2b6b] uppercase tracking-widest mb-1">
                Processing Your Sources
              </p>
              <p className="text-sm text-gray-700 mb-4">
                Running the transformation pipeline on{' '}
                <span className="font-semibold text-[#1a2b6b]">{sources.length} source{sources.length > 1 ? 's' : ''}</span>…
              </p>
              <PipelineAnimation onComplete={handlePipelineComplete} />
            </div>
          )}

          {/* After pipeline: show output section */}
          {pipelineDone && (
            <div>
              {/* Pipeline done summary */}
              <div className="flex items-center gap-3 mb-6">
                <div className="w-8 h-8 rounded-full bg-[#1a2b6b] flex items-center justify-center flex-shrink-0">
                  <svg className="w-4 h-4 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={3}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M4.5 12.75l6 6 9-13.5" />
                  </svg>
                </div>
                <div>
                  <p className="text-sm font-bold text-[#1a2b6b]">Pipeline Complete</p>
                  <p className="text-xs text-gray-700">All 8 steps finished successfully</p>
                </div>
              </div>

              <div className="border-t border-gray-100 mb-6" />

              {/* Error state */}
              {error && (
                <div className="flex items-start gap-2 rounded-xl border border-red-200 bg-red-50 px-4 py-3 mb-4">
                  <svg className="w-4 h-4 text-red-500 mt-0.5 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126zM12 15.75h.007v.008H12v-.008z" />
                  </svg>
                  <p className="text-xs text-red-600">{error}</p>
                </div>
              )}

              {/* API still loading */}
              {apiLoading && !error && (
                <div className="flex items-center gap-3 py-4">
                  <svg className="w-5 h-5 text-[#1a2b6b] animate-spin" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v4l3-3-3-3v4a8 8 0 00-8 8h4z" />
                  </svg>
                  <p className="text-sm text-gray-700">Waiting for API response…</p>
                </div>
              )}

              {/* Candidate cards */}
              {!apiLoading && candidates.length > 0 && (
                <div className="flex flex-col gap-5">
                  {candidates.map((c, i) => (
                    <CandidateCard
                      key={i}
                      candidate={c}
                      index={i}
                      schema={schemas[i] || ''}
                      onSchemaChange={v => setSchemas(p => ({ ...p, [i]: v }))}
                      fields={customFields[i] || []}
                      onFieldToggle={f => toggleField(i, f)}
                      onGenerate={() => handleGenerate(c, i)}
                      generating={generating[i]}
                      profile={profiles[i]}
                      genError={genErrors[i]}
                      validationNotices={validationNotices[i] || []}
                    />
                  ))}
                </div>
              )}
            </div>
          )}

        </div>
      </div>

      {/* Footer */}
      <p className="text-center text-xs text-blue-200 mt-8">
        All processing is done securely · No data is stored permanently
      </p>
    </div>
  );
}
