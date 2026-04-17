from __future__ import annotations

from collections import defaultdict


def _task_sort_key(task) -> tuple:
    dl = task.deadline.toordinal() if task.deadline else 10**9
    ts = task.created_at.timestamp() if task.created_at else 0.0
    return (dl, -ts, task.id)


def topological_sort_tasks(tasks: list) -> tuple[list, bool]:
    """
    Sort tasks so every prerequisite appears before its dependent task.
    Only edges between tasks in the given list are considered.

    Returns (ordered_tasks, has_cycle). If the subgraph has a cycle,
    remaining tasks are appended in a stable fallback order and has_cycle is True.
    """
    if not tasks:
        return [], False

    id_to_task = {t.id: t for t in tasks}
    ids = set(id_to_task)
    graph: dict[int, list[int]] = {tid: [] for tid in ids}
    in_degree = {tid: 0 for tid in ids}

    for t in tasks:
        for p in t.prerequisites:
            if p.id not in ids:
                continue
            graph[p.id].append(t.id)
            in_degree[t.id] += 1

    result: list[Task] = []
    remaining = set(ids)

    while remaining:
        ready = [tid for tid in remaining if in_degree[tid] == 0]
        if not ready:
            break
        ready.sort(key=lambda tid: _task_sort_key(id_to_task[tid]))
        u = ready[0]
        remaining.remove(u)
        result.append(id_to_task[u])
        for v in graph[u]:
            in_degree[v] -= 1

    has_cycle = len(result) < len(ids)
    if has_cycle:
        rest_ids = [tid for tid in ids if id_to_task[tid] not in result]
        rest_ids.sort(key=lambda tid: _task_sort_key(id_to_task[tid]))
        result.extend(id_to_task[tid] for tid in rest_ids)

    return result, has_cycle


def prerequisite_set_creates_cycle(all_tasks: list, dependent, new_prerequisite_ids: set[int]) -> bool:
    """True if replacing dependent.prerequisites with new_prerequisite_ids introduces a cycle."""
    ids = {t.id for t in all_tasks}
    for pid in new_prerequisite_ids:
        if pid == dependent.id or pid not in ids:
            return True

    graph: dict[int, list[int]] = defaultdict(list)
    in_degree = {tid: 0 for tid in ids}

    for t in all_tasks:
        if t.id == dependent.id:
            ps = new_prerequisite_ids
        else:
            ps = {p.id for p in t.prerequisites}
        for p in ps:
            if p not in ids:
                continue
            graph[p].append(t.id)
            in_degree[t.id] += 1

    remaining = set(ids)
    while True:
        batch = [i for i in remaining if in_degree[i] == 0]
        if not batch:
            break
        u = batch[0]
        remaining.remove(u)
        for v in graph[u]:
            in_degree[v] -= 1

    return len(remaining) > 0
