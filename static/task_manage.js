// static/task_manage.js
let editingTaskId = null;

function openAddTaskModal() {
  document.getElementById('addTaskModal').style.display = 'block';
}

function closeAddTaskModal() {
  document.getElementById('addTaskModal').style.display = 'none';
}

function openEditModal(id, title, description, startTime, allDay) {
  editingTaskId = id;
  document.getElementById('editTaskTitle').value = title;
  document.getElementById('editTaskDesc').value = description;
  const startInput = document.getElementById('editTaskStart');
  const checkbox = document.getElementById('editTaskAllDay');

  if (allDay) {
    checkbox.checked = true;
    startInput.type = 'date';
    startInput.value = startTime.split('T')[0];
  } else {
    checkbox.checked = false;
    startInput.type = 'datetime-local';
    startInput.value = startTime.replace(' ', 'T');
  }

  document.getElementById('editTaskModal').style.display = 'block';
}

function closeEditTaskModal() {
  document.getElementById('editTaskModal').style.display = 'none';
}

function toggleAllDay(prefix) {
  const checkbox = document.getElementById(`${prefix}TaskAllDay`);
  const startInput = document.getElementById(`${prefix}TaskStart`);
  if (checkbox.checked) {
    const current = startInput.value;
    startInput.type = 'date';
    if (current.includes('T')) startInput.value = current.split('T')[0];
  } else {
    startInput.type = 'datetime-local';
  }
}

async function addTask() {
  const title = document.getElementById('newTaskTitle').value.trim();
  const description = document.getElementById('newTaskDesc').value.trim() || '';
  const startTime = document.getElementById('newTaskStart').value;
  const allDay = document.getElementById('newTaskAllDay').checked ? 1 : 0;

  if (!title) return alert('Title is required.');
  if (!startTime) return alert('Start time is required.');

  const response = await fetch('/test_add_task', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ title, description, start_time: startTime, all_day: allDay })
  });

  if (response.ok) {
    const newTask = await response.json();
    const li = document.createElement('li');
    li.id = `task-${newTask.task_id}`;
    li.innerHTML = `
      <strong>${newTask.title}</strong> — ${newTask.description} — ${newTask.start_time}
      ${newTask.all_day ? '(All Day)' : ''}
      <button onclick="openEditModal(${newTask.task_id}, '${newTask.title}', '${newTask.description}', '${newTask.start_time}', ${newTask.all_day})">Modify</button>
      <button onclick="completeTask(${newTask.task_id})">Complete</button>
      <button onclick="confirmDeleteTask(${newTask.task_id})">Delete</button>
    `;

    // ✅ Always close modal and reset fields
    closeAddTaskModal();
    document.getElementById('newTaskTitle').value = '';
    document.getElementById('newTaskDesc').value = '';
    document.getElementById('newTaskStart').value = '';
    document.getElementById('newTaskAllDay').checked = false;
    toggleAllDay('new');

    // ✅ Refresh the page to show updated data everywhere
    location.reload();

  } else {
    alert('Failed to add task.');
  }
}

async function saveTaskChanges() {
  const title = document.getElementById('editTaskTitle').value.trim();
  const description = document.getElementById('editTaskDesc').value.trim() || '';
  const startTime = document.getElementById('editTaskStart').value;
  const allDay = document.getElementById('editTaskAllDay').checked ? 1 : 0;

  if (!title) return alert('Title is required.');
  if (!startTime) return alert('Start time is required.');

  const response = await fetch(`/test_update_task/${editingTaskId}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ title, description, start_time: startTime, all_day: allDay })
  });

  if (response.ok) {
    const updated = await response.json();

    // ✅ Update only if list item exists
    const li = document.getElementById(`task-${editingTaskId}`);
    if (li) {
      li.innerHTML = `
        <strong>${updated.title}</strong> — ${updated.description} — ${updated.start_time}
        ${updated.all_day ? '(All Day)' : ''}
        <button onclick="openEditModal(${updated.task_id}, '${updated.title}', '${updated.description}', '${updated.start_time}', ${updated.all_day})">Modify</button>
        <button onclick="completeTask(${updated.task_id})">Complete</button>
        <button onclick="confirmDeleteTask(${updated.task_id})">Delete</button>
      `;
    }

    closeEditTaskModal();
  } else {
    alert('Failed to update task.');
  }
}

async function confirmDeleteTask(taskId) {
  if (confirm('Are you sure you want to delete this task?')) {
    const response = await fetch(`/test_delete_task/${taskId}`, { method: 'POST' });
    if (response.ok) {
      const li = document.getElementById(`task-${taskId}`);
      if (li) li.remove();
    } else {
      alert('Failed to delete task.');
    }
  }
}

async function completeTask(taskId) {
  const response = await fetch(`/test_complete_task/${taskId}`, { method: 'POST' });
  if (response.ok) {
    const li = document.getElementById(`task-${taskId}`);
    if (li) li.remove(); // ✅ only remove if visible
  } else {
    alert('Failed to mark task as completed.');
  }
}
