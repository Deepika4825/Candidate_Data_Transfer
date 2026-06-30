// ── Helpers ────────────────────────────────────────────────────────────────
const ALL_OUTPUT_FIELDS = [
  'Candidate ID', 'Full Name', 'Email', 'Phone', 'Current Company',
  'Skills', 'Education', 'Experience', 'Projects', 'Certifications',
  'Overall Confidence', 'Status',
];

function downloadFile(content, filename, mime) {
  const blob = new Blob([content], { type: mime });
  const url  = URL.createObjectURL(blob);
  const a    = document.createElement('a');
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

function jsonToCsv(obj) {
  const rows = Object.entries(obj).map(([k, v]) => {
    const val = Array.isArray(v) ? v.join('; ') : String(v ?? '');
    return `"${k}","${val.replace(/"/g, '""')}"`;
  });
  return 'Field,Value\n' + rows.join('\n');
}

// ── Sub-icons ──────────────────────────────────────────────────────────────
function DownloadIcon() {
  return (
    <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5M16.5 12L12 16.5m0 0L7.5 12m4.5 4.5V3" />
    </svg>
  );
}

// ── CandidateCard ──────────────────────────────────────────────────────────
export default function CandidateCard({
  candidate: c,
  index: i,
  schema,
  onSchemaChange,
  fields,
  onFieldToggle,
  onGenerate,
  generating,
  profile,
  genError,
  validationNotices = [],
}) {
  const conf = c.confidence || {};

  const scoreColor =
    conf.score >= 90 ? 'green' :
    conf.score >= 75 ? 'blue'  : 'yellow';

  const colorMap = {
    green:  { badge: 'bg-green-50 border-green-200 text-green-700',   text: 'text-green-700'  },
    blue:   { badge: 'bg-blue-50 border-blue-200 text-blue-700',      text: 'text-blue-700'   },
    yellow: { badge: 'bg-yellow-50 border-yellow-200 text-yellow-700', text: 'text-yellow-700' },
  };
  const col = colorMap[scoreColor];

  return (
    <div className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">

      {/* ── Header ── */}
      <div className="px-5 pt-5 pb-4 flex items-start justify-between gap-3 flex-wrap">
        <div>
          <p className="font-bold text-gray-900 text-base">{c.name || `Candidate ${i + 1}`}</p>
          {c.candidate_id && (
            <p className="text-xs text-gray-700 mt-0.5 font-mono">ID: {c.candidate_id}</p>
          )}
        </div>
        {conf.percentage && (
          <div className={`flex flex-col items-center rounded-xl px-4 py-2 border ${col.badge}`}>
            <span className={`text-2xl font-bold leading-none ${col.text}`}>{conf.percentage}</span>
            <span className={`text-[10px] font-semibold mt-0.5 ${col.text}`}>{conf.status}</span>
          </div>
        )}
      </div>

      <div className="border-t border-gray-100" />

      {/* ── Confidence bar ── */}
      {conf.percentage && (
        <div className="px-5 py-3 flex items-center justify-between bg-gray-50">
          <span className="text-xs font-semibold text-gray-600">Overall Confidence Score</span>
          <span className={`text-sm font-bold ${col.text}`}>
            {conf.percentage} · {conf.status}
          </span>
        </div>
      )}

      <div className="border-t border-gray-100" />

      {/* ── Output Profile Generation ── */}
      <div className="px-5 py-5">
        <p className="text-[10px] font-bold text-[#1a2b6b] uppercase tracking-widest mb-4">
          Output Profile Generation
        </p>

        {/* Schema radio buttons */}
        <div className="flex gap-6 mb-4">
          {['default', 'custom'].map(t => (
            <label key={t} className="flex items-center gap-2 cursor-pointer select-none">
              <input
                type="radio"
                name={`schema-${i}`}
                value={t}
                checked={schema === t}
                onChange={() => onSchemaChange(t)}
                className="w-4 h-4 accent-[#1a2b6b]"
              />
              <span className="text-xs font-semibold text-gray-700">
                {t === 'default' ? 'Default Output Schema' : 'Custom Output Schema'}
              </span>
            </label>
          ))}
        </div>
        {schema === 'custom' && (
          <div className="mb-4 rounded-xl border border-blue-100 bg-blue-50 p-4">
            <p className="text-[10px] font-bold text-[#1a2b6b] uppercase tracking-widest mb-3">
              Select Fields
            </p>
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
              {ALL_OUTPUT_FIELDS.map(field => {
                const checked = fields.includes(field);
                return (
                  <label
                    key={field}
                    className="flex items-center gap-2 cursor-pointer select-none"
                    onClick={() => onFieldToggle(field)}
                  >
                    <div
                      className={[
                        'w-4 h-4 rounded border-2 flex items-center justify-center flex-shrink-0 transition-all',
                        checked ? 'bg-[#1a2b6b] border-[#1a2b6b]' : 'bg-white border-gray-300',
                      ].join(' ')}
                    >
                      {checked && (
                        <svg className="w-2.5 h-2.5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={3}>
                          <path strokeLinecap="round" strokeLinejoin="round" d="M4.5 12.75l6 6 9-13.5" />
                        </svg>
                      )}
                    </div>
                    <span className="text-xs text-gray-700">{field}</span>
                  </label>
                );
              })}
            </div>
          </div>
        )}

        {/* Generate button */}
        <button
          onClick={onGenerate}
          disabled={generating}
          className="flex items-center gap-2 rounded-lg bg-[#1a2b6b] hover:bg-[#162057] text-white px-4 py-2.5 text-xs font-bold transition-all disabled:opacity-40 disabled:cursor-not-allowed"
        >
          {generating ? (
            <>
              <svg className="w-3.5 h-3.5 animate-spin" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v4l3-3-3-3v4a8 8 0 00-8 8h4z" />
              </svg>
              Generating…
            </>
          ) : (
            'Generate Config & Profile'
          )}
        </button>

        {/* Validation notices (info banners) */}
        {validationNotices.length > 0 && (
          <div className="mt-3 flex flex-col gap-2">
            {validationNotices.map((msg, n) => (
              <div key={n} className="flex items-start gap-2 rounded-lg border border-amber-200 bg-amber-50 p-3">
                <svg className="w-4 h-4 text-amber-600 mt-0.5 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126zM12 15.75h.007v.008H12v-.008z" />
                </svg>
                <p className="text-xs text-amber-800 font-medium">{msg}</p>
              </div>
            ))}
          </div>
        )}

        {/* Error */}
        {genError && (
          <div className="mt-3 flex items-start gap-2 rounded-lg border border-red-200 bg-red-50 p-3">
            <svg className="w-4 h-4 text-red-500 mt-0.5 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126zM12 15.75h.007v.008H12v-.008z" />
            </svg>
            <p className="text-xs text-red-600">{genError}</p>
          </div>
        )}

        {/* Result panels */}
        {profile && (
          <div className="mt-5 flex flex-col gap-5">

            {/* config.json panel */}
            {profile.config_used && (
              <div>
                <div className="flex items-center justify-between mb-2 flex-wrap gap-2">
                  <p className="text-[10px] font-bold text-gray-700 uppercase tracking-widest">
                    Generated config.json
                  </p>
                  <button
                    onClick={() => downloadFile(
                      JSON.stringify(profile.config_used, null, 2),
                      'config.json',
                      'application/json'
                    )}
                    className="flex items-center gap-1 text-[10px] font-bold text-[#1a2b6b] hover:text-[#162057]"
                  >
                    <DownloadIcon /> Download config.json
                  </button>
                </div>
                <pre className="text-xs font-mono bg-[#0f1a45] text-yellow-300 p-4 rounded-lg overflow-x-auto max-h-48 border border-[#1a2b6b]/30 leading-relaxed">
                  {JSON.stringify(profile.config_used, null, 2)}
                </pre>
              </div>
            )}

            {/* Final profile panel */}
            {profile.profile && (
              <div>
                <div className="flex items-center justify-between mb-2 flex-wrap gap-2">
                  <p className="text-[10px] font-bold text-gray-700 uppercase tracking-widest">
                    Final Candidate Profile
                  </p>
                  <div className="flex gap-2">
                    <button
                      onClick={() => downloadFile(
                        JSON.stringify(profile.profile, null, 2),
                        `candidate_${c.candidate_id || 'profile'}.json`,
                        'application/json'
                      )}
                      className="flex items-center gap-1 text-[10px] font-bold bg-[#1a2b6b] hover:bg-[#162057] text-white rounded-lg px-3 py-1.5 transition-colors"
                    >
                      <DownloadIcon /> Download JSON
                    </button>
                    <button
                      onClick={() => downloadFile(
                        jsonToCsv(profile.profile),
                        `candidate_${c.candidate_id || 'profile'}.csv`,
                        'text/csv'
                      )}
                      className="flex items-center gap-1 text-[10px] font-bold bg-[#0f1a45] hover:bg-[#162057] text-white rounded-lg px-3 py-1.5 transition-colors"
                    >
                      <DownloadIcon /> Download CSV
                    </button>
                  </div>
                </div>
                <pre className="text-xs font-mono bg-[#0f1a45] text-green-400 p-4 rounded-lg overflow-x-auto max-h-72 border border-[#1a2b6b]/30 leading-relaxed">
                  {JSON.stringify(profile.profile, null, 2)}
                </pre>
              </div>
            )}

          </div>
        )}
      </div>
    </div>
  );
}
