import { useState } from 'react';

// ── Icons ──────────────────────────────────────────────────────────────────
const CsvIcon = ({ className = 'w-5 h-5' }) => (
  <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.8}>
    <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m0 12.75h7.5m-7.5 3H12M10.5 2.25H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z" />
  </svg>
);
const JsonIcon = ({ className = 'w-5 h-5' }) => (
  <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.8}>
    <path strokeLinecap="round" strokeLinejoin="round" d="M17.25 6.75L22.5 12l-5.25 5.25m-10.5 0L1.5 12l5.25-5.25m7.5-3l-4.5 16.5" />
  </svg>
);
const ResumeIcon = ({ className = 'w-5 h-5' }) => (
  <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.8}>
    <path strokeLinecap="round" strokeLinejoin="round" d="M15.75 17.25v3.375c0 .621-.504 1.125-1.125 1.125h-9.75a1.125 1.125 0 01-1.125-1.125V7.875c0-.621.504-1.125 1.125-1.125H6.75a9.06 9.06 0 011.5.124m7.5 10.376h3.375c.621 0 1.125-.504 1.125-1.125V11.25c0-4.46-3.243-8.161-7.5-8.876a9.06 9.06 0 00-1.5-.124H9.375c-.621 0-1.125.504-1.125 1.125v3.5m7.5 10.375H9.375a1.125 1.125 0 01-1.125-1.125v-9.25m12 6.625v-1.875a3.375 3.375 0 00-3.375-3.375h-1.5a1.125 1.125 0 01-1.125-1.125v-1.5a3.375 3.375 0 00-3.375-3.375H9.75" />
  </svg>
);
const ConfigIcon = ({ className = 'w-5 h-5' }) => (
  <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.8}>
    <path strokeLinecap="round" strokeLinejoin="round" d="M10.343 3.94c.09-.542.56-.94 1.11-.94h1.093c.55 0 1.02.398 1.11.94l.149.894c.07.424.384.764.78.93.398.164.855.142 1.205-.108l.737-.527a1.125 1.125 0 011.45.12l.773.774c.39.389.44 1.002.12 1.45l-.527.737c-.25.35-.272.806-.107 1.204.165.397.505.71.93.78l.893.15c.543.09.94.56.94 1.109v1.094c0 .55-.397 1.02-.94 1.11l-.893.149c-.425.07-.765.383-.93.78-.165.398-.143.854.107 1.204l.527.738c.32.447.269 1.06-.12 1.45l-.774.773a1.125 1.125 0 01-1.449.12l-.738-.527c-.35-.25-.806-.272-1.203-.107-.397.165-.71.505-.781.929l-.149.894c-.09.542-.56.94-1.11.94h-1.094c-.55 0-1.019-.398-1.11-.94l-.148-.894c-.071-.424-.384-.764-.781-.93-.398-.164-.854-.142-1.204.108l-.738.527c-.447.32-1.06.269-1.45-.12l-.773-.774a1.125 1.125 0 01-.12-1.45l.527-.737c.25-.35.273-.806.108-1.204-.165-.397-.505-.71-.93-.78l-.894-.15c-.542-.09-.94-.56-.94-1.109v-1.094c0-.55.398-1.02.94-1.11l.894-.149c.424-.07.765-.383.93-.78.165-.398.143-.854-.108-1.204l-.526-.738a1.125 1.125 0 01.12-1.45l.773-.773a1.125 1.125 0 011.45-.12l.737.527c.35.25.807.272 1.204.107.397-.165.71-.505.78-.929l.15-.894z" />
    <path strokeLinecap="round" strokeLinejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
  </svg>
);

// ── Constants ──────────────────────────────────────────────────────────────
const SOURCES = [
  { id: 'csv',    label: 'Recruiter CSV',  file: 'candidates.csv',     Icon: CsvIcon    },
  { id: 'json',   label: 'ATS JSON',       file: 'ats.json',           Icon: JsonIcon   },
  { id: 'resume', label: 'Resumes',        file: 'Deepika_Resume.pdf', Icon: ResumeIcon },
  { id: 'config', label: 'Runtime Config', file: 'config.json',        Icon: ConfigIcon },
];

