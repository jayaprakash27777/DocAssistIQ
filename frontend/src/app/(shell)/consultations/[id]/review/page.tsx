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
    <div className="flex flex-col h-full bg-gray-50">
      <div className="px-6 py-4 border-b bg-white shadow-sm flex items-center justify-between shrink-0">
        <div>
          <h1 className="text-xl font-bold text-gray-900 tracking-tight">Note Review Workspace</h1>
          <p className="text-sm text-gray-500 mt-1">Review AI extracted facts, transcript, and draft clinical note.</p>
        </div>
        <div className="flex gap-3">
          <Link 
            href={`/consultations/${id}`}
            className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md shadow-sm hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 transition-colors"
          >
            Back to Consultation
          </Link>
          <Link 
            href={`/consultations/${id}`}
            className="px-4 py-2 text-sm font-medium text-white bg-blue-600 border border-transparent rounded-md shadow-sm hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 transition-colors"
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
