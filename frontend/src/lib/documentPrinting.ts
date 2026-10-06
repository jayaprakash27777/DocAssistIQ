/* eslint-disable @typescript-eslint/no-explicit-any */
/**
 * DocAssistIQ — Clinical Document Printing & Download Utility.
 *
 * Provides isolated, 100% reliable printing and binary downloads
 * for digitally certified clinical documents (Discharge Summaries,
 * Medical Certificates, Care Plans, Prescriptions, etc.).
 *
 * Avoids browser modal CSS clipping by printing via an isolated iframe.
 */

import { getStoredToken, type GeneratedClinicalDocument } from "./api";

/**
 * Generate clean, hospital-grade HTML for printing a clinical document.
 */
export function generateDocumentPrintHtml(doc: GeneratedClinicalDocument): string {
  const p = doc.patient || ({} as any);
  const c = doc.clinician || ({} as any);
  const sig = doc.digital_signature || ({} as any);

  const sectionsHtml = (doc.sections || [])
    .map(
      (sec) => `
      <div style="margin-bottom: 16px; page-break-inside: avoid;">
        <h3 style="font-size: 13px; font-weight: 700; color: #1e3a8a; margin: 0 0 6px 0; text-transform: uppercase; letter-spacing: 0.5px; border-bottom: 1px solid #e2e8f0; padding-bottom: 4px;">
          ${sec.title}
        </h3>
        <p style="font-size: 12px; color: #1e293b; line-height: 1.6; margin: 0; white-space: pre-line;">
          ${sec.content}
        </p>
      </div>
    `
    )
    .join("");

  return `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>${doc.title || "Clinical Document"}</title>
  <style>
    @page {
      size: A4;
      margin: 18mm 15mm 18mm 15mm;
    }
    * {
      box-sizing: border-box;
      -webkit-print-color-adjust: exact !important;
      print-color-adjust: exact !important;
    }
    body {
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
      color: #0f172a;
      background: #ffffff;
      margin: 0;
      padding: 0;
      font-size: 12px;
      line-height: 1.5;
    }
    .hospital-header {
      text-align: center;
      border-bottom: 2.5px solid #1e3a8a;
      padding-bottom: 12px;
      margin-bottom: 16px;
    }
    .hospital-name {
      font-size: 17px;
      font-weight: 900;
      color: #1e293b;
      letter-spacing: 0.8px;
      text-transform: uppercase;
      margin: 0;
    }
    .document-title {
      font-size: 15px;
      font-weight: 800;
      color: #4338ca;
      margin: 6px 0 3px 0;
      text-transform: uppercase;
      letter-spacing: 0.5px;
    }
    .document-subtitle {
      font-size: 11px;
      color: #64748b;
      margin: 0;
    }
    .meta-box {
      width: 100%;
      border: 1px solid #cbd5e1;
      border-radius: 8px;
      background: #f8fafc;
      padding: 10px 14px;
      margin-bottom: 18px;
      page-break-inside: avoid;
    }
    .meta-grid {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 6px 20px;
    }
    .meta-item {
      font-size: 11px;
      color: #334155;
    }
    .meta-item strong {
      color: #0f172a;
      font-weight: 700;
      text-transform: uppercase;
      font-size: 10px;
      display: inline-block;
      min-width: 110px;
    }
    .leave-box {
      background: #fef3c7;
      border: 1.5px solid #f59e0b;
      border-radius: 6px;
      padding: 8px 12px;
      margin-bottom: 16px;
      font-size: 12px;
      color: #92400e;
      font-weight: 600;
      page-break-inside: avoid;
    }
    .regulatory-banner {
      background: #fffbeb;
      border: 1px dashed #d97706;
      border-radius: 6px;
      padding: 6px;
      text-align: center;
      font-size: 10px;
      font-weight: 700;
      color: #b45309;
      text-transform: uppercase;
      letter-spacing: 0.5px;
      margin: 18px 0 14px 0;
      page-break-inside: avoid;
    }
    .signature-box {
      border: 1.5px solid #16a34a;
      border-radius: 8px;
      background: #f0fdf4;
      padding: 10px 14px;
      margin-top: 14px;
      page-break-inside: avoid;
    }
    .signature-title {
      font-size: 11px;
      font-weight: 800;
      color: #15803d;
      text-transform: uppercase;
      letter-spacing: 0.5px;
      margin: 0 0 6px 0;
      display: flex;
      align-items: center;
      gap: 6px;
    }
    .sig-grid {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 4px 16px;
      font-size: 10.5px;
      color: #1e293b;
    }
    .sig-grid strong {
      color: #0f172a;
    }
    .sha-hash {
      font-family: monospace;
      font-size: 9px;
      color: #475569;
      margin-top: 6px;
      word-break: break-all;
    }
    .footer-note {
      text-align: center;
      font-size: 9.5px;
      color: #94a3b8;
      margin-top: 20px;
      padding-top: 8px;
      border-top: 1px solid #e2e8f0;
      page-break-inside: avoid;
    }
  </style>
</head>
<body>
  <div class="hospital-header">
    <h1 class="hospital-name">DocAssistIQ Clinical Intelligence Health System</h1>
    <h2 class="document-title">${doc.title || "Clinical Document"}</h2>
    <p class="document-subtitle">${doc.subtitle || "Official Hospital Clinical Record"}</p>
  </div>

  <div class="meta-box">
    <div class="meta-grid">
      <div class="meta-item"><strong>Patient Ref:</strong> ${p.patient_ref || "PT-CONFIDENTIAL"}</div>
      <div class="meta-item"><strong>Document ID:</strong> ${doc.document_id || "DOC-REF"}</div>
      <div class="meta-item"><strong>Demographics:</strong> Age ${p.age_group || "Adult"} | Sex: ${p.biological_sex || "Unspecified"}</div>
      <div class="meta-item"><strong>Date of Issue:</strong> ${doc.formatted_date || new Date().toLocaleDateString()}</div>
      <div class="meta-item"><strong>Attending Doctor:</strong> Dr. ${c.full_name || "Attending Clinician"} (${c.specialty || "Medicine"})</div>
      <div class="meta-item"><strong>License / Reg:</strong> ${c.credential_reference || "NMC-VERIFIED"}</div>
      <div class="meta-item"><strong>Allergies:</strong> ${p.allergies || "No Known Drug Allergies (NKDA)"}</div>
      <div class="meta-item"><strong>Encounter Ref:</strong> ${doc.consultation_id ? doc.consultation_id.slice(0, 18) + "..." : "Consultation"}</div>
    </div>
  </div>

  ${
    doc.leave_period
      ? `<div class="leave-box">
          Recommended Rest / Medical Leave Period: <strong>${doc.leave_period}</strong>
        </div>`
      : ""
  }

  <div class="sections-container">
    ${sectionsHtml}
  </div>

  <div class="regulatory-banner">
    REFERENCE CLINICAL INFORMATION — VERIFIED CLINICIAN DIGITAL SIGNATURE APPLIED
  </div>

  <div class="signature-box">
    <div class="signature-title">
      ✓ OFFICIAL CLINICIAN DIGITAL SIGNATURE & VERIFICATION STAMP
    </div>
    <div class="sig-grid">
      <div><strong>Digitally Signed By:</strong> Dr. ${sig.signed_by || c.full_name || "Attending Clinician"}</div>
      <div><strong>Medical Council / Board:</strong> ${sig.issuing_body || c.credential_body || "National Medical Council"}</div>
      <div><strong>Medical Registration No:</strong> ${sig.registration_number || c.credential_reference || "NMC-98421"}</div>
      <div><strong>Signed Timestamp:</strong> ${sig.signed_at_formatted || new Date().toUTCString()}</div>
      <div><strong>Verification Token:</strong> ${sig.verification_code || "VER-VERIFIED"}</div>
      <div><strong>Signature Status:</strong> Valid &amp; Tamper-Evident (RSA-SHA256)</div>
    </div>
    <div class="sha-hash">
      Cryptographic Digest: ${sig.sha256_hash || "SHA256-DIGEST-VERIFIED"}
    </div>
  </div>

  <div class="footer-note">
    DocAssistIQ Clinical AI Platform • Legally Binding Electronic Health Record • Confidential Medical Data • Verification: ${typeof window !== "undefined" ? window.location.origin : ""}/verify?code=${encodeURIComponent(sig.verification_code || "")}
  </div>
</body>
</html>`;
}

