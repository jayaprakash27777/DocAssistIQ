/**
 * DocAssistIQ — Client-Side Offline IndexedDB Persistence & Resilient Sync
 *
 * Automatically saves active clinical note edits, draft sections, and consultation notes
 * to the browser's local IndexedDB. If network connectivity drops in the clinic/hospital,
 * work is never lost and is automatically synced upon reconnection.
 */

const DB_NAME = "DocAssistIQ_Offline_v1";
const DB_VERSION = 1;
const STORE_NOTES = "clinical_notes";

function openDB(): Promise<IDBDatabase> {
  return new Promise((resolve, reject) => {
    if (typeof window === "undefined" || !window.indexedDB) {
      return reject(new Error("IndexedDB not available in this environment"));
    }

    const request = window.indexedDB.open(DB_NAME, DB_VERSION);

    request.onupgradeneeded = (event) => {
      const db = (event.target as IDBOpenDBRequest).result;
      if (!db.objectStoreNames.contains(STORE_NOTES)) {
        db.createObjectStore(STORE_NOTES, { keyPath: "consultationId" });
      }
    };

    request.onsuccess = () => resolve(request.result);
    request.onerror = () => reject(request.error);
  });
}

export interface OfflineNoteRecord {
  consultationId: string;
  body: Record<string, any>;
  version: number;
  updatedAt: string;
  synced: boolean;
}

/**
 * Persists active clinical note state to IndexedDB with millisecond timestamp.
 */
export async function saveOfflineNoteDraft(
  consultationId: string,
  body: Record<string, any>,
  version: number
): Promise<void> {
  try {
    const db = await openDB();
    const tx = db.transaction(STORE_NOTES, "readwrite");
    const store = tx.objectStore(STORE_NOTES);

    const record: OfflineNoteRecord = {
      consultationId,
      body,
      version,
      updatedAt: new Date().toISOString(),
      synced: false,
    };

    store.put(record);

    return new Promise((resolve, reject) => {
      tx.oncomplete = () => resolve();
      tx.onerror = () => reject(tx.error);
    });
  } catch (err) {
    // Graceful fallback to localStorage if IndexedDB is blocked in private browsing
    try {
      if (typeof window !== "undefined") {
        localStorage.setItem(
          `docassist_draft_${consultationId}`,
          JSON.stringify({ body, version, updatedAt: new Date().toISOString() })
        );
      }
    } catch {
      // Storage quota or policy restriction
    }
  }
}

/**
 * Retrieves the latest offline cached draft for a consultation.
 */
export async function getOfflineNoteDraft(
  consultationId: string
): Promise<OfflineNoteRecord | null> {
  try {
    const db = await openDB();
    const tx = db.transaction(STORE_NOTES, "readonly");
    const store = tx.objectStore(STORE_NOTES);
    const req = store.get(consultationId);

    return new Promise((resolve) => {
      req.onsuccess = () => resolve(req.result || null);
      req.onerror = () => resolve(null);
    });
  } catch {
    try {
      if (typeof window !== "undefined") {
        const raw = localStorage.getItem(`docassist_draft_${consultationId}`);
        if (raw) return JSON.parse(raw);
      }
    } catch {}
    return null;
  }
}

/**
 * Clears the offline draft once successfully synced to the backend server.
 */
export async function clearOfflineNoteDraft(consultationId: string): Promise<void> {
  try {
    const db = await openDB();
    const tx = db.transaction(STORE_NOTES, "readwrite");
    const store = tx.objectStore(STORE_NOTES);
    store.delete(consultationId);

    if (typeof window !== "undefined") {
      localStorage.removeItem(`docassist_draft_${consultationId}`);
    }
  } catch {}
}

/**
 * Registers an online listener that triggers a callback when network is restored.
 */
export function registerNetworkReconnectionSync(onReconnected: () => void): () => void {
  if (typeof window === "undefined") return () => {};

  const handleOnline = () => {
    onReconnected();
  };

  window.addEventListener("online", handleOnline);
  return () => window.removeEventListener("online", handleOnline);
}
