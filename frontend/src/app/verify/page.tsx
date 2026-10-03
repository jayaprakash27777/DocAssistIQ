"use client";

import React, { useState, useEffect, Suspense } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import Link from "next/link";
import {
  ShieldCheck,
  ShieldAlert,
  FileText,
  Search,
  CheckCircle2,
  Copy,
  Check,
  Download,
  Printer,
  Calendar,
  User,
  Stethoscope,
  Lock,
  ExternalLink,
  Sparkles,
  Award,
  Building,
  RefreshCw,
  Clock,
  ArrowRight,
  Fingerprint
} from "lucide-react";

interface VerificationData {
  status: string;
  verification_code: string;
  sha256_hash: string;
  document_id: string;
  document_type: string;
  title: string;
  subtitle: string;
  consultation_id: string;
  patient_ref: string;
  patient_age_group: string;
  patient_sex: string;
  doctor_name: string;
  doctor_specialty: string;
  registration_number: string;
  issuing_body: string;
  signed_at: string;
  signed_at_formatted: string;
  signature_status: string;
  institution: string;
  verified_at: string;
  sections_summary: string[];
}

function VerifyPortalContent() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const initialCode = searchParams.get("code") || searchParams.get("token") || "";

  const [inputCode, setInputCode] = useState(initialCode);
  const [loading, setLoading] = useState(false);
  const [verificationResult, setVerificationResult] = useState<VerificationData | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [copiedHash, setCopiedHash] = useState(false);
  const [copiedCode, setCopiedCode] = useState(false);
  const [downloadingFormat, setDownloadingFormat] = useState<"pdf" | "docx" | null>(null);

  const performVerification = async (codeToVerify: string) => {
    const trimmed = codeToVerify.trim();
    if (!trimmed) {
      setError("Please enter a digital signature verification token or SHA-256 hash.");
      return;
    }

    setLoading(true);
    setError(null);
    setVerificationResult(null);

    try {
      const rawUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
      const rootUrl = rawUrl.replace(/\/api\/v1\/?$/, "");

      let endpoint = `${rootUrl}/api/v1/documents/verify/${encodeURIComponent(trimmed)}`;
      let method = "GET";
      let body: string | undefined = undefined;

      // If it looks like a 64-char SHA-256 hex string, use hash verification
      if (/^[a-fA-F0-9]{64}$/.test(trimmed)) {
        endpoint = `${rootUrl}/api/v1/documents/verify/hash`;
        method = "POST";
        body = JSON.stringify({ sha256_hash: trimmed });
      }

      const res = await fetch(endpoint, {
        method,
        headers: { "Content-Type": "application/json" },
        body,
      });

      if (!res.ok) {
        const errJson = await res.json().catch(() => null);
        throw new Error(errJson?.error?.message || errJson?.detail || `Document signature could not be verified (HTTP ${res.status}).`);
      }

      const data = await res.json();
      setVerificationResult(data);
    } catch (err: any) {
      setError(err?.message || "Failed to verify digital document signature.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (initialCode) {
      setInputCode(initialCode);
      performVerification(initialCode);
    }
  }, [initialCode]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (inputCode.trim()) {
      router.push(`/verify?code=${encodeURIComponent(inputCode.trim())}`);
      performVerification(inputCode);
    }
  };

  const copyToClipboard = (text: string, type: "hash" | "code") => {
    navigator.clipboard.writeText(text);
    if (type === "hash") {
      setCopiedHash(true);
      setTimeout(() => setCopiedHash(false), 2000);
    } else {
      setCopiedCode(true);
      setTimeout(() => setCopiedCode(false), 2000);
    }
  };

  const handleDownload = async (format: "pdf" | "docx") => {
    if (!verificationResult) return;
    try {
      setDownloadingFormat(format);
      const rawUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
      const rootUrl = rawUrl.replace(/\/api\/v1\/?$/, "");
      const downloadEndpoint = `${rootUrl}/api/v1/clinical-documents/export/${encodeURIComponent(verificationResult.consultation_id)}/${encodeURIComponent(verificationResult.document_type)}/${format}`;

      const res = await fetch(downloadEndpoint);
      if (!res.ok) throw new Error(`Download failed with HTTP ${res.status}`);
      const blob = await res.blob();
      const blobUrl = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = blobUrl;
      a.download = `${verificationResult.document_type}_${verificationResult.patient_ref}.${format}`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(blobUrl);
    } catch (err: any) {
      alert(`Could not download file: ${err?.message || "Unknown error"}`);
    } finally {
      setDownloadingFormat(null);
    }
  };

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900 selection:bg-emerald-100 selection:text-emerald-900">
      {/* Top Header - Clean Hospital White */}
      <header className="border-b border-slate-200 bg-white sticky top-0 z-40 shadow-xs">
        <div className="max-w-6xl mx-auto px-4 h-16 flex items-center justify-between">
          <Link href="/" className="flex items-center gap-3 group">
            <div className="w-10 h-10 rounded-xl bg-emerald-600 flex items-center justify-center shadow-sm group-hover:bg-emerald-700 transition-colors">
              <ShieldCheck className="w-5 h-5 text-white" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="font-extrabold text-slate-900 tracking-tight text-base">DocAssistIQ</span>
                <span className="text-[10px] font-extrabold uppercase px-2 py-0.5 rounded-full bg-emerald-50 text-emerald-800 border border-emerald-200">
                  Trust &amp; Verification
                </span>
              </div>
              <p className="text-[11px] text-slate-500 font-medium">Cryptographic Clinical Document Registry</p>
            </div>
          </Link>

          <div className="flex items-center gap-2.5">
            <Link
              href="/ai"
              className="flex items-center gap-1.5 px-3.5 py-2 rounded-xl text-xs font-semibold bg-slate-100 hover:bg-slate-200 text-slate-700 border border-slate-200 transition-colors"
            >
              <Sparkles className="w-3.5 h-3.5 text-indigo-600" />
              <span>DocAssist IQ AI</span>
            </Link>
            <Link
              href="/dashboard"
              className="flex items-center gap-1.5 px-3.5 py-2 rounded-xl text-xs font-semibold bg-indigo-600 hover:bg-indigo-700 text-white transition-colors shadow-xs"
            >
              <span>Clinician Portal</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </Link>
          </div>
        </div>
      </header>

      {/* Main Body */}
      <main className="max-w-4xl mx-auto px-4 py-8">
        {/* Hero Section */}
        <div className="text-center max-w-2xl mx-auto mb-8">
          <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-emerald-50 border border-emerald-200 text-emerald-800 text-xs font-semibold mb-3">
            <Fingerprint className="w-3.5 h-3.5 text-emerald-600" />
            <span>Digital Signature Public Validation Portal</span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900 tracking-tight leading-snug">
            Verify Clinical Document Authenticity
          </h1>
          <p className="text-slate-600 text-sm mt-2 leading-relaxed font-normal">
            Validate the cryptographic SHA-256 integrity, licensed clinician credentials, and tamper-evident audit record of any official medical document issued by DocAssistIQ Health System.
          </p>
        </div>

        {/* Verification Search Box - Pure Light White Card */}
        <div className="bg-white border border-slate-200 rounded-2xl p-5 sm:p-6 shadow-sm mb-6">
          <form onSubmit={handleSubmit} className="space-y-3">
            <label htmlFor="verify-token-input" className="block text-xs font-bold uppercase tracking-wider text-slate-700">
              Enter Verification Token or SHA-256 Hash
            </label>
            <div className="flex flex-col sm:flex-row gap-3">
              <div className="relative flex-1">
                <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2 pointer-events-none" />
                <input
                  id="verify-token-input"
                  type="text"
                  value={inputCode}
                  onChange={(e) => setInputCode(e.target.value)}
                  placeholder="e.g. DOCASSIST-SIG-A0CA63CEA3D4 or 64-character sha256 hash..."
                  className="w-full pl-10 pr-4 py-2.5 rounded-xl bg-slate-50 border border-slate-300 text-slate-900 placeholder-slate-400 text-sm focus:outline-hidden focus:border-emerald-600 focus:ring-2 focus:ring-emerald-100 font-mono transition-all"
                />
              </div>
              <button
                type="submit"
                disabled={loading}
                className="px-6 py-2.5 rounded-xl font-bold text-sm bg-emerald-600 hover:bg-emerald-700 text-white shadow-xs transition-all flex items-center justify-center gap-2 cursor-pointer disabled:opacity-50 active:scale-98 shrink-0"
              >
                {loading ? <RefreshCw className="w-4 h-4 animate-spin" /> : <ShieldCheck className="w-4 h-4" />}
                <span>{loading ? "Verifying..." : "Verify Document"}</span>
              </button>
            </div>
            <div className="flex items-center gap-2 text-xs text-slate-500 mt-2">
              <Lock className="w-3.5 h-3.5 text-emerald-600 shrink-0" />
              <span>Tokens can be found at the bottom of official PDF and DOCX clinical documents.</span>
            </div>
          </form>
        </div>

        {/* Verification Status Feedback - Error state */}
        {error && (
          <div className="mb-6 p-4 sm:p-5 rounded-2xl bg-rose-50 border border-rose-200 text-rose-900 flex items-start gap-3.5">
            <ShieldAlert className="w-5 h-5 text-rose-600 shrink-0 mt-0.5" />
            <div>
              <h3 className="font-bold text-sm text-rose-900">Verification Failed / Invalid Document</h3>
              <p className="text-xs sm:text-sm text-rose-700 mt-1 leading-relaxed">{error}</p>
              <p className="text-xs text-rose-600 mt-1.5 font-medium">
                This verification code does not match any certified record in the DocAssistIQ Trust Registry. Check for typos or request an updated document from the issuing medical facility.
              </p>
            </div>
          </div>
        )}

        {/* Verified Result Card - Pristine Clinical Light Paper */}
        {verificationResult && (
          <div className="rounded-2xl border border-slate-200 bg-white overflow-hidden shadow-md mb-8">
            {/* Top Security Banner */}
            <div className="p-5 sm:p-6 bg-gradient-to-r from-emerald-50 via-teal-50 to-white border-b border-emerald-100 flex flex-col md:flex-row md:items-center justify-between gap-4">
              <div className="flex items-center gap-3.5">
                <div className="w-12 h-12 rounded-xl bg-emerald-600 text-white flex items-center justify-center shrink-0 shadow-sm">
                  <CheckCircle2 className="w-7 h-7" />
                </div>
                <div>
                  <div className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full bg-emerald-100 text-emerald-800 text-[11px] font-extrabold uppercase tracking-wider mb-1">
                    <span className="w-2 h-2 rounded-full bg-emerald-600" />
                    Cryptographically Authenticated &amp; Valid
                  </div>
                  <h2 className="text-lg sm:text-xl font-extrabold text-slate-900 tracking-tight">{verificationResult.title}</h2>
                  <p className="text-xs text-slate-600">{verificationResult.subtitle}</p>
                </div>
              </div>

              <div className="text-left md:text-right bg-white p-3 rounded-xl border border-slate-200 shadow-2xs">
                <span className="text-[10px] font-mono text-emerald-700 uppercase font-bold block">Document ID</span>
                <span className="text-sm font-mono font-bold text-slate-900">{verificationResult.document_id}</span>
                <span className="text-[11px] text-slate-500 block mt-0.5">Verified: {verificationResult.verified_at}</span>
              </div>
            </div>

            {/* Core Verification Details Grid */}
            <div className="p-5 sm:p-6 grid grid-cols-1 md:grid-cols-2 gap-4 border-b border-slate-100 text-sm">
              {/* Doctor Details */}
              <div className="bg-slate-50 rounded-xl p-4 border border-slate-200 space-y-2.5">
                <div className="flex items-center gap-2 text-indigo-700 text-xs font-bold uppercase tracking-wider">
                  <Stethoscope className="w-4 h-4" />
                  <span>Licensed Medical Prescriber / Clinician</span>
                </div>
                <div>
                  <h3 className="text-base font-bold text-slate-900">{verificationResult.doctor_name}</h3>
                  <p className="text-xs text-slate-600 font-medium">{verificationResult.doctor_specialty}</p>
                </div>
                <div className="pt-2 border-t border-slate-200 grid grid-cols-2 gap-2 text-xs">
                  <div>
                    <span className="text-slate-500 text-[11px] block">License / Reg Number</span>
                    <span className="font-mono font-bold text-slate-800">{verificationResult.registration_number}</span>
                  </div>
                  <div>
                    <span className="text-slate-500 text-[11px] block">Issuing Medical Board</span>
                    <span className="font-semibold text-slate-800">{verificationResult.issuing_body}</span>
                  </div>
                </div>
              </div>

              {/* Patient & Encounter Details */}
              <div className="bg-slate-50 rounded-xl p-4 border border-slate-200 space-y-2.5">
                <div className="flex items-center gap-2 text-emerald-700 text-xs font-bold uppercase tracking-wider">
                  <User className="w-4 h-4" />
                  <span>Patient &amp; Clinical Encounter</span>
                </div>
                <div className="grid grid-cols-2 gap-2">
                  <div>
                    <span className="text-slate-500 text-[11px] block">Patient Reference ID</span>
                    <span className="font-mono font-bold text-slate-900 text-sm">{verificationResult.patient_ref}</span>
                  </div>
                  <div>
                    <span className="text-slate-500 text-[11px] block">Demographics</span>
                    <span className="text-slate-800 text-xs font-medium">
                      {verificationResult.patient_age_group} • {verificationResult.patient_sex}
                    </span>
                  </div>
                </div>
                <div className="pt-2 border-t border-slate-200 grid grid-cols-2 gap-2 text-xs">
                  <div>
                    <span className="text-slate-500 text-[11px] block">Consultation UUID</span>
                    <span className="font-mono text-[11px] text-slate-700 truncate block">
                      {verificationResult.consultation_id.substring(0, 16)}...
                    </span>
                  </div>
                  <div>
                    <span className="text-slate-500 text-[11px] block">Digitally Signed Date</span>
                    <span className="font-semibold text-slate-800 text-[11px]">{verificationResult.signed_at_formatted}</span>
                  </div>
                </div>
              </div>
            </div>

            {/* Cryptographic Proof & Hash Integrity */}
            <div className="p-5 sm:p-6 bg-emerald-50/40 border-b border-emerald-100 space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold uppercase tracking-wider text-slate-800 flex items-center gap-1.5">
                  <Lock className="w-3.5 h-3.5 text-emerald-700" />
                  Cryptographic Integrity Proof
                </span>
                <span className="text-[11px] text-emerald-800 font-mono font-bold bg-emerald-100/70 px-2 py-0.5 rounded">
                  SHA-256 Authenticated
                </span>
              </div>

              <div className="space-y-2.5">
                <div className="bg-white p-3 rounded-xl border border-slate-200 flex flex-col sm:flex-row sm:items-center justify-between gap-2 shadow-2xs">
                  <div className="min-w-0">
                    <span className="text-[10px] uppercase font-bold text-slate-500 block">Verification Token</span>
                    <span className="font-mono font-bold text-emerald-800 text-xs sm:text-sm tracking-wide break-all">
                      {verificationResult.verification_code}
                    </span>
                  </div>
                  <button
                    type="button"
                    onClick={() => copyToClipboard(verificationResult.verification_code, "code")}
                    className="self-start sm:self-auto px-3 py-1.5 rounded-lg bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-semibold flex items-center gap-1.5 transition-colors cursor-pointer border border-slate-200"
                  >
                    {copiedCode ? <Check className="w-3.5 h-3.5 text-emerald-600" /> : <Copy className="w-3.5 h-3.5" />}
                    <span>{copiedCode ? "Copied" : "Copy Token"}</span>
                  </button>
                </div>

                <div className="bg-white p-3 rounded-xl border border-slate-200 flex flex-col sm:flex-row sm:items-center justify-between gap-2 shadow-2xs">
                  <div className="min-w-0">
                    <span className="text-[10px] uppercase font-bold text-slate-500 block">Digital SHA-256 Digest</span>
                    <span className="font-mono text-slate-700 text-xs break-all">
                      {verificationResult.sha256_hash}
                    </span>
                  </div>
                  <button
                    type="button"
                    onClick={() => copyToClipboard(verificationResult.sha256_hash, "hash")}
                    className="self-start sm:self-auto px-3 py-1.5 rounded-lg bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-semibold flex items-center gap-1.5 transition-colors cursor-pointer border border-slate-200"
                  >
                    {copiedHash ? <Check className="w-3.5 h-3.5 text-emerald-600" /> : <Copy className="w-3.5 h-3.5" />}
                    <span>{copiedHash ? "Copied" : "Copy Digest"}</span>
                  </button>
                </div>
              </div>
            </div>

            {/* Document Certified Sections Summary */}
            {verificationResult.sections_summary && verificationResult.sections_summary.length > 0 && (
              <div className="p-5 sm:p-6 border-b border-slate-100">
                <h4 className="text-xs font-bold uppercase tracking-wider text-slate-700 mb-3 flex items-center gap-2">
                  <FileText className="w-4 h-4 text-indigo-600" />
                  Certified Sections in this Document ({verificationResult.sections_summary.length})
                </h4>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                  {verificationResult.sections_summary.map((sec, idx) => (
                    <div
                      key={idx}
                      className="px-3 py-2 rounded-xl bg-slate-50 border border-slate-200 text-xs text-slate-800 flex items-center gap-2 font-medium"
                    >
                      <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600 shrink-0" />
                      <span className="truncate">{sec}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Actions Bar */}
            <div className="p-5 sm:p-6 bg-slate-50 flex flex-wrap items-center justify-between gap-4">
              <div className="flex items-center gap-2 text-xs text-slate-600 font-medium">
                <Building className="w-4 h-4 text-slate-500" />
                <span>{verificationResult.institution}</span>
              </div>

              <div className="flex items-center gap-2.5">
                <button
                  type="button"
                  onClick={() => window.print()}
                  className="px-3.5 py-2 rounded-xl text-xs font-bold bg-white hover:bg-slate-100 text-slate-800 border border-slate-300 transition-colors flex items-center gap-1.5 cursor-pointer shadow-2xs"
                >
                  <Printer className="w-3.5 h-3.5 text-slate-600" />
                  <span>Print Certificate</span>
                </button>

                <button
                  type="button"
                  onClick={() => handleDownload("pdf")}
                  disabled={downloadingFormat !== null}
                  className="px-4 py-2 rounded-xl text-xs font-bold bg-rose-600 hover:bg-rose-700 text-white transition-all shadow-xs flex items-center gap-1.5 cursor-pointer disabled:opacity-50"
                >
                  {downloadingFormat === "pdf" ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : <Download className="w-3.5 h-3.5" />}
                  <span>Download PDF</span>
                </button>

                <button
                  type="button"
                  onClick={() => handleDownload("docx")}
                  disabled={downloadingFormat !== null}
                  className="px-4 py-2 rounded-xl text-xs font-bold bg-indigo-600 hover:bg-indigo-700 text-white transition-all shadow-xs flex items-center gap-1.5 cursor-pointer disabled:opacity-50"
                >
                  {downloadingFormat === "docx" ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : <Download className="w-3.5 h-3.5" />}
                  <span>Download DOCX</span>
                </button>
              </div>
            </div>
          </div>
        )}
      </main>

      {/* Footer - Clean Hospital White */}
      <footer className="border-t border-slate-200 py-6 text-center text-xs text-slate-500 bg-white">
        <p>DocAssistIQ Health Systems • Cryptographic Integrity Audit Service • HIPAA &amp; NDHM Compliant</p>
      </footer>
    </div>
  );
}

export default function VerifyPortalPage() {
  return (
    <Suspense
      fallback={
        <div className="min-h-screen bg-slate-50 flex items-center justify-center text-slate-600 text-sm">
          Loading Verification Portal...
        </div>
      }
    >
      <VerifyPortalContent />
    </Suspense>
  );
}