export default function SelectionPage({ onStart }) {
  const [selected, setSelected] = useState(new Set());

  const toggle = (id) => {
    setSelected(prev => {
      const next = new Set(prev);
      next.has(id) ? next.delete(id) : next.add(id);
      return next;
    });
  };

  const handleStart = () => {
    if (selected.size === 0) return;
    onStart([...selected]);
  };

  return (
    <div className="min-h-screen w-full bg-[#0f1a45] flex items-center justify-center px-4 py-12">
      <div className="w-full max-w-lg">

        {/* Card */}
        <div className="bg-white rounded-2xl shadow-2xl p-8">

          {/* Title */}
          <div className="text-center mb-7">
            <h1 className="text-2xl font-bold text-[#1a2b6b] leading-tight mb-2">
              Candidate Data Transformer
            </h1>
            <p className="text-sm text-gray-700">
              Select one or more data sources to extract, normalize, and merge candidate profiles.
            </p>
          </div>

          <div className="border-t border-gray-100 mb-6" />

          {/* Section label */}
          <p className="text-xs font-bold text-[#1a2b6b] uppercase tracking-widest mb-4">
            Select Data Sources
          </p>

          {/* Source checkboxes */}
          <div className="flex flex-col gap-3 mb-7">
            {SOURCES.map(({ id, label, file, Icon }) => {
              const checked = selected.has(id);
              return (
                <button
                  key={id}
                  type="button"
                  onClick={() => toggle(id)}
                  className={[
                    'w-full flex items-center gap-4 rounded-xl border-2 px-4 py-3.5 text-left transition-all duration-150 cursor-pointer',
                    checked
                      ? 'border-[#1a2b6b] bg-blue-50'
                      : 'border-gray-200 bg-white hover:border-[#1a2b6b]/40',
                  ].join(' ')}
                >
                  {/* Icon box */}
                  <div
                    className={[
                      'w-9 h-9 rounded-lg flex items-center justify-center flex-shrink-0',
                      checked ? 'bg-[#1a2b6b]' : 'bg-gray-100',
                    ].join(' ')}
                  >
                    <Icon className={`w-4 h-4 ${checked ? 'text-white' : 'text-gray-500'}`} />
                  </div>

                  {/* Labels */}
                  <div className="flex-1 min-w-0">
                    <p className={`text-sm font-semibold ${checked ? 'text-[#1a2b6b]' : 'text-gray-800'}`}>
                      {label}
                    </p>
                  </div>

                  {/* Checkbox */}
                  <div
                    className={[
                      'w-5 h-5 rounded border-2 flex items-center justify-center flex-shrink-0 transition-all',
                      checked ? 'bg-[#1a2b6b] border-[#1a2b6b]' : 'border-gray-300 bg-white',
                    ].join(' ')}
                  >
                    {checked && (
                      <svg className="w-3 h-3 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={3}>
                        <path strokeLinecap="round" strokeLinejoin="round" d="M4.5 12.75l6 6 9-13.5" />
                      </svg>
                    )}
                  </div>
                </button>
              );
            })}
          </div>

          {/* Start button */}
          <button
            onClick={handleStart}
            disabled={selected.size === 0}
            className="w-full flex items-center justify-center gap-2 rounded-xl bg-[#1a2b6b] px-6 py-3.5 text-sm font-semibold text-white transition-all duration-150 hover:bg-[#162057] disabled:opacity-40 disabled:cursor-not-allowed focus:outline-none focus:ring-2 focus:ring-[#1a2b6b] focus:ring-offset-2"
          >
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M5.25 5.653c0-.856.917-1.398 1.667-.986l11.54 6.348a1.125 1.125 0 010 1.971l-11.54 6.347a1.125 1.125 0 01-1.667-.985V5.653z" />
            </svg>
            Start Processing
            {selected.size > 0 && (
              <span className="bg-white/20 rounded-full text-xs px-2 py-0.5">
                {selected.size} source{selected.size > 1 ? 's' : ''}
              </span>
            )}
          </button>

        </div>

        {/* Footer */}
        <p className="text-center text-xs text-blue-200 mt-6">
          All processing is done securely · No data is stored permanently
        </p>
      </div>
    </div>
  );
}
