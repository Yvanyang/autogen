"""
Documentation generator for creating HTML documentation for files and features.
"""
import os
from pathlib import Path
from typing import Dict, List, Optional, Union, Any
import json
from datetime import datetime

class DocumentationGenerator:
    """
    Generator class for creating HTML documentation for files and features.
    """

    def __init__(self, output_dir: Union[str, Path]):
        """
        Initialize the documentation generator.

        Args:
            output_dir: Output directory for documentation
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate_vue_component_doc(self, analysis: Dict[str, Any]) -> str:
        """
        Generate HTML documentation for a Vue component.

        Args:
            analysis: Analysis results from a Vue file

        Returns:
            HTML documentation as a string
        """
        file_path = analysis["file_path"]
        component_name = analysis["component_name"]
        
        html = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Component: {component_name}</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; }}
                h1, h2, h3 {{ color: #333; }}
                .container {{ max-width: 1200px; margin: 0 auto; }}
                .section {{ margin-bottom: 30px; }}
                .code {{ background-color: #f5f5f5; padding: 15px; border-radius: 5px; overflow-x: auto; }}
                table {{ width: 100%; border-collapse: collapse; }}
                th, td {{ padding: 8px; text-align: left; border-bottom: 1px solid #ddd; }}
                th {{ background-color: #f2f2f2; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>Component: {component_name}</h1>
                <p>File: {file_path}</p>
                <p>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                
                <div class="section">
                    <h2>Props</h2>
                    <div class="code">
                        <pre>{analysis["props"]}</pre>
                    </div>
                </div>
                
                <div class="section">
                    <h2>Data</h2>
                    <div class="code">
                        <pre>{analysis["data"]}</pre>
                    </div>
                </div>
                
                <div class="section">
                    <h2>Methods</h2>
                    <div class="code">
                        <pre>{analysis["methods"]}</pre>
                    </div>
                </div>
                
                <div class="section">
                    <h2>Dependencies</h2>
                    <ul>
        """
        
        for dep in analysis["component_dependencies"]:
            html += f"<li>{dep}</li>\n"
            
        html += """
                    </ul>
                </div>
                
                <div class="section">
                    <h2>Template</h2>
                    <div class="code">
                        <pre>{}</pre>
                    </div>
                </div>
            </div>
        </body>
        </html>
        """.format(analysis["template"].replace("<", "&lt;").replace(">", "&gt;"))
        
        return html

    def generate_index_doc(self, analyses: Dict[str, Dict[str, Any]]) -> str:
        """
        Generate an index HTML document for all components.

        Args:
            analyses: Mapping of file paths to analysis results

        Returns:
            HTML index document as a string
        """
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        html = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Vue Components Documentation</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; }}
                h1, h2, h3 {{ color: #333; }}
                .container {{ max-width: 1200px; margin: 0 auto; }}
                .component-list {{ list-style-type: none; padding: 0; }}
                .component-item {{ padding: 10px; border-bottom: 1px solid #eee; }}
                .component-item:hover {{ background-color: #f9f9f9; }}
                a {{ color: #0077cc; text-decoration: none; }}
                a:hover {{ text-decoration: underline; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>Vue Components Documentation</h1>
                <p>Generated: {timestamp}</p>
                
                <h2>Components</h2>
                <ul class="component-list">
        """
        
        for file_path, analysis in analyses.items():
            component_name = analysis["component_name"]
            component_file = os.path.basename(file_path).replace(".vue", ".html")
            html += f'<li class="component-item"><a href="{component_file}">{component_name}</a> ({file_path})</li>\n'
            
        html += """
                </ul>
            </div>
        </body>
        </html>
        """
        
        return html

    def save_documentation(self, analyses: Dict[str, Dict[str, Any]]) -> None:
        """
        Save documentation for all analyzed components.

        Args:
            analyses: Mapping of file paths to analysis results
        """
        for file_path, analysis in analyses.items():
            component_doc = self.generate_vue_component_doc(analysis)
            output_file = self.output_dir / f"{os.path.basename(file_path).replace('.vue', '.html')}"
            
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(component_doc)
        
        index_doc = self.generate_index_doc(analyses)
        index_file = self.output_dir / "index.html"
        
        with open(index_file, "w", encoding="utf-8") as f:
            f.write(index_doc)
            
        with open(self.output_dir / "analysis_data.json", "w", encoding="utf-8") as f:
            json.dump(analyses, f, indent=2)
            
    def generate_post_migration_doc(self, vue_analyses: Dict[str, Dict[str, Any]], 
                                   react_dir: Union[str, Path]) -> str:
        """
        Generate post-migration documentation comparing Vue and React implementations.
        
        Args:
            vue_analyses: Mapping of file paths to Vue component analysis results
            react_dir: Directory containing the React components
            
        Returns:
            HTML documentation as a string
        """
        react_dir = Path(react_dir)
        
        html = """
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Migration Documentation</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 0; padding: 20px; }
                h1, h2, h3 { color: #333; }
                .container { max-width: 1200px; margin: 0 auto; }
                .component { margin-bottom: 40px; border: 1px solid #ddd; border-radius: 5px; overflow: hidden; }
                .component-header { background-color: #f5f5f5; padding: 15px; border-bottom: 1px solid #ddd; }
                .component-body { padding: 20px; }
                .code-comparison { display: flex; flex-wrap: wrap; gap: 20px; }
                .code-block { flex: 1; min-width: 300px; }
                .code { background-color: #f5f5f5; padding: 15px; border-radius: 5px; overflow-x: auto; }
                .vue-code { border-left: 4px solid #42b883; }
                .react-code { border-left: 4px solid #61dafb; }
                table { width: 100%; border-collapse: collapse; margin-bottom: 20px; }
                th, td { padding: 8px; text-align: left; border-bottom: 1px solid #ddd; }
                th { background-color: #f2f2f2; }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>Vue to React Migration Documentation</h1>
                <p>Generated: {}</p>
                
                <h2>Components</h2>
        """.format(datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        
        for vue_file_path, vue_analysis in vue_analyses.items():
            component_name = vue_analysis["component_name"]
            react_file_path = react_dir / f"{component_name}.jsx"
            
            html += f"""
                <div class="component">
                    <div class="component-header">
                        <h3>{component_name}</h3>
                    </div>
                    <div class="component-body">
                        <p>Vue file: {vue_file_path}</p>
                        <p>React file: {react_file_path}</p>
                        
                        <h4>Component Structure</h4>
                        <div class="code-comparison">
                            <div class="code-block">
                                <h5>Vue Template</h5>
                                <div class="code vue-code">
                                    <pre>{vue_analysis["template"].replace("<", "&lt;").replace(">", "&gt;")}</pre>
                                </div>
                            </div>
            """
            
            if react_file_path.exists():
                with open(react_file_path, "r", encoding="utf-8") as f:
                    react_content = f.read()
                    
                html += f"""
                            <div class="code-block">
                                <h5>React JSX</h5>
                                <div class="code react-code">
                                    <pre>{react_content.replace("<", "&lt;").replace(">", "&gt;")}</pre>
                                </div>
                            </div>
                """
            else:
                html += f"""
                            <div class="code-block">
                                <h5>React JSX</h5>
                                <div class="code react-code">
                                    <pre>React component not found at {react_file_path}</pre>
                                </div>
                            </div>
                """
                
            html += """
                        </div>
                        
                        <h4>Migration Notes</h4>
                        <table>
                            <tr>
                                <th>Vue Feature</th>
                                <th>React Equivalent</th>
                            </tr>
            """
            
            if vue_analysis["props"]:
                html += """
                            <tr>
                                <td>Props</td>
                                <td>Function parameters and PropTypes</td>
                            </tr>
                """
                
            if vue_analysis["data"]:
                html += """
                            <tr>
                                <td>Data properties</td>
                                <td>useState hooks</td>
                            </tr>
                """
                
            if vue_analysis["methods"]:
                html += """
                            <tr>
                                <td>Methods</td>
                                <td>Regular functions or useCallback</td>
                            </tr>
                """
                
            html += """
                        </table>
                    </div>
                </div>
            """
            
        html += """
            </div>
        </body>
        </html>
        """
        
        return html
        
    def save_post_migration_doc(self, vue_analyses: Dict[str, Dict[str, Any]], 
                               react_dir: Union[str, Path]) -> None:
        """
        Save post-migration documentation.
        
        Args:
            vue_analyses: Mapping of file paths to Vue component analysis results
            react_dir: Directory containing the React components
        """
        doc = self.generate_post_migration_doc(vue_analyses, react_dir)
        output_file = self.output_dir / "migration_documentation.html"
        
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(doc)
