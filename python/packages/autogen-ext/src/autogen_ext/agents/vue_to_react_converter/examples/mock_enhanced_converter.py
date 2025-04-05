"""
Mock implementation of the enhanced Vue to React converter for demonstration purposes.
"""
import os
import shutil
from pathlib import Path
import json
import asyncio

class MockChatCompletionClient:
    """Mock implementation of a chat completion client for testing."""
    
    def __init__(self, model="gpt-4"):
        """Initialize the mock client."""
        self.model = model
    
    async def create(self, messages, **kwargs):
        """Mock create method that returns a predefined response."""
        print(f"[Model: {self.model}] Processing request with {len(messages)} messages")
        return {
            "choices": [
                {
                    "message": {
                        "content": "This is a mock response from the model."
                    }
                }
            ]
        }

class MockEnhancedVueToReactConverter:
    """
    Mock implementation of the enhanced Vue to React converter.
    """
    
    def __init__(self, model_client, max_lines_per_chunk=500):
        """Initialize the mock converter."""
        self.model_client = model_client
        self.max_lines_per_chunk = max_lines_per_chunk
    
    def save_knowledge_base(self, file_path):
        """Mock method to save knowledge base to a file."""
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, 'w') as f:
            json.dump({
                "version": "1.0",
                "rules": [
                    "Vue template tags become JSX",
                    "Vue data() becomes React useState",
                    "Vue methods become React functions",
                    "Vue lifecycle hooks map to React useEffect"
                ]
            }, f, indent=2)
    
    async def convert_file(self, vue_file_path, output_dir, knowledge_base_path=None):
        """
        Mock method to convert a Vue file to React.
        
        In a real implementation, this would use the LLM to perform the conversion.
        For this mock, we'll implement a simple rule-based conversion.
        """
        print(f"Converting {vue_file_path} to React...")
        
        os.makedirs(output_dir, exist_ok=True)
        
        with open(vue_file_path, 'r') as f:
            vue_content = f.read()
        
        base_name = os.path.basename(vue_file_path).replace('.vue', '')
        
        react_file = os.path.join(output_dir, f"{base_name}.jsx")
        
        if base_name == "App":
            react_content = self._convert_app_component(vue_content)
        elif base_name == "PageManager":
            react_content = self._convert_page_manager_component(vue_content)
        else:
            react_content = self._convert_generic_component(vue_content, base_name)
        
        with open(react_file, 'w') as f:
            f.write(react_content)
        
        css_file = os.path.join(output_dir, f"{base_name}.css")
        css_content = self._extract_css(vue_content)
        
        with open(css_file, 'w') as f:
            f.write(css_content)
        
        report_dir = os.path.join(output_dir, ".reports")
        os.makedirs(report_dir, exist_ok=True)
        report_path = os.path.join(report_dir, f"{base_name}_conversion_report.json")
        
        report = {
            "source_file": vue_file_path,
            "target_file": react_file,
            "css_file": css_file,
            "conversion_status": "success",
            "issues": [],
            "timestamp": "2025-04-05T16:00:00Z"
        }
        
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        await asyncio.sleep(0.5)
        
        return {
            "vue_file": vue_file_path,
            "react_file": react_file,
            "css_file": css_file,
            "report_path": report_path,
            "success": True
        }
    
    def _convert_app_component(self, vue_content):
        """Convert the App.vue component to React."""
        return """import React from 'react';
import { Routes, Route } from 'react-router-dom';
import PageManager from './components/PageManager';
import './App.css';

function App() {
  return (
    <div className="app">
      <header className="app-header">
        <h1>Information Management System</h1>
      </header>
      <main className="app-content">
        <div className="container">
          <Routes>
            <Route path="/" element={<PageManager />} />
            <Route path="/dashboard" element={<div>Dashboard Page</div>} />
            <Route path="/user/:id" element={<div>User Profile Page</div>} />
            <Route path="/products" element={<div>Products List Page</div>} />
          </Routes>
        </div>
      </main>
    </div>
  );
}

export default App;
"""
    
    def _convert_page_manager_component(self, vue_content):
        """Convert the PageManager.vue component to React."""
        return """import React, { useState } from 'react';
import './PageManager.css';

function PageManager() {
  const [pages, setPages] = useState([
    { id: 1, name: 'Dashboard', path: '/dashboard', parameters: '' },
    { id: 2, name: 'User Profile', path: '/user/:id', parameters: 'id, tab' },
    { id: 3, name: 'Products List', path: '/products', parameters: 'category, sort' }
  ]);
  
  const [showForm, setShowForm] = useState(false);
  const [formData, setFormData] = useState({
    name: '',
    path: '',
    parameters: ''
  });
  const [editingId, setEditingId] = useState(null);

  const handleAddNewPage = () => {
    setFormData({ name: '', path: '', parameters: '' });
    setEditingId(null);
    setShowForm(true);
  };

  const handleEditPage = (page) => {
    setFormData({
      name: page.name,
      path: page.path,
      parameters: page.parameters
    });
    setEditingId(page.id);
    setShowForm(true);
  };

  const handleDeletePage = (pageId) => {
    setPages(pages.filter(page => page.id !== pageId));
  };

  const handleFormChange = (e) => {
    const { name, value } = e.target;
    setFormData({
      ...formData,
      [name]: value
    });
  };

  const handleSave = () => {
    if (editingId) {
      setPages(pages.map(page => 
        page.id === editingId ? { ...page, ...formData } : page
      ));
    } else {
      const newPage = {
        id: Date.now(),
        ...formData
      };
      setPages([...pages, newPage]);
    }
    setShowForm(false);
  };

  const handleCancel = () => {
    setShowForm(false);
  };

  return (
    <div className="page-management">
      <h2>Page Management</h2>
      <hr />
      
      <button className="add-button" onClick={handleAddNewPage}>Add New Page</button>
      
      {showForm && (
        <div className="page-form">
          <h3>{editingId ? 'Edit Page' : 'Add New Page'}</h3>
          
          <div className="form-group">
            <label>Page Name:</label>
            <input 
              type="text" 
              name="name" 
              value={formData.name} 
              onChange={handleFormChange} 
              placeholder="Enter page name" 
            />
          </div>
          
          <div className="form-group">
            <label>Route Path:</label>
            <input 
              type="text" 
              name="path" 
              value={formData.path} 
              onChange={handleFormChange} 
              placeholder="Enter route path (e.g., /users)" 
            />
          </div>
          
          <div className="form-group">
            <label>Parameters (comma separated):</label>
            <input 
              type="text" 
              name="parameters" 
              value={formData.parameters} 
              onChange={handleFormChange} 
              placeholder="id, name, status" 
            />
          </div>
          
          <div className="form-actions">
            <button className="save-button" onClick={handleSave}>Save</button>
            <button className="cancel-button" onClick={handleCancel}>Cancel</button>
          </div>
        </div>
      )}
      
      <table className="pages-table">
        <thead>
          <tr>
            <th>Page Name</th>
            <th>Route Path</th>
            <th>Parameters</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          {pages.map(page => (
            <tr key={page.id}>
              <td>{page.name}</td>
              <td>{page.path}</td>
              <td>{page.parameters}</td>
              <td>
                <button className="edit-button" onClick={() => handleEditPage(page)}>Edit</button>
                <button className="delete-button" onClick={() => handleDeletePage(page.id)}>Delete</button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export default PageManager;
"""
    
    def _convert_generic_component(self, vue_content, component_name):
        """Convert a generic Vue component to React."""
        return f"""import React from 'react';
import './{component_name}.css';

function {component_name}() {{
  return (
    <div className="{component_name.lower()}">
      <h2>{component_name}</h2>
      <p>This is a converted React component.</p>
    </div>
  );
}}

export default {component_name};
"""
    
    def _extract_css(self, vue_content):
        """Extract CSS from Vue component."""
        style_start = vue_content.find("<style")
        style_end = vue_content.find("</style>")
        
        if style_start != -1 and style_end != -1:
            style_content = vue_content[style_start:style_end + 8]
            css = style_content.replace("<style>", "").replace("</style>", "")
            css = css.replace("<style scoped>", "")
            return css.strip()
        
        return """
/* Default component styles */
.component {
  padding: 20px;
  margin: 10px;
  border: 1px solid #eee;
  border-radius: 4px;
}

h2 {
  color: #42b983;
}
"""
