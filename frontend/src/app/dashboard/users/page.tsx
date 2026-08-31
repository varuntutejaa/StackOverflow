"use client";

import { useState } from "react";
import { Plus, ShieldCheck } from "lucide-react";
import { toast } from "sonner";

import { PageHeader } from "@/components/shell/page-header";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Dialog, DialogContent, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Badge, EmptyState, Label, NativeSelect, Skeleton, Switch } from "@/components/ui/misc";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Table, TBody, TD, TH, THead, TR } from "@/components/ui/table";
import { ApiError } from "@/lib/api";
import { useAuditLogs, useCreateUser, useUpdateUser, useUsers } from "@/lib/hooks";
import { relativeTime, titleCase } from "@/lib/utils";

const ROLES = ["admin", "gov_officer", "training_provider", "beneficiary"];

export default function UsersPage() {
  const { data, isLoading, refetch } = useUsers({ page_size: 50 });
  const { data: audit } = useAuditLogs({ page_size: 40 });
  const createUser = useCreateUser();
  const updateUser = useUpdateUser();
  const [open, setOpen] = useState(false);
  const [form, setForm] = useState({ full_name: "", email: "", password: "", role: "gov_officer", district: "", organisation: "" });

  async function create() {
    try {
      await createUser.mutateAsync({ ...form });
      toast.success("User created");
      setOpen(false);
      setForm({ full_name: "", email: "", password: "", role: "gov_officer", district: "", organisation: "" });
    } catch (e) {
      toast.error(e instanceof ApiError ? String(e.detail) : "Failed");
    }
  }

  return (
    <div className="space-y-5">
      <PageHeader
        title="Users & Roles"
        description="Role-based access control. Roles: Admin, Government Officer, Training Provider, Beneficiary."
        actions={
          <Button onClick={() => setOpen(true)}><Plus className="size-4" /> Add user</Button>
        }
      />

      <Tabs defaultValue="users">
        <TabsList>
          <TabsTrigger value="users">Users</TabsTrigger>
          <TabsTrigger value="audit">Audit Log</TabsTrigger>
        </TabsList>

        <TabsContent value="users">
          <Card className="p-0">
            {isLoading ? (
              <div className="space-y-2 p-4">{Array.from({ length: 6 }).map((_, i) => <Skeleton key={i} className="h-10 w-full" />)}</div>
            ) : !data?.items.length ? (
              <div className="p-6"><EmptyState icon={ShieldCheck} title="No users" /></div>
            ) : (
              <Table>
                <THead>
                  <TR><TH>Name</TH><TH>Email</TH><TH>Role</TH><TH>Organisation</TH><TH>Active</TH><TH>Change role</TH></TR>
                </THead>
                <TBody>
                  {data.items.map((u) => (
                    <TR key={u.id}>
                      <TD className="font-medium">{u.full_name}</TD>
                      <TD className="text-muted-foreground">{u.email}</TD>
                      <TD><Badge>{titleCase(u.role)}</Badge></TD>
                      <TD className="text-muted-foreground">{u.organisation ?? "—"}</TD>
                      <TD>
                        <Switch
                          checked={u.is_active}
                          onCheckedChange={(v) => updateUser.mutate({ id: u.id, body: { is_active: v } }, { onSuccess: () => refetch() })}
                        />
                      </TD>
                      <TD>
                        <NativeSelect
                          value={u.role}
                          onChange={(e) => updateUser.mutate({ id: u.id, body: { role: e.target.value } }, { onSuccess: () => { toast.success("Role updated"); refetch(); } })}
                        >
                          {ROLES.map((r) => <option key={r} value={r}>{titleCase(r)}</option>)}
                        </NativeSelect>
                      </TD>
                    </TR>
                  ))}
                </TBody>
              </Table>
            )}
          </Card>
        </TabsContent>

        <TabsContent value="audit">
          <Card className="p-0">
            <Table>
              <THead>
                <TR><TH>When</TH><TH>Actor</TH><TH>Action</TH><TH>Entity</TH><TH>Status</TH><TH>IP</TH></TR>
              </THead>
              <TBody>
                {audit?.items.map((a: any) => (
                  <TR key={a.id}>
                    <TD className="text-muted-foreground">{relativeTime(a.created_at)}</TD>
                    <TD>{a.actor_email ?? "—"}</TD>
                    <TD className="font-mono text-xs">{a.action}</TD>
                    <TD className="text-muted-foreground">{a.entity_type ?? "—"}</TD>
                    <TD><Badge variant={a.status === "success" ? "success" : "destructive"}>{a.status}</Badge></TD>
                    <TD className="text-muted-foreground">{a.ip_address ?? "—"}</TD>
                  </TR>
                ))}
              </TBody>
            </Table>
          </Card>
        </TabsContent>
      </Tabs>

      <Dialog open={open} onOpenChange={setOpen}>
        <DialogContent>
          <DialogHeader><DialogTitle>Add user</DialogTitle></DialogHeader>
          <div className="grid gap-3">
            <div className="space-y-1.5"><Label>Full name</Label><Input value={form.full_name} onChange={(e) => setForm((f) => ({ ...f, full_name: e.target.value }))} /></div>
            <div className="space-y-1.5"><Label>Email</Label><Input type="email" value={form.email} onChange={(e) => setForm((f) => ({ ...f, email: e.target.value }))} /></div>
            <div className="space-y-1.5"><Label>Temporary password</Label><Input type="text" value={form.password} onChange={(e) => setForm((f) => ({ ...f, password: e.target.value }))} /></div>
            <div className="space-y-1.5">
              <Label>Role</Label>
              <NativeSelect className="w-full" value={form.role} onChange={(e) => setForm((f) => ({ ...f, role: e.target.value }))}>
                {ROLES.map((r) => <option key={r} value={r}>{titleCase(r)}</option>)}
              </NativeSelect>
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-1.5"><Label>District</Label><Input value={form.district} onChange={(e) => setForm((f) => ({ ...f, district: e.target.value }))} /></div>
              <div className="space-y-1.5"><Label>Organisation</Label><Input value={form.organisation} onChange={(e) => setForm((f) => ({ ...f, organisation: e.target.value }))} /></div>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setOpen(false)}>Cancel</Button>
            <Button onClick={create} loading={createUser.isPending}>Create</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