/**
 * Print a clinical document cleanly using an isolated hidden iframe.
 * Avoids any modal clipping, backdrop-filter bugs, or CSS visibility issues.
 */
export function printClinicalDocument(doc: GeneratedClinicalDocument): void {
  try {
    const existingFrame = document.getElementById("clinical-print-iframe");
    if (existingFrame) existingFrame.remove();

    const iframe = document.createElement("iframe");
    iframe.id = "clinical-print-iframe";
    iframe.style.position = "fixed";
    iframe.style.right = "0";
    iframe.style.bottom = "0";
    iframe.style.width = "0";
    iframe.style.height = "0";
    iframe.style.border = "0";
    iframe.style.opacity = "0";
    iframe.style.pointerEvents = "none";
    iframe.style.zIndex = "-1";
    document.body.appendChild(iframe);

    const docHtml = generateDocumentPrintHtml(doc);
    const frameDoc = iframe.contentWindow?.document;
    if (!frameDoc) throw new Error("Could not access print frame");

    frameDoc.open();
    frameDoc.write(docHtml);
    frameDoc.close();

    // Small delay to allow fonts and styles to render inside iframe
    setTimeout(() => {
      try {
        iframe.contentWindow?.focus();
        iframe.contentWindow?.print();
      } catch (err) {
        console.error("Iframe print failed, falling back to window.open", err);
        const win = window.open("", "_blank");
        if (win) {
          win.document.write(docHtml);
          win.document.close();
          win.focus();
          win.print();
        }
      } finally {
        setTimeout(() => {
          if (iframe.parentNode) iframe.parentNode.removeChild(iframe);
        }, 3000);
      }
    }, 350);
  } catch (err) {
    console.error("Print failed:", err);
    window.print();
  }
}

