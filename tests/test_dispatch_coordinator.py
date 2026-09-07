"""Offline P-04 checks: gate hook holds tools, ping shape, coordinator replies."""

from agent import coordinator as coord


class _Q:
    def __init__(self, stub, rows=None):
        self.stub = stub
        self.rows = rows or []

    def select(self, *a):
        return self

    def eq(self, *a):
        return self

    def order(self, *a, **k):
        return self

    def insert(self, row):
        self.stub.writes.append(row)
        return self

    def update(self, row):
        self.stub.writes.append(("update", row))
        return self

    def delete(self):
        return self

    def execute(self):
        return self

    @property
    def data(self):
        return self.rows


class _SB:
    def __init__(self, contacts, gate=None, audit=None):
        self.contacts = contacts
        self.gate = gate or []
        self.audit = audit or []
        self.writes = []

    def table(self, name):
        if name == "contacts":
            return _Q(self, self.contacts)
        if name == "gate_pending":
            return _Q(self, self.gate)
        if name == "audit_log":
            return _Q(self, self.audit)
        return _Q(self)


class _Ev:
    def __init__(self, name):
        self.tool_name = name
        self.tool_input = {"resident_name": "X"}
        self.interrupted = None

    def interrupt(self, token):
        self.interrupted = token


def _contacts():
    return [
        {"status": "ok", "residents": {"name": "A"}},
        {"status": "ok", "residents": {"name": "B"}},
        {"status": "medical", "residents": {"name": "Mabel Thornton"}},
        {"status": "unreachable", "residents": {"name": "Cecil Ward"}},
    ]


def test_gate_holds_and_ping_shape():
    sb = _SB(_contacts())
    gate = coord.CoordinatorGate(sb, "evt")
    ev = _Ev("escalate_medical")
    gate.on_before_tool_call(ev)
    assert ev.interrupted == "coordinator-decision"
    ev2 = _Ev("unrelated_tool")
    gate.on_before_tool_call(ev2)
    assert ev2.interrupted is None
    text = coord.compose_ping(sb, "evt", "Elm St heat warning")
    assert text.startswith("[Coordinator]") and "Reply" in text and "Mabel" in text


def test_coordinator_reply_approves_first_option():
    sb = _SB([], gate=[{"id": "g1", "tool": "escalate_medical", "input": "{}"}])
    out = coord.handle_coordinator_reply(sb, "evt", "1")
    assert out["outcome"] == "approved"
    assert out["decision"]["tool"] == "escalate_medical"
    assert coord.handle_coordinator_reply(sb, "evt", "9")["outcome"] == "ignored"


def test_maybe_ping_batches_inside_window():
    sb = _SB(_contacts(), gate=[{"id": "g1", "tool": "x", "input": "{}"}],
             audit=[{"created_at": "2999-01-01T00:00:00+00:00"}])
    out = coord.maybe_ping(sb, "evt", "heat", 0.0)
    assert out is not None and out["outcome"] == "batched"
