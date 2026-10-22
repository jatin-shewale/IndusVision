import { useEffect, useState } from "react";
import { Plus } from "lucide-react";
import Layout from "../components/Layout";
import { Panel } from "../components/UI";
import api from "../api/client";
import type { InventoryItem } from "../types";

export default function Inventory() {
  const [items, setItems] = useState<InventoryItem[]>([]);
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({ item_name: "", category: "raw_material", quantity: 0, unit: "kg", threshold: 10 });

  async function load() {
    const res = await api.get("/api/inventory/items");
    setItems(res.data);
  }

  useEffect(() => { load(); }, []);

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault();
    await api.post("/api/inventory/items", form);
    setShowForm(false);
    setForm({ item_name: "", category: "raw_material", quantity: 0, unit: "kg", threshold: 10 });
    load();
  }

  return (
    <Layout title="Inventory">
      <div className="space-y-6">
        <div className="flex justify-between items-center">
          <p className="text-textmuted text-sm">{items.length} items tracked · {items.filter(i => i.low_stock).length} below threshold</p>
          <button onClick={() => setShowForm(!showForm)} className="flex items-center gap-1 bg-amber text-base font-display font-600 text-sm px-3 py-2 rounded hover:brightness-110">
            <Plus size={15} /> Add Item
          </button>
        </div>

        {showForm && (
          <Panel title="New Inventory Item">
            <form onSubmit={handleCreate} className="grid md:grid-cols-5 gap-3">
              <input required placeholder="Item name" value={form.item_name}
                onChange={(e) => setForm({ ...form, item_name: e.target.value })}
                className="bg-panel2 border border-border rounded px-3 py-2 text-sm text-textprimary" />
              <select value={form.category} onChange={(e) => setForm({ ...form, category: e.target.value })}
                className="bg-panel2 border border-border rounded px-3 py-2 text-sm text-textprimary">
                <option value="raw_material">Raw Material</option>
                <option value="finished_goods">Finished Goods</option>
                <option value="scrap">Scrap</option>
              </select>
              <input required type="number" placeholder="Quantity" value={form.quantity}
                onChange={(e) => setForm({ ...form, quantity: Number(e.target.value) })}
                className="bg-panel2 border border-border rounded px-3 py-2 text-sm text-textprimary" />
              <input placeholder="Unit (kg, units...)" value={form.unit}
                onChange={(e) => setForm({ ...form, unit: e.target.value })}
                className="bg-panel2 border border-border rounded px-3 py-2 text-sm text-textprimary" />
              <input required type="number" placeholder="Reorder threshold" value={form.threshold}
                onChange={(e) => setForm({ ...form, threshold: Number(e.target.value) })}
                className="bg-panel2 border border-border rounded px-3 py-2 text-sm text-textprimary" />
              <button type="submit" className="md:col-span-5 bg-amber text-base font-display font-600 rounded py-2 text-sm">
                Save Item
              </button>
            </form>
          </Panel>
        )}

        <Panel title="Stock Levels">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-left text-textmuted font-mono text-xs uppercase border-b border-border">
                  <th className="py-2 pr-4">Item</th>
                  <th className="py-2 pr-4">Category</th>
                  <th className="py-2 pr-4">Quantity</th>
                  <th className="py-2 pr-4">Threshold</th>
                  <th className="py-2 pr-4">Status</th>
                </tr>
              </thead>
              <tbody>
                {items.map((i) => (
                  <tr key={i.id} className="border-b border-border/50">
                    <td className="py-2 pr-4 text-textprimary">{i.item_name}</td>
                    <td className="py-2 pr-4 text-textmuted font-mono text-xs">{i.category}</td>
                    <td className="py-2 pr-4">{i.quantity} {i.unit}</td>
                    <td className="py-2 pr-4 text-textmuted">{i.threshold} {i.unit}</td>
                    <td className="py-2 pr-4">
                      {i.low_stock ? (
                        <span className="text-amber font-mono text-xs">REORDER</span>
                      ) : (
                        <span className="text-safe font-mono text-xs">OK</span>
                      )}
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
