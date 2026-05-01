import Link from "next/link";

export default function NotFound() {
  return (
    <div className="min-h-screen bg-sika-slate-50 flex items-center justify-center px-6">
      <div className="text-center">
        <div className="text-6xl mb-4">🤔</div>
        <h2 className="font-display text-2xl text-sika-slate-900 mb-2">Page not found</h2>
        <p className="text-sika-slate-500 mb-8">The page you're looking for doesn't exist.</p>
        <Link
          href="/"
          className="inline-block bg-sika-gold text-white font-semibold px-8 py-4 rounded-2xl hover:bg-sika-gold-dark transition-colors"
        >
          Go Home
        </Link>
      </div>
    </div>
  );
}
