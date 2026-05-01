export default function Loading() {
  return (
    <div className="min-h-screen bg-sika-slate-50 flex items-center justify-center">
      <div className="text-center">
        <div className="w-16 h-16 bg-sika-gold rounded-2xl flex items-center justify-center mx-auto mb-4 animate-pulse">
          <span className="text-3xl">🪙</span>
        </div>
        <p className="text-sika-slate-500">Loading...</p>
      </div>
    </div>
  );
}
