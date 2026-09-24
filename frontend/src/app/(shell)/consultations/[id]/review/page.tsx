/* eslint-disable @typescript-eslint/no-unused-vars */
"use client";

import { useParams } from "next/navigation";
import NoteReviewWorkspace from "@/components/clinical/NoteReviewWorkspace";
import Link from "next/link";

export default function NoteReviewPage() {
  const params = useParams();
  const id = Array.isArray(params.id) ? params.id[0] : params.id;

  if (!id) {
    return <div className="p-8 text-red-500">Invalid Consultation ID</div>;
  }

  return (
    <div className="flex flex-col h-full bg-slate-50/50">
      <div className="px-6 py-4 border-b border-slate-200/80 bg-white/80 backdrop-blur-xl shadow-sm flex items-center justify-between shrink-0">
        <div>
          <h1 className="text-xl font-bold text-slate-900 tracking-tight font-heading">Note Review Workspace</h1>
          <p className="text-sm text-slate-500 mt-0.5 font-medium">Review AI extracted facts, transcript, and draft clinical note.</p>
        </div>
        <div className="flex gap-3 items-center">
          <Link 
            href={`/consultations/${id}`}
            className="px-4 py-2 text-sm font-semibold text-slate-700 bg-white border border-slate-200 rounded-xl shadow-sm hover:bg-slate-50 transition-colors"
          >
            ← Back to Consultation
          </Link>
          <Link 
            href={`/consultations/${id}`}
            className="px-4 py-2 text-sm font-semibold text-white bg-teal-600 hover:bg-teal-700 rounded-xl shadow-md shadow-teal-600/20 transition-all"
          >
            Finalize Note
          </Link>
        </div>
      </div>
      <div className="flex-1 p-6 overflow-hidden">
        <NoteReviewWorkspace consultationId={id} />
      </div>
    </div>
  );
}
