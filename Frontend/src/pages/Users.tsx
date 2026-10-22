import { useEffect, useState } from "react";
import { Plus } from "lucide-react";
import Layout from "../components/Layout";
import { Panel, StatusPill } from "../components/UI";
import api from "../api/client";
import type { User } from "../types";

export default function Users() {
  const [users, setUsers] = useState<User[]>([]);
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({ name: "", email: "", password: "", role: "operator", department: "" });
  const [error, setError] = useState("");

  async function load() {
    const res = await api.get("/api/users");
    setUsers(res.data);
  }
  useEffect(() => { load(); }, []);

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    try {
      await api.post("/api/auth/register", form);
      setShowForm(false);
      setForm({ name: "", email: "", password: "", role: "operator", department: "" });
      load();
    } catch (err: any) {
      setError(err?.response?.data?.detail || "Could not create user");
    }
  }

  async function toggleActive(id: string, is_active: boolean) {
    await api.patch(`/api/users/${id}`, { is_active: !is_active });
    load();
  }

  return (
    <Layout title="Users">
      <div className="space-y-6">
        <div className="flex justify-between items-center">
          <p className="text-textmuted text-sm">{users.length} user(s)</p>
          <button onClick={() => setShowForm(!showForm)} className="flex items-center gap-1 bg-amber text-base font-display font-600 text-sm px-3 py-2 rounded hover:brightness-110">
            <Plus size={15} /> Add User
          </button>
        </div>

        {showForm && (
          <Panel title="New User">
            <form onSubmit={handleCreate} className="grid md:grid-cols-5 gap-3">
              <input required placeholder="Full name" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })}
                className="bg-panel2 border border-border rounded px-3 py-2 text-sm text-textprimary" />
              <input required type="email" placeholder="Email" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })}
                className="bg-panel2 border border-border rounded px-3 py-2 text-sm text-textprimary" />
              <input required type="password" placeholder="Password" value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })}
                className="bg-panel2 border border-border rounded px-3 py-2 text-sm text-textprimary" />
              <select value={form.role} onChange={(e) => setForm({ ...form, role: e.target.value })}
                className="bg-panel2 border border-border rounded px-3 py-2 text-sm text-textprimary">
                <option value="admin">Admin</option>
                <option value="engineer">Engineer</option>
                <option value="supervisor">Supervisor</option>
                <option value="operator">Operator</option>
              </select>
              <input placeholder="Department" value={form.department} onChange={(e) => setForm({ ...form, department: e.target.value })}
                className="bg-panel2 border border-border rounded px-3 py-2 text-sm text-textprimary" />
              {error && <p className="md:col-span-5 text-danger text-sm">{error}</p>}
              <button type="submit" className="md:col-span-5 bg-amber text-base font-display font-600 rounded py-2 text-sm">Create User</button>
            </form>
          </Panel>
        )}

        <Panel title="All Users">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-left text-textmuted font-mono text-xs uppercase border-b border-border">
                  <th className="py-2 pr-4">Name</th>
                  <th className="py-2 pr-4">Email</th>
                  <th className="py-2 pr-4">Role</th>
                  <th className="py-2 pr-4">Department</th>
                  <th className="py-2 pr-4">Status</th>
                  <th className="py-2 pr-4"></th>
                </tr>
              </thead>
              <tbody>
                {users.map((u) => (
                  <tr key={u.id} className="border-b border-border/50">
                    <td className="py-2 pr-4 text-textprimary">{u.name}</td>
                    <td className="py-2 pr-4 text-textmuted">{u.email}</td>
                    <td className="py-2 pr-4 font-mono text-xs uppercase">{u.role}</td>
                    <td className="py-2 pr-4">{u.department || "—"}</td>
                    <td className="py-2 pr-4"><StatusPill status={u.is_active ? "running" : "offline"} /></td>
                    <td className="py-2 pr-4">
                      <button onClick={() => toggleActive(u.id, u.is_active)} className="text-xs font-mono text-amber hover:underline">
                        {u.is_active ? "Deactivate" : "Activate"}
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Panel>
      </div>
    </Layout>
  );
}