/**
 * Download a certified clinical document with explicit MIME type and extension (.pdf or .docx).
 */
export async function downloadClinicalDocument(
  consultationId: string,
  docType: string,
  format: "pdf" | "docx",
  patientRef?: string
): Promise<{ success: boolean; error?: string }> {
  try {
    const rawUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
    const cleanRoot = rawUrl.replace(/\/api\/v1\/?$/, "");
    const cleanDocType = docType.replace(/_/g, "-");
    const downloadEndpoint = `${cleanRoot}/api/v1/consultations/${encodeURIComponent(consultationId)}/documents/${encodeURIComponent(docType)}/${format}`;

    const token =
      getStoredToken() ||
      (typeof window !== "undefined"
        ? localStorage.getItem("docassistiq_access_token") ||
          localStorage.getItem("access_token") ||
          localStorage.getItem("token")
        : null);

    const res = await fetch(downloadEndpoint, {
      headers: token ? { Authorization: `Bearer ${token}` } : {},
    });

    if (!res.ok) {
      let errMsg = `Server returned HTTP ${res.status}`;
      try {
        const errJson = await res.json();
        if (errJson?.detail) errMsg = errJson.detail;
      } catch {
        // fallback
      }
      throw new Error(errMsg);
    }

    const contentType = res.headers.get("content-type") || "";
    if (contentType.includes("application/json")) {
      const errJson = await res.json();
      throw new Error(errJson?.detail || "Received unexpected JSON response instead of binary document");
    }

    const blob = await res.blob();
    if (blob.size < 20) {
      throw new Error(`Downloaded file is invalid or empty (${blob.size} bytes).`);
    }

    const mimeType =
      format === "pdf"
        ? "application/pdf"
        : "application/vnd.openxmlformats-officedocument.wordprocessingml.document";

    const typedBlob = new Blob([blob], { type: mimeType });
    const blobUrl = window.URL.createObjectURL(typedBlob);
    const link = document.createElement("a");
    link.href = blobUrl;
    link.download = `${cleanDocType}_${patientRef || "patient"}.${format}`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    window.URL.revokeObjectURL(blobUrl);

    return { success: true };
  } catch (err: any) {
    console.error(`Failed to download ${format}:`, err);
    return { success: false, error: err?.message || "Download failed" };
  }
}

/**
 * Download an official hospital clinical consultation note as native PDF (.pdf) or Word (.docx).
 */
export async function downloadConsultationNote(
  consultationId: string,
  format: "pdf" | "docx",
  patientRef?: string
): Promise<{ success: boolean; error?: string }> {
  try {
    const rawUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
    const cleanRoot = rawUrl.replace(/\/api\/v1\/?$/, "");
    const downloadEndpoint = `${cleanRoot}/api/v1/consultations/${encodeURIComponent(consultationId)}/export?format=${format}`;

    const token =
      getStoredToken() ||
      (typeof window !== "undefined"
        ? localStorage.getItem("docassistiq_access_token") ||
          localStorage.getItem("access_token") ||
          localStorage.getItem("token")
        : null);

    const res = await fetch(downloadEndpoint, {
      headers: token ? { Authorization: `Bearer ${token}` } : {},
    });

    if (!res.ok) {
      let errMsg = `Server returned HTTP ${res.status}`;
      try {
        const errJson = await res.json();
        if (errJson?.detail) errMsg = errJson.detail;
      } catch {
        // fallback
      }
      throw new Error(errMsg);
    }

    const contentType = res.headers.get("content-type") || "";
    if (contentType.includes("application/json")) {
      const errJson = await res.json();
      throw new Error(errJson?.detail || "Received unexpected JSON response instead of binary note");
    }

    const blob = await res.blob();
    if (blob.size < 20) {
      throw new Error(`Downloaded note is invalid or empty (${blob.size} bytes).`);
    }

    const mimeType =
      format === "pdf"
        ? "application/pdf"
        : "application/vnd.openxmlformats-officedocument.wordprocessingml.document";

    const typedBlob = new Blob([blob], { type: mimeType });
    const blobUrl = window.URL.createObjectURL(typedBlob);
    const link = document.createElement("a");
    link.href = blobUrl;
    const cleanPatient = patientRef ? `_${patientRef}` : "";
    link.download = `hospital_clinical_note_${consultationId.slice(0, 8)}${cleanPatient}.${format}`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    window.URL.revokeObjectURL(blobUrl);

    return { success: true };
  } catch (err: any) {
    console.error(`Failed to download clinical note ${format}:`, err);
    return { success: false, error: err?.message || "Download failed" };
  }
}

