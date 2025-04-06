<template>
  <div class="page-manager">
    <h2>Page Management</h2>
    
    <div class="controls">
      <button @click="addNewPage" class="btn add-btn">Add New Page</button>
    </div>
    
    <div v-if="showForm" class="page-form">
      <h3>{{ editIndex === null ? 'Add New Page' : 'Edit Page' }}</h3>
      <div class="form-group">
        <label for="pageName">Page Name:</label>
        <input type="text" id="pageName" v-model="currentPage.name" placeholder="Enter page name">
      </div>
      
      <div class="form-group">
        <label for="routePath">Route Path:</label>
        <input type="text" id="routePath" v-model="currentPage.route" placeholder="Enter route path (e.g., /users)">
      </div>
      
      <div class="form-group">
        <label for="pageParams">Parameters (comma separated):</label>
        <input type="text" id="pageParams" v-model="paramsInput" placeholder="id, name, status">
      </div>
      
      <div class="form-actions">
        <button @click="savePage" class="btn save-btn">Save</button>
        <button @click="cancelEdit" class="btn cancel-btn">Cancel</button>
      </div>
    </div>
    
    <div class="pages-list">
      <table v-if="pages.length > 0">
        <thead>
          <tr>
            <th>Page Name</th>
            <th>Route Path</th>
            <th>Parameters</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="(page, index) in pages" :key="index">
            <td>{{ page.name }}</td>
            <td>{{ page.route }}</td>
            <td>{{ page.params.join(', ') }}</td>
            <td>
              <button @click="editPage(index)" class="btn edit-btn">Edit</button>
              <button @click="deletePage(index)" class="btn delete-btn">Delete</button>
            </td>
          </tr>
        </tbody>
      </table>
      <div v-else class="no-pages">
        No pages added yet. Click "Add New Page" to get started.
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'PageManager',
  data() {
    return {
      pages: [],
      currentPage: {
        name: '',
        route: '',
        params: []
      },
      paramsInput: '',
      showForm: false,
      editIndex: null
    }
  },
  methods: {
    addNewPage() {
      this.resetForm();
      this.showForm = true;
      this.editIndex = null;
    },
    
    editPage(index) {
      const page = this.pages[index];
      this.currentPage = {
        name: page.name,
        route: page.route,
        params: [...page.params]
      };
      this.paramsInput = page.params.join(', ');
      this.showForm = true;
      this.editIndex = index;
    },
    
    savePage() {
      // Validate inputs
      if (!this.currentPage.name || !this.currentPage.route) {
        alert('Page name and route path are required!');
        return;
      }
      
      // Process parameters
      const params = this.paramsInput
        .split(',')
        .map(param => param.trim())
        .filter(param => param.length > 0);
      
      const pageToSave = {
        name: this.currentPage.name,
        route: this.currentPage.route,
        params: params
      };
      
      if (this.editIndex !== null) {
        // Update existing page
        this.pages.splice(this.editIndex, 1, pageToSave);
      } else {
        // Add new page
        this.pages.push(pageToSave);
      }
      
      this.resetForm();
    },
    
    deletePage(index) {
      if (confirm('Are you sure you want to delete this page?')) {
        this.pages.splice(index, 1);
      }
    },
    
    cancelEdit() {
      this.resetForm();
    },
    
    resetForm() {
      this.currentPage = {
        name: '',
        route: '',
        params: []
      };
      this.paramsInput = '';
      this.showForm = false;
      this.editIndex = null;
    }
  },
  created() {
    // Load sample data
    this.pages = [
      {
        name: 'Dashboard',
        route: '/dashboard',
        params: []
      },
      {
        name: 'User Profile',
        route: '/user/:id',
        params: ['id', 'tab']
      },
      {
        name: 'Products List',
        route: '/products',
        params: ['category', 'sort']
      }
    ];
  }
}
</script>

<style scoped>
.page-manager {
  background-color: #f9f9f9;
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

h2 {
  margin-top: 0;
  color: #42b983;
  border-bottom: 2px solid #42b983;
  padding-bottom: 10px;
}

.controls {
  margin-bottom: 20px;
}

.btn {
  padding: 8px 16px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-weight: bold;
  transition: background-color 0.3s;
}

.add-btn {
  background-color: #42b983;
  color: white;
}

.add-btn:hover {
  background-color: #3aa876;
}

.page-form {
  background-color: white;
  padding: 20px;
  border-radius: 8px;
  margin-bottom: 20px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.form-group {
  margin-bottom: 15px;
}

label {
  display: block;
  margin-bottom: 5px;
  font-weight: bold;
}

input {
  width: 100%;
  padding: 8px;
  border: 1px solid #ddd;
  border-radius: 4px;
}

.form-actions {
  display: flex;
  gap: 10px;
  margin-top: 20px;
}

.save-btn {
  background-color: #42b983;
  color: white;
}

.save-btn:hover {
  background-color: #3aa876;
}

.cancel-btn {
  background-color: #f2f2f2;
  color: #333;
}

.cancel-btn:hover {
  background-color: #e0e0e0;
}

.pages-list {
  margin-top: 20px;
}

table {
  width: 100%;
  border-collapse: collapse;
}

th, td {
  padding: 12px;
  text-align: left;
  border-bottom: 1px solid #ddd;
}

th {
  background-color: #f2f2f2;
  font-weight: bold;
}

.edit-btn {
  background-color: #4a90e2;
  color: white;
  margin-right: 5px;
}

.edit-btn:hover {
  background-color: #3a80d2;
}

.delete-btn {
  background-color: #e74c3c;
  color: white;
}

.delete-btn:hover {
  background-color: #d73c2c;
}

.no-pages {
  text-align: center;
  padding: 20px;
  color: #666;
  font-style: italic;
}
</style>
