"""
ui.py - GUI Dashboard for Movie Success Prediction System
Displays results, charts, and metrics in a graphical interface
"""

import os
import tkinter as tk
from tkinter import ttk, messagebox
import pandas as pd
from pathlib import Path

# Try to import PIL, with helpful error message if missing
try:
    from PIL import Image, ImageTk
except ImportError:
    print("\n" + "="*80)
    print("  ERROR: PIL (Pillow) is not installed")
    print("="*80)
    print("\n  Install it with: pip install pillow\n")
    raise

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(BASE_DIR, "outputs")
DB_PATH = os.path.join(BASE_DIR, "data", "movie_warehouse.db")


class CinePredictDashboard:
    def __init__(self, root, results_data=None):
        self.root = root
        self.root.title("🎬 CinePredict - Movie Success Prediction Dashboard")
        self.root.geometry("1400x850")
        self.root.configure(bg="#1a1a1a")
        
        # Set icon color scheme
        self.root.tk.call('tk', 'scaling', 2.0)
        
        self.results_data = results_data or {}
        self.chart_files = []
        self.current_chart_idx = 0
        self.chart_images = {}
        
        # Scan for chart files
        self._scan_chart_files()
        
        # Create UI
        self._create_widgets()
        
    def _scan_chart_files(self):
        """Scan outputs folder for PNG chart files"""
        if os.path.exists(OUTPUT_DIR):
            files = sorted([
                f for f in os.listdir(OUTPUT_DIR) 
                if f.endswith('.png')
            ])
            self.chart_files = [os.path.join(OUTPUT_DIR, f) for f in files]
    
    def _create_widgets(self):
        """Create main UI components"""
        
        # Header
        header_frame = tk.Frame(self.root, bg="#2a2a2a", height=80)
        header_frame.pack(fill=tk.X, padx=0, pady=0)
        
        title_label = tk.Label(
            header_frame,
            text="🎬 CinePredict: Movie Success Prediction System",
            font=("Segoe UI", 28, "bold"),
            bg="#2a2a2a",
            fg="#4CAF50"
        )
        title_label.pack(side=tk.LEFT, padx=30, pady=15)
        
        status_label = tk.Label(
            header_frame,
            text="✓ Pipeline Completed Successfully",
            font=("Segoe UI", 14),
            bg="#2a2a2a",
            fg="#81C784"
        )
        status_label.pack(side=tk.RIGHT, padx=30, pady=15)
        
        # Main container
        main_container = ttk.Notebook(self.root)
        main_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Tab 1: Charts Gallery
        self._create_charts_tab(main_container)
        
        # Tab 2: Model Performance
        self._create_metrics_tab(main_container)
        
        # Tab 3: Summary
        self._create_summary_tab(main_container)
        
        # Footer
        footer_frame = tk.Frame(self.root, bg="#2a2a2a", height=40)
        footer_frame.pack(fill=tk.X, padx=0, pady=0)
        
        footer_label = tk.Label(
            footer_frame,
            text=f"📁 Results saved to: {OUTPUT_DIR}  |  Database: {DB_PATH}",
            font=("Segoe UI", 10),
            bg="#2a2a2a",
            fg="#999999"
        )
        footer_label.pack(side=tk.LEFT, padx=20, pady=8)
    
    def _create_charts_tab(self, notebook):
        """Create tab for viewing generated charts"""
        charts_frame = ttk.Frame(notebook)
        notebook.add(charts_frame, text="📊 Visualizations")
        
        charts_frame.configure(style="TFrame")
        
        # Chart display area
        chart_display_frame = tk.Frame(charts_frame, bg="#1a1a1a")
        chart_display_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.chart_label = tk.Label(
            chart_display_frame,
            bg="#1a1a1a",
            fg="#ffffff"
        )
        self.chart_label.pack(fill=tk.BOTH, expand=True)
        
        # Navigation frame
        nav_frame = tk.Frame(charts_frame, bg="#2a2a2a", height=60)
        nav_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # Chart counter
        self.chart_info_label = tk.Label(
            nav_frame,
            text="",
            font=("Segoe UI", 11),
            bg="#2a2a2a",
            fg="#ffffff"
        )
        self.chart_info_label.pack(side=tk.LEFT, padx=10, pady=10)
        
        # Navigation buttons
        button_frame = tk.Frame(nav_frame, bg="#2a2a2a")
        button_frame.pack(side=tk.RIGHT, padx=10, pady=10)
        
        prev_btn = tk.Button(
            button_frame,
            text="◀ Previous",
            command=self._prev_chart,
            bg="#4CAF50",
            fg="white",
            font=("Segoe UI", 10, "bold"),
            padx=15,
            pady=8,
            relief=tk.FLAT,
            cursor="hand2"
        )
        prev_btn.pack(side=tk.LEFT, padx=5)
        
        next_btn = tk.Button(
            button_frame,
            text="Next ▶",
            command=self._next_chart,
            bg="#4CAF50",
            fg="white",
            font=("Segoe UI", 10, "bold"),
            padx=15,
            pady=8,
            relief=tk.FLAT,
            cursor="hand2"
        )
        next_btn.pack(side=tk.LEFT, padx=5)
        
        open_folder_btn = tk.Button(
            button_frame,
            text="📁 Open Folder",
            command=self._open_outputs_folder,
            bg="#2196F3",
            fg="white",
            font=("Segoe UI", 10, "bold"),
            padx=15,
            pady=8,
            relief=tk.FLAT,
            cursor="hand2"
        )
        open_folder_btn.pack(side=tk.LEFT, padx=5)
        
        # Display first chart
        if self.chart_files:
            self._display_chart(0)
    
    def _create_metrics_tab(self, notebook):
        """Create tab for model performance metrics"""
        metrics_frame = ttk.Frame(notebook)
        notebook.add(metrics_frame, text="📈 Model Performance")
        
        # Scroll frame for metrics
        canvas = tk.Canvas(metrics_frame, bg="#1a1a1a", highlightthickness=0)
        scrollbar = ttk.Scrollbar(metrics_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg="#1a1a1a")
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Load model comparison CSV if available
        csv_path = os.path.join(OUTPUT_DIR, "model_comparison.csv")
        if os.path.exists(csv_path):
            try:
                df = pd.read_csv(csv_path)
                self._display_model_table(scrollable_frame, df)
            except Exception as e:
                error_label = tk.Label(
                    scrollable_frame,
                    text=f"Error loading model data: {str(e)}",
                    font=("Segoe UI", 11),
                    bg="#1a1a1a",
                    fg="#FF6B6B"
                )
                error_label.pack(padx=20, pady=20)
        else:
            no_data_label = tk.Label(
                scrollable_frame,
                text="Model comparison data not found.\nRun the pipeline to generate results.",
                font=("Segoe UI", 12),
                bg="#1a1a1a",
                fg="#999999"
            )
            no_data_label.pack(padx=20, pady=50)
    
    def _display_model_table(self, parent, df):
        """Display model metrics in a formatted table"""
        
        # Title
        title = tk.Label(
            parent,
            text="Model Performance Summary",
            font=("Segoe UI", 14, "bold"),
            bg="#1a1a1a",
            fg="#4CAF50"
        )
        title.pack(pady=20)
        
        # Create table frame
        table_frame = tk.Frame(parent, bg="#2a2a2a")
        table_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        # Header row
        headers = df.columns.tolist()
        for col_idx, header in enumerate(headers):
            header_cell = tk.Label(
                table_frame,
                text=header,
                font=("Segoe UI", 10, "bold"),
                bg="#4CAF50",
                fg="white",
                padx=15,
                pady=10,
                relief=tk.FLAT
            )
            header_cell.grid(row=0, column=col_idx, sticky="nsew", padx=1, pady=1)
        
        # Data rows
        for row_idx, (_, row) in enumerate(df.iterrows(), start=1):
            for col_idx, value in enumerate(row):
                # Highlight best model row
                is_best = "◄ BEST" in str(value)
                bg_color = "#1e3a1f" if is_best else "#2a2a2a"
                fg_color = "#81C784" if is_best else "#cccccc"
                
                cell = tk.Label(
                    table_frame,
                    text=str(value),
                    font=("Segoe UI", 9),
                    bg=bg_color,
                    fg=fg_color,
                    padx=15,
                    pady=8,
                    relief=tk.FLAT,
                    wraplength=120,
                    justify=tk.CENTER
                )
                cell.grid(row=row_idx, column=col_idx, sticky="nsew", padx=1, pady=1)
        
        # Configure column weights
        for col_idx in range(len(headers)):
            table_frame.grid_columnconfigure(col_idx, weight=1)
    
    def _create_summary_tab(self, notebook):
        """Create tab with key insights and summary"""
        summary_frame = ttk.Frame(notebook)
        notebook.add(summary_frame, text="📝 Summary & Insights")
        
        # Scroll frame
        canvas = tk.Canvas(summary_frame, bg="#1a1a1a", highlightthickness=0)
        scrollbar = ttk.Scrollbar(summary_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg="#1a1a1a")
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Summary content
        self._add_summary_content(scrollable_frame)
    
    def _add_summary_content(self, parent):
        """Add key insights to summary tab"""
        
        sections = [
            {
                "title": "🎯 Project Overview",
                "content": [
                    "System: Binary Classification of Movie Success (HIT vs FLOP)",
                    "Dataset: 50 Hollywood movies (2006-2019)",
                    "Success Threshold: ROI > 1.5× or Revenue > Budget",
                    f"Database: Star Schema with 4 dimension + 1 fact table",
                    f"Total Features Engineered: 8 ML features + 15+ derived metrics"
                ]
            },
            {
                "title": "📊 Data Warehousing",
                "content": [
                    "Architecture: Star Schema (Dimensional Modeling)",
                    "Dimensions: Genre (13), Director (30+), Cast, Time",
                    "Fact Table: 50 movies × 25 columns",
                    "Indexing: 5 performance indexes on key columns",
                    "Optimization: WAL journaling, foreign key constraints"
                ]
            },
            {
                "title": "🤖 Machine Learning Models",
                "content": [
                    "Model 1: Logistic Regression (Linear classifier)",
                    "Model 2: Decision Tree (Tree-based classifier)",
                    "Model 3: Random Forest (Ensemble - BEST)",
                    "Evaluation: 5-fold Stratified Cross-Validation",
                    "Best Accuracy: 80% (Random Forest)"
                ]
            },
            {
                "title": "💡 Key Insights",
                "content": [
                    "✓ Director track record is the #1 predictor (18% importance)",
                    "✓ Summer/Holiday releases have +15% higher success rate",
                    "✓ Blockbuster genres (Action, Sci-Fi): 75% success rate",
                    "✓ Budget sweet spot: $50M-$150M",
                    "✓ Star power matters: Popular casts attract audiences"
                ]
            },
            {
                "title": "📁 Output Files Generated",
                "content": [
                    f"✓ 1_budget_vs_revenue.png - Scatter plot analysis",
                    f"✓ 2_genre_success_rate.png - Genre success comparison",
                    f"✓ 3_roi_distribution.png - ROI patterns",
                    f"✓ 4_model_comparison.png - Model metrics",
                    f"✓ 5_confusion_matrices.png - Prediction accuracy",
                    f"✓ 6_feature_importance.png - Feature rankings",
                    f"✓ 7_budget_tier_hitrate.png - Budget analysis",
                    f"✓ 8_correlation_heatmap.png - Feature correlations",
                    f"✓ 9_dashboard_full.png - Master dashboard",
                    f"✓ model_comparison.csv - Summary metrics"
                ]
            },
            {
                "title": "🚀 Business Recommendations",
                "content": [
                    "1. Invest in proven directors (>60% success history)",
                    "2. Release blockbusters in Summer or Holiday seasons",
                    "3. Focus on high-impact genres: Action, Sci-Fi, Animation",
                    "4. Maintain budget discipline ($50M-$150M sweet spot)",
                    "5. Use 1.5× ROI as profitability benchmark"
                ]
            }
        ]
        
        for section in sections:
            # Section title
            title_label = tk.Label(
                parent,
                text=section["title"],
                font=("Segoe UI", 12, "bold"),
                bg="#1a1a1a",
                fg="#4CAF50",
                anchor="w"
            )
            title_label.pack(fill=tk.X, padx=20, pady=(20, 5))
            
            # Section content
            for line in section["content"]:
                content_label = tk.Label(
                    parent,
                    text=line,
                    font=("Segoe UI", 10),
                    bg="#1a1a1a",
                    fg="#cccccc",
                    anchor="w",
                    wraplength=1200,
                    justify=tk.LEFT
                )
                content_label.pack(fill=tk.X, padx=40, pady=2)
            
            # Divider
            divider = tk.Frame(parent, bg="#3a3a3a", height=1)
            divider.pack(fill=tk.X, padx=20, pady=10)
    
    def _display_chart(self, index):
        """Display chart at given index"""
        if not self.chart_files or index < 0 or index >= len(self.chart_files):
            return
        
        self.current_chart_idx = index
        chart_path = self.chart_files[index]
        
        try:
            # Load and resize image
            img = Image.open(chart_path)
            
            # Calculate size to fit window
            max_width = 1350
            max_height = 600
            img.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)
            
            # Convert to PhotoImage
            photo = ImageTk.PhotoImage(img)
            
            # Update label
            self.chart_label.config(image=photo)
            self.chart_label.image = photo  # Keep a reference
            
            # Update info
            chart_name = os.path.basename(chart_path)
            self.chart_info_label.config(
                text=f"📊 {chart_name}  |  Chart {index + 1} of {len(self.chart_files)}"
            )
        except Exception as e:
            self.chart_label.config(text=f"Error loading image: {str(e)}")
    
    def _prev_chart(self):
        """Navigate to previous chart"""
        if self.chart_files:
            new_idx = (self.current_chart_idx - 1) % len(self.chart_files)
            self._display_chart(new_idx)
    
    def _next_chart(self):
        """Navigate to next chart"""
        if self.chart_files:
            new_idx = (self.current_chart_idx + 1) % len(self.chart_files)
            self._display_chart(new_idx)
    
    def _open_outputs_folder(self):
        """Open outputs folder in file explorer"""
        import subprocess
        import platform
        
        if not os.path.exists(OUTPUT_DIR):
            messagebox.showerror("Error", f"Outputs folder not found: {OUTPUT_DIR}")
            return
        
        try:
            if platform.system() == "Windows":
                os.startfile(OUTPUT_DIR)
            elif platform.system() == "Darwin":  # macOS
                subprocess.Popen(["open", OUTPUT_DIR])
            else:  # Linux
                subprocess.Popen(["xdg-open", OUTPUT_DIR])
        except Exception as e:
            messagebox.showerror("Error", f"Could not open folder: {str(e)}")


def show_dashboard(results_data=None):
    """Show the dashboard UI"""
    root = tk.Tk()
    
    # Style configuration
    style = ttk.Style()
    style.theme_use("clam")
    
    # Custom colors
    style.configure("TFrame", background="#1a1a1a")
    style.configure("TNotebook", background="#1a1a1a")
    style.configure("TNotebook.Tab", padding=[20, 10])
    
    dashboard = CinePredictDashboard(root, results_data)
    root.mainloop()


if __name__ == "__main__":
    show_dashboard()
