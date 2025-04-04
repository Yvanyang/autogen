<template>
  <div class="todo-app">
    <h1>Vue Todo App</h1>
    
    <div class="add-todo">
      <input 
        v-model="newTodo" 
        @keyup.enter="addTodo" 
        placeholder="Add a new task..."
        class="todo-input"
      />
      <button @click="addTodo" class="add-button">Add</button>
    </div>
    
    <div v-if="todos.length === 0" class="empty-state">
      No tasks yet! Add one above.
    </div>
    
    <ul class="todo-list">
      <li v-for="(todo, index) in todos" :key="index" class="todo-item">
        <div class="todo-content">
          <input 
            type="checkbox" 
            v-model="todo.completed" 
            class="todo-checkbox"
          />
          <span 
            :class="{ 'completed': todo.completed }"
            class="todo-text"
          >
            {{ todo.text }}
          </span>
        </div>
        <div class="todo-actions">
          <button @click="removeTodo(index)" class="delete-button">Delete</button>
        </div>
      </li>
    </ul>
    
    <div class="todo-stats" v-if="todos.length > 0">
      <span>{{ completedCount }} completed / {{ todos.length }} total</span>
      <button @click="clearCompleted" class="clear-button">Clear Completed</button>
    </div>
  </div>
</template>

<script>
export default {
  name: 'TodoApp',
  data() {
    return {
      newTodo: '',
      todos: [
        { text: 'Learn Vue', completed: true },
        { text: 'Build a Todo App', completed: false },
        { text: 'Convert to React', completed: false }
      ]
    }
  },
  computed: {
    completedCount() {
      return this.todos.filter(todo => todo.completed).length;
    }
  },
  methods: {
    addTodo() {
      if (this.newTodo.trim()) {
        this.todos.push({
          text: this.newTodo,
          completed: false
        });
        this.newTodo = '';
      }
    },
    removeTodo(index) {
      this.todos.splice(index, 1);
    },
    clearCompleted() {
      this.todos = this.todos.filter(todo => !todo.completed);
    }
  }
}
</script>

<style scoped>
.todo-app {
  max-width: 500px;
  margin: 0 auto;
  padding: 20px;
  font-family: Arial, sans-serif;
}

h1 {
  text-align: center;
  color: #2c3e50;
}

.add-todo {
  display: flex;
  margin-bottom: 20px;
}

.todo-input {
  flex: 1;
  padding: 10px;
  border: 1px solid #ddd;
  border-radius: 4px 0 0 4px;
  font-size: 16px;
}

.add-button {
  padding: 10px 15px;
  background-color: #42b983;
  color: white;
  border: none;
  border-radius: 0 4px 4px 0;
  cursor: pointer;
  font-size: 16px;
}

.todo-list {
  list-style-type: none;
  padding: 0;
}

.todo-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px;
  margin-bottom: 10px;
  background-color: #f9f9f9;
  border-radius: 4px;
  transition: all 0.3s;
}

.todo-content {
  display: flex;
  align-items: center;
}

.todo-checkbox {
  margin-right: 10px;
}

.todo-text {
  font-size: 16px;
}

.completed {
  text-decoration: line-through;
  color: #999;
}

.delete-button {
  padding: 5px 10px;
  background-color: #e74c3c;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}

.todo-stats {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 20px;
  padding-top: 10px;
  border-top: 1px solid #eee;
}

.clear-button {
  padding: 5px 10px;
  background-color: #7f8c8d;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}

.empty-state {
  text-align: center;
  color: #7f8c8d;
  margin: 20px 0;
}
</style>
