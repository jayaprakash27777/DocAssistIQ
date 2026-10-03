"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useAuth } from "@/lib/auth-context";
import {
  getAdminUsers,
  updateAdminUser,
  type AdminUserItem,
} from "@/lib/api";
import { useToast } from "@/components/shell/ToastProvider";
import {
  Users,
  Shield,
  Search,
  Filter,
  CheckCircle2,
  XCircle,
  ArrowLeft,
  RefreshCw,
  KeyRound,
  UserCheck,
  UserX,
  ChevronLeft,
  ChevronRight,
  ShieldAlert,
} from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";

export default function AdminUsersPage() {
  const { user: currentUser } = useAuth();
  const { toast } = useToast();

  const [users, setUsers] = useState<AdminUserItem[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [pages, setPages] = useState(1);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [roleFilter, setRoleFilter] = useState<string>("");
  const [statusFilter, setStatusFilter] = useState<string>("");
  const [lastUpdated, setLastUpdated] = useState<Date>(new Date());

  // Action states
  const [modifyingId, setModifyingId] = useState<string | null>(null);
  const [selectedPermissionsUser, setSelectedPermissionsUser] = useState<AdminUserItem | null>(null);

  const PAGE_SIZE = 15;
  const isAdmin = currentUser?.role === "admin" || currentUser?.role === "super_admin";

  const fetchUsers = async () => {
    setLoading(true);
    const res = await getAdminUsers({
      page,
      page_size: PAGE_SIZE,
      search: search.trim() || undefined,
      role: roleFilter || undefined,
      is_active: statusFilter === "active" ? true : statusFilter === "suspended" ? false : undefined,
    });

    if (res.ok) {
      setUsers(res.data.items);
      setTotal(res.data.total);
      setPages(res.data.pages);
      setLastUpdated(new Date());
    } else {
      toast.error(res.error?.message || "Failed to load user directory.");
    }
    setLoading(false);
  };

  useEffect(() => {
    if (!isAdmin) return;
    fetchUsers();
  }, [page, roleFilter, statusFilter, isAdmin]);

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setPage(1);
    fetchUsers();
  };

  const handleRoleChange = async (targetUser: AdminUserItem, newRole: string) => {
    if (modifyingId) return;
    if (targetUser.id === currentUser?.id) {
      toast.error("You cannot change your own administrative role.");
      return;
    }

    setModifyingId(targetUser.id);
    const res = await updateAdminUser(targetUser.id, { role: newRole });
    if (res.ok) {
      toast.success(`Successfully assigned role "${newRole}" to ${targetUser.email}.`);
      setUsers((prev) =>
        prev.map((u) => (u.id === targetUser.id ? { ...u, role: newRole, permissions: res.data.permissions } : u))
      );
    } else {
      toast.error(res.error?.message || "Failed to update role.");
    }
    setModifyingId(null);
  };

  const handleStatusToggle = async (targetUser: AdminUserItem) => {
    if (modifyingId) return;
    if (targetUser.id === currentUser?.id) {
      toast.error("You cannot suspend your own account.");
      return;
    }

    const nextStatus = !targetUser.is_active;
    setModifyingId(targetUser.id);
    const res = await updateAdminUser(targetUser.id, { is_active: nextStatus });
    if (res.ok) {
      if (nextStatus) {
        toast.success(`Account for ${targetUser.email} has been activated.`);
      } else {
        toast.info(`Account for ${targetUser.email} has been suspended.`);
      }
      setUsers((prev) =>
        prev.map((u) => (u.id === targetUser.id ? { ...u, is_active: nextStatus } : u))
      );
    } else {
      toast.error(res.error?.message || "Failed to update account status.");
    }
    setModifyingId(null);
  };

  if (!currentUser) return null;

  if (!isAdmin) {
    return (
      <div className="min-h-[70vh] flex items-center justify-center p-8">
        <div className="glass-panel-4k p-10 rounded-3xl border border-slate-200/90 bg-white/85 backdrop-blur-2xl shadow-xl max-w-md text-center">
          <div className="w-16 h-16 rounded-2xl bg-amber-50 text-amber-600 flex items-center justify-center mx-auto mb-4 border border-amber-200">
            <ShieldAlert size={32} />
          </div>
          <h2 className="text-2xl font-bold text-slate-900 mb-2 font-heading">
            Administrator Access Required
          </h2>
          <p className="text-slate-500 mb-6 text-sm">
            Only platform administrators can access the User Directory & RBAC Governance module.
          </p>
          <Link
            href="/admin"
            className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-slate-900 hover:bg-slate-800 text-white font-semibold text-sm transition-colors"
          >
            Return to Command Center
          </Link>
        </div>
      </div>
    );
  }

  // Count summaries from loaded items
  const doctorCount = users.filter((u) => u.role === "doctor").length;
  const adminCount = users.filter((u) => u.role === "admin" || u.role === "super_admin").length;
  const suspendedCount = users.filter((u) => !u.is_active).length;

  return (
    <div className="min-h-screen bg-slate-50 relative overflow-hidden p-6 md:p-8 pt-8">
      {/* Background accents */}
      <div className="absolute top-[-10%] right-[-10%] w-[45%] h-[45%] bg-purple-300/15 rounded-full blur-3xl pointer-events-none" />
      <div className="absolute bottom-[-10%] left-[-10%] w-[40%] h-[40%] bg-blue-300/15 rounded-full blur-3xl pointer-events-none" />

      <div className="max-w-7xl mx-auto space-y-8 relative z-10">
        
        {/* Navigation & Header */}
        <header className="space-y-4">
          <div className="flex items-center gap-2 text-sm text-slate-500">
            <Link
              href="/admin"
              className="inline-flex items-center gap-1 text-slate-600 hover:text-slate-900 font-semibold transition-colors"
            >
              <ArrowLeft size={16} /> Command Center
            </Link>
            <span>/</span>
            <span className="text-slate-900 font-bold">User Directory & RBAC</span>
          </div>

          <div className="flex flex-col md:flex-row md:items-end justify-between gap-4">
            <div>
              <div className="flex items-center gap-3 mb-2">
                <div className="p-2.5 bg-violet-500/10 rounded-xl border border-violet-500/20 text-violet-600">
                  <Users size={28} />
                </div>
                <h1 className="text-3xl md:text-4xl font-bold text-slate-900 tracking-tight font-heading">
                  User Directory & RBAC Governance
                </h1>
              </div>
              <p className="text-slate-500 text-sm md:text-base font-medium max-w-2xl">
                Real-time user authorization, role transitions, account active status, and HIPAA access compliance.
              </p>
            </div>

            <div className="flex items-center gap-3">
              <button
                onClick={fetchUsers}
                disabled={loading}
                className="px-3.5 py-2 rounded-xl bg-white border border-slate-200 text-slate-700 hover:bg-slate-50 font-semibold text-xs transition-all shadow-sm flex items-center gap-2"
              >
                <RefreshCw size={14} className={loading ? "animate-spin" : ""} />
                Refresh Feed
              </button>
              <div className="text-xs text-slate-500 font-mono">
                Updated: {lastUpdated.toLocaleTimeString([], { hour12: false, hour: "2-digit", minute: "2-digit", second: "2-digit" })}
              </div>
            </div>
          </div>
        </header>

        {/* Quick Metrics Bar */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="p-4 rounded-2xl bg-white/80 border border-slate-200/80 shadow-sm">
            <span className="text-xs font-bold text-slate-500 uppercase tracking-wider block mb-1">Total Registered</span>
            <span className="text-3xl font-extrabold text-slate-900 font-heading">{total}</span>
          </div>
          <div className="p-4 rounded-2xl bg-white/80 border border-slate-200/80 shadow-sm">
            <span className="text-xs font-bold text-slate-500 uppercase tracking-wider block mb-1">Clinician Doctors</span>
            <span className="text-3xl font-extrabold text-blue-600 font-heading">{doctorCount}</span>
          </div>
          <div className="p-4 rounded-2xl bg-white/80 border border-slate-200/80 shadow-sm">
            <span className="text-xs font-bold text-slate-500 uppercase tracking-wider block mb-1">Administrators</span>
            <span className="text-3xl font-extrabold text-purple-600 font-heading">{adminCount}</span>
          </div>
          <div className="p-4 rounded-2xl bg-white/80 border border-slate-200/80 shadow-sm">
            <span className="text-xs font-bold text-slate-500 uppercase tracking-wider block mb-1">Suspended Accounts</span>
            <span className={`text-3xl font-extrabold font-heading ${suspendedCount > 0 ? "text-amber-600" : "text-slate-800"}`}>
              {suspendedCount}
            </span>
          </div>
        </div>

        {/* Search & Filter Toolbar */}
        <div className="bg-white/80 backdrop-blur-xl border border-slate-200/90 rounded-2xl p-4 shadow-sm flex flex-col md:flex-row items-stretch md:items-center justify-between gap-4">
          {/* Search Form */}
          <form onSubmit={handleSearchSubmit} className="relative flex-grow max-w-md">
            <Search size={16} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400" />
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search by clinician name or email address..."
              className="w-full pl-10 pr-4 py-2 rounded-xl border border-slate-200 text-sm focus:outline-none focus:ring-2 focus:ring-violet-500/20 focus:border-violet-500 bg-white"
            />
          </form>

          {/* Filters */}
          <div className="flex flex-wrap items-center gap-3">
            {/* Role Filter */}
            <div className="flex items-center gap-1.5 bg-slate-100 p-1 rounded-xl text-xs font-semibold">
              <span className="text-slate-400 px-2 flex items-center gap-1">
                <Filter size={12} /> Role:
              </span>
              <button
                onClick={() => { setRoleFilter(""); setPage(1); }}
                className={`px-2.5 py-1 rounded-lg transition-colors ${roleFilter === "" ? "bg-white text-slate-900 shadow-xs font-bold" : "text-slate-600 hover:text-slate-900"}`}
              >
                All
              </button>
              <button
                onClick={() => { setRoleFilter("doctor"); setPage(1); }}
                className={`px-2.5 py-1 rounded-lg transition-colors ${roleFilter === "doctor" ? "bg-white text-blue-700 shadow-xs font-bold" : "text-slate-600 hover:text-slate-900"}`}
              >
                Doctors
              </button>
              <button
                onClick={() => { setRoleFilter("admin"); setPage(1); }}
                className={`px-2.5 py-1 rounded-lg transition-colors ${roleFilter === "admin" ? "bg-white text-purple-700 shadow-xs font-bold" : "text-slate-600 hover:text-slate-900"}`}
              >
                Admins
              </button>
            </div>

            {/* Status Filter */}
            <div className="flex items-center gap-1.5 bg-slate-100 p-1 rounded-xl text-xs font-semibold">
              <span className="text-slate-400 px-2">Status:</span>
              <button
                onClick={() => { setStatusFilter(""); setPage(1); }}
                className={`px-2.5 py-1 rounded-lg transition-colors ${statusFilter === "" ? "bg-white text-slate-900 shadow-xs font-bold" : "text-slate-600 hover:text-slate-900"}`}
              >
                All
              </button>
              <button
                onClick={() => { setStatusFilter("active"); setPage(1); }}
                className={`px-2.5 py-1 rounded-lg transition-colors ${statusFilter === "active" ? "bg-white text-emerald-700 shadow-xs font-bold" : "text-slate-600 hover:text-slate-900"}`}
              >
                Active
              </button>
              <button
                onClick={() => { setStatusFilter("suspended"); setPage(1); }}
                className={`px-2.5 py-1 rounded-lg transition-colors ${statusFilter === "suspended" ? "bg-white text-rose-700 shadow-xs font-bold" : "text-slate-600 hover:text-slate-900"}`}
              >
                Suspended
              </button>
            </div>
          </div>
        </div>

        {/* User Directory Table */}
        <div className="bg-white/90 backdrop-blur-xl border border-slate-200/90 rounded-3xl shadow-xl shadow-slate-200/50 overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="border-b border-slate-200 bg-slate-50/70 text-xs font-bold text-slate-500 uppercase tracking-wider">
                  <th className="py-4 px-6">User / Clinician</th>
                  <th className="py-4 px-6">Role (RBAC)</th>
                  <th className="py-4 px-6">Status</th>
                  <th className="py-4 px-6">Permissions</th>
                  <th className="py-4 px-6">Joined Date</th>
                  <th className="py-4 px-6 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 text-sm">
                {loading && users.length === 0 ? (
                  <tr>
                    <td colSpan={6} className="py-12 text-center text-slate-400">
                      <RefreshCw size={24} className="animate-spin mx-auto mb-2 text-violet-500" />
                      Loading user directory...
                    </td>
                  </tr>
                ) : users.length === 0 ? (
                  <tr>
                    <td colSpan={6} className="py-12 text-center text-slate-400">
                      <Users size={32} className="mx-auto mb-2 text-slate-300" />
                      No registered users match the selected filters.
                    </td>
                  </tr>
                ) : (
                  users.map((item) => {
                    const isSelf = item.id === currentUser?.id;
                    const isModifying = modifyingId === item.id;

                    return (
                      <tr key={item.id} className="hover:bg-slate-50/60 transition-colors">
                        {/* User / Email */}
                        <td className="py-4 px-6">
                          <div className="flex items-center gap-3">
                            <div className="w-10 h-10 rounded-2xl bg-gradient-to-br from-violet-100 to-indigo-100 text-violet-700 font-bold flex items-center justify-center border border-violet-200 shadow-xs shrink-0">
                              {item.full_name?.charAt(0)?.toUpperCase() || item.email.charAt(0).toUpperCase()}
                            </div>
                            <div>
                              <div className="font-bold text-slate-900 flex items-center gap-1.5">
                                <span>{item.full_name || "Unnamed Clinician"}</span>
                                {isSelf && (
                                  <span className="text-[10px] bg-slate-900 text-white font-semibold px-1.5 py-0.2 rounded">
                                    You
                                  </span>
                                )}
                              </div>
                              <div className="text-xs text-slate-500 font-mono">{item.email}</div>
                            </div>
                          </div>
                        </td>

                        {/* Role (RBAC) */}
                        <td className="py-4 px-6">
                          <div className="flex items-center gap-2">
                            <span className={`inline-flex items-center gap-1 px-2.5 py-1 rounded-lg text-xs font-bold ${
                              item.role === "admin" || item.role === "super_admin"
                                ? "bg-purple-100 text-purple-800 border border-purple-200"
                                : "bg-blue-100 text-blue-800 border border-blue-200"
                            }`}>
                              <Shield size={12} />
                              {item.role.toUpperCase()}
                            </span>

                            {/* Role selector dropdown */}
                            {!isSelf && (
                              <select
                                value={item.role}
                                disabled={isModifying}
                                onChange={(e) => handleRoleChange(item, e.target.value)}
                                className="text-xs bg-white border border-slate-200 rounded-lg px-2 py-1 text-slate-700 hover:border-slate-300 focus:outline-none focus:ring-1 focus:ring-violet-500 disabled:opacity-50"
                              >
                                <option value="doctor">Doctor</option>
                                <option value="admin">Admin</option>
                                <option value="super_admin">Super Admin</option>
                              </select>
                            )}
                          </div>
                        </td>

                        {/* Status */}
                        <td className="py-4 px-6">
                          <span className={`inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-bold ${
                            item.is_active
                              ? "bg-emerald-100 text-emerald-800 border border-emerald-200"
                              : "bg-rose-100 text-rose-800 border border-rose-200"
                          }`}>
                            {item.is_active ? <CheckCircle2 size={12} /> : <XCircle size={12} />}
                            {item.is_active ? "Active" : "Suspended"}
                          </span>
                        </td>

                        {/* Permissions Badge */}
                        <td className="py-4 px-6">
                          <button
                            onClick={() => setSelectedPermissionsUser(item)}
                            className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-semibold transition-colors"
                          >
                            <KeyRound size={12} className="text-violet-500" />
                            <span>{item.permissions?.length || 0} Permissions</span>
                          </button>
                        </td>

                        {/* Joined Date */}
                        <td className="py-4 px-6 text-xs text-slate-500 font-mono">
                          {new Date(item.created_at).toLocaleDateString(undefined, {
                            year: "numeric",
                            month: "short",
                            day: "numeric",
                          })}
                        </td>

                        {/* Actions */}
                        <td className="py-4 px-6 text-right">
                          <div className="flex items-center justify-end gap-2">
                            {!isSelf ? (
                              <button
                                onClick={() => handleStatusToggle(item)}
                                disabled={isModifying}
                                className={`px-3 py-1.5 rounded-xl text-xs font-bold transition-all flex items-center gap-1.5 ${
                                  item.is_active
                                    ? "bg-rose-50 text-rose-700 hover:bg-rose-100 border border-rose-200 disabled:opacity-50"
                                    : "bg-emerald-50 text-emerald-700 hover:bg-emerald-100 border border-emerald-200 disabled:opacity-50"
                                }`}
                              >
                                {isModifying ? (
                                  <RefreshCw size={12} className="animate-spin" />
                                ) : item.is_active ? (
                                  <>
                                    <UserX size={13} /> Suspend
                                  </>
                                ) : (
                                  <>
                                    <UserCheck size={13} /> Activate
                                  </>
                                )}
                              </button>
                            ) : (
                              <span className="text-xs text-slate-400 font-medium italic">Current User</span>
                            )}
                          </div>
                        </td>
                      </tr>
                    );
                  })
                )}
              </tbody>
            </table>
          </div>

          {/* Pagination Footer */}
          <div className="p-4 border-t border-slate-200/80 bg-slate-50/50 flex items-center justify-between text-xs text-slate-600">
            <div>
              Showing page <strong>{page}</strong> of <strong>{pages || 1}</strong> ({total} total users)
            </div>
            <div className="flex items-center gap-2">
              <button
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                disabled={page <= 1 || loading}
                className="p-1.5 rounded-lg border border-slate-200 bg-white hover:bg-slate-50 disabled:opacity-40 transition-colors"
              >
                <ChevronLeft size={16} />
              </button>
              <button
                onClick={() => setPage((p) => Math.min(pages, p + 1))}
                disabled={page >= pages || loading}
                className="p-1.5 rounded-lg border border-slate-200 bg-white hover:bg-slate-50 disabled:opacity-40 transition-colors"
              >
                <ChevronRight size={16} />
              </button>
            </div>
          </div>
        </div>

        {/* Regulatory Watermark */}
        <div className="py-2 text-center">
          <span className="text-[11px] font-bold tracking-wider text-slate-500 uppercase bg-slate-100 px-3 py-1 rounded-full border border-slate-200">
            REFERENCE INFORMATION — CLINICIAN REVIEW REQUIRED
          </span>
        </div>

      </div>

      {/* Permissions Inspection Modal */}
      <AnimatePresence>
        {selectedPermissionsUser && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/40 backdrop-blur-xs">
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.95 }}
              className="bg-white rounded-3xl p-6 shadow-2xl border border-slate-200 max-w-lg w-full space-y-4"
            >
              <div className="flex items-center justify-between border-b border-slate-100 pb-3">
                <div className="flex items-center gap-2">
                  <KeyRound size={20} className="text-violet-600" />
                  <h3 className="font-bold text-slate-900 font-heading">
                    Assigned RBAC Permissions
                  </h3>
                </div>
                <button
                  onClick={() => setSelectedPermissionsUser(null)}
                  className="p-1 rounded-lg text-slate-400 hover:text-slate-600 hover:bg-slate-100"
                >
                  <XCircle size={18} />
                </button>
              </div>

              <div>
                <div className="text-sm font-semibold text-slate-800 mb-1">
                  {selectedPermissionsUser.full_name || selectedPermissionsUser.email}
                </div>
                <div className="text-xs text-slate-500 font-mono mb-4">
                  Role: <strong className="text-violet-700">{selectedPermissionsUser.role.toUpperCase()}</strong>
                </div>

                <div className="max-h-60 overflow-y-auto space-y-1.5 p-3 rounded-2xl bg-slate-50 border border-slate-200/80">
                  {selectedPermissionsUser.permissions && selectedPermissionsUser.permissions.length > 0 ? (
                    selectedPermissionsUser.permissions.map((perm) => (
                      <div key={perm} className="text-xs font-mono text-slate-700 flex items-center gap-2">
                        <CheckCircle2 size={13} className="text-emerald-500 shrink-0" />
                        <span>{perm}</span>
                      </div>
                    ))
                  ) : (
                    <div className="text-xs text-slate-400 italic">No specific granular permissions assigned.</div>
                  )}
                </div>
              </div>

              <div className="flex justify-end pt-2">
                <button
                  onClick={() => setSelectedPermissionsUser(null)}
                  className="px-4 py-2 rounded-xl bg-slate-900 text-white font-semibold text-xs hover:bg-slate-800 transition-colors"
                >
                  Close
                </button>
              </div>
            </motion.div>
          </div>
        )}
      </AnimatePresence>
    </div>
  );
}
