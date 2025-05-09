import * as React from 'react';
import * as Tabs from '@radix-ui/react-tabs';
import * as Dialog from '@radix-ui/react-dialog';

// Mock data
const users = [
  { id: 1, name: 'Alice Admin', email: 'alice@matchwise.com', role: 'Admin' },
  { id: 2, name: 'Bob Manager', email: 'bob@matchwise.com', role: 'Manager' },
  { id: 3, name: 'Charlie User', email: 'charlie@matchwise.com', role: 'User' },
];

export default function Admin() {
  const [openUserId, setOpenUserId] = React.useState<number | null>(null);
  return (
    <div className="w-full p-4 space-y-8">
      <h1 className="text-2xl font-bold text-primary mb-4">Admin Dashboard</h1>
      <Tabs.Root defaultValue="users" className="w-full">
        <Tabs.List className="flex gap-2 mb-4">
          <Tabs.Trigger value="users" className="px-4 py-2 rounded-lg font-semibold text-primary bg-white/70 shadow border border-primary-light data-[state=active]:bg-primary data-[state=active]:text-white transition">Users</Tabs.Trigger>
          <Tabs.Trigger value="data" className="px-4 py-2 rounded-lg font-semibold text-primary bg-white/70 shadow border border-primary-light data-[state=active]:bg-primary data-[state=active]:text-white transition">Data</Tabs.Trigger>
          <Tabs.Trigger value="settings" className="px-4 py-2 rounded-lg font-semibold text-primary bg-white/70 shadow border border-primary-light data-[state=active]:bg-primary data-[state=active]:text-white transition">Settings</Tabs.Trigger>
        </Tabs.List>
        {/* Users Tab */}
        <Tabs.Content value="users">
          <div className="bg-white/60 backdrop-blur-md shadow-glass rounded-2xl p-6 border border-primary-light">
            <h2 className="text-lg font-bold mb-4">User Management</h2>
            <div className="overflow-x-auto">
              <table className="min-w-full text-sm">
                <thead>
                  <tr className="text-slate-700 border-b">
                    <th className="p-2 text-left">Name</th>
                    <th className="p-2 text-left">Email</th>
                    <th className="p-2 text-left">Role</th>
                    <th className="p-2 text-left">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {users.map((u) => (
                    <tr key={u.id} className="border-b last:border-0">
                      <td className="p-2 font-semibold text-slate-900">{u.name}</td>
                      <td className="p-2">{u.email}</td>
                      <td className="p-2">{u.role}</td>
                      <td className="p-2 flex gap-2">
                        <Dialog.Root open={openUserId === u.id} onOpenChange={(open) => setOpenUserId(open ? u.id : null)}>
                          <Dialog.Trigger asChild>
                            <button className="px-2 py-1 rounded bg-primary text-white text-xs font-bold hover:bg-primary-dark">Edit</button>
                          </Dialog.Trigger>
                          <Dialog.Content className="fixed inset-0 flex items-center justify-center z-50">
                            <div className="bg-white rounded-xl shadow-lg p-6 w-80 border border-primary-light">
                              <Dialog.Title className="font-bold text-lg mb-2">Edit User</Dialog.Title>
                              <div className="mb-4">
                                <label className="block text-xs font-semibold mb-1">Name</label>
                                <input className="w-full border rounded p-2" defaultValue={u.name} />
                              </div>
                              <div className="mb-4">
                                <label className="block text-xs font-semibold mb-1">Email</label>
                                <input className="w-full border rounded p-2" defaultValue={u.email} />
                              </div>
                              <div className="mb-4">
                                <label className="block text-xs font-semibold mb-1">Role</label>
                                <select className="w-full border rounded p-2" defaultValue={u.role}>
                                  <option>Admin</option>
                                  <option>Manager</option>
                                  <option>User</option>
                                </select>
                              </div>
                              <div className="flex justify-end gap-2">
                                <Dialog.Close asChild>
                                  <button className="px-3 py-1 rounded bg-primary text-white font-semibold">Save</button>
                                </Dialog.Close>
                                <Dialog.Close asChild>
                                  <button className="px-3 py-1 rounded bg-slate-200 text-slate-700 font-semibold">Cancel</button>
                                </Dialog.Close>
                              </div>
                            </div>
                          </Dialog.Content>
                        </Dialog.Root>
                        <button className="px-2 py-1 rounded bg-error text-white text-xs font-bold hover:bg-error-dark">Delete</button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </Tabs.Content>
        {/* Data Tab */}
        <Tabs.Content value="data">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="bg-white/60 backdrop-blur-md shadow-glass rounded-2xl p-6 border border-primary-light flex flex-col items-center">
              <div className="text-3xl font-bold text-primary mb-2">Teams</div>
              <div className="text-slate-600 mb-4">Manage all football teams in the database.</div>
              <button className="px-4 py-2 rounded bg-primary text-white font-semibold">Manage Teams</button>
            </div>
            <div className="bg-white/60 backdrop-blur-md shadow-glass rounded-2xl p-6 border border-primary-light flex flex-col items-center">
              <div className="text-3xl font-bold text-primary mb-2">Players</div>
              <div className="text-slate-600 mb-4">Manage all players and their data.</div>
              <button className="px-4 py-2 rounded bg-primary text-white font-semibold">Manage Players</button>
            </div>
            <div className="bg-white/60 backdrop-blur-md shadow-glass rounded-2xl p-6 border border-primary-light flex flex-col items-center">
              <div className="text-3xl font-bold text-primary mb-2">Matches</div>
              <div className="text-slate-600 mb-4">Manage fixtures, results, and match data.</div>
              <button className="px-4 py-2 rounded bg-primary text-white font-semibold">Manage Matches</button>
            </div>
          </div>
        </Tabs.Content>
        {/* Settings Tab */}
        <Tabs.Content value="settings">
          <div className="bg-white/60 backdrop-blur-md shadow-glass rounded-2xl p-6 border border-primary-light w-full">
            <h2 className="text-lg font-bold mb-4">Platform Settings</h2>
            <form className="space-y-4">
              <div>
                <label className="block text-xs font-semibold mb-1">Theme</label>
                <select className="w-full border rounded p-2">
                  <option>Light</option>
                  <option>Dark</option>
                  <option>System</option>
                </select>
              </div>
              <div>
                <label className="block text-xs font-semibold mb-1">Maintenance Mode</label>
                <input type="checkbox" className="ml-2 align-middle" />
                <span className="ml-2 text-sm text-slate-600">Enable maintenance mode</span>
              </div>
              <div>
                <label className="block text-xs font-semibold mb-1">Contact Email</label>
                <input className="w-full border rounded p-2" defaultValue="support@matchwise.com" />
              </div>
              <button type="submit" className="px-4 py-2 rounded bg-primary text-white font-semibold mt-2">Save Settings</button>
            </form>
          </div>
        </Tabs.Content>
      </Tabs.Root>
    </div>
  );
} 