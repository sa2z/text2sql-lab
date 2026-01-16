"""
Visualization utilities for creating charts from data
"""
from typing import Dict, Any, Optional
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
import plotly.graph_objects as go


def create_bar_chart(df: pd.DataFrame, x_col: str, y_col: str, 
                     title: str = "", use_plotly: bool = True) -> Any:
    """
    Create a bar chart from DataFrame
    
    Args:
        df: DataFrame with data
        x_col: Column name for x-axis
        y_col: Column name for y-axis
        title: Chart title
        use_plotly: Use plotly (interactive) or matplotlib (static)
    
    Returns:
        Chart object
    """
    if use_plotly:
        fig = px.bar(df, x=x_col, y=y_col, title=title)
        fig.update_layout(xaxis_title=x_col, yaxis_title=y_col)
        return fig
    else:
        fig, ax = plt.subplots(figsize=(10, 6))
        df.plot(kind='bar', x=x_col, y=y_col, ax=ax)
        ax.set_title(title)
        ax.set_xlabel(x_col)
        ax.set_ylabel(y_col)
        plt.xticks(rotation=45)
        plt.tight_layout()
        return fig


def create_line_chart(df: pd.DataFrame, x_col: str, y_col: str, 
                      title: str = "", use_plotly: bool = True) -> Any:
    """Create a line chart from DataFrame"""
    if use_plotly:
        fig = px.line(df, x=x_col, y=y_col, title=title)
        fig.update_layout(xaxis_title=x_col, yaxis_title=y_col)
        return fig
    else:
        fig, ax = plt.subplots(figsize=(10, 6))
        df.plot(kind='line', x=x_col, y=y_col, ax=ax, marker='o')
        ax.set_title(title)
        ax.set_xlabel(x_col)
        ax.set_ylabel(y_col)
        plt.xticks(rotation=45)
        plt.tight_layout()
        return fig


def create_pie_chart(df: pd.DataFrame, names_col: str, values_col: str, 
                     title: str = "", use_plotly: bool = True) -> Any:
    """Create a pie chart from DataFrame"""
    if use_plotly:
        fig = px.pie(df, names=names_col, values=values_col, title=title)
        return fig
    else:
        fig, ax = plt.subplots(figsize=(10, 8))
        df.set_index(names_col)[values_col].plot(kind='pie', ax=ax, autopct='%1.1f%%')
        ax.set_title(title)
        ax.set_ylabel('')
        plt.tight_layout()
        return fig


def create_scatter_plot(df: pd.DataFrame, x_col: str, y_col: str, 
                        color_col: str = None, title: str = "", 
                        use_plotly: bool = True) -> Any:
    """Create a scatter plot from DataFrame"""
    if use_plotly:
        fig = px.scatter(df, x=x_col, y=y_col, color=color_col, title=title)
        fig.update_layout(xaxis_title=x_col, yaxis_title=y_col)
        return fig
    else:
        fig, ax = plt.subplots(figsize=(10, 6))
        if color_col:
            for category in df[color_col].unique():
                subset = df[df[color_col] == category]
                ax.scatter(subset[x_col], subset[y_col], label=category, alpha=0.6)
            ax.legend()
        else:
            ax.scatter(df[x_col], df[y_col], alpha=0.6)
        ax.set_title(title)
        ax.set_xlabel(x_col)
        ax.set_ylabel(y_col)
        plt.tight_layout()
        return fig


def create_heatmap(df: pd.DataFrame, title: str = "", 
                   use_plotly: bool = True) -> Any:
    """Create a heatmap from DataFrame (correlation matrix)"""
    if use_plotly:
        fig = px.imshow(df, title=title, text_auto=True, aspect="auto")
        return fig
    else:
        fig, ax = plt.subplots(figsize=(10, 8))
        sns.heatmap(df, annot=True, fmt='.2f', cmap='coolwarm', ax=ax)
        ax.set_title(title)
        plt.tight_layout()
        return fig


def auto_visualize(df: pd.DataFrame, query: str = "") -> Optional[Any]:
    """
    Automatically choose and create an appropriate visualization
    based on the DataFrame structure
    
    Args:
        df: DataFrame to visualize
        query: Optional natural language query for context
    
    Returns:
        Chart object or None if no suitable visualization
    """
    if df.empty:
        print("DataFrame is empty, cannot create visualization")
        return None
    
    # If only one row, show as table
    if len(df) == 1:
        print("Single row result - displaying as table")
        return df
    
    # Get numeric and categorical columns
    numeric_cols = df.select_dtypes(include=['int64', 'float64']).columns.tolist()
    categorical_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
    
    # If we have one categorical and one numeric column - bar chart
    if len(categorical_cols) == 1 and len(numeric_cols) == 1:
        return create_bar_chart(
            df, categorical_cols[0], numeric_cols[0],
            title=f"{numeric_cols[0]} by {categorical_cols[0]}"
        )
    
    # If we have date column and numeric column - line chart
    date_cols = df.select_dtypes(include=['datetime64']).columns.tolist()
    if len(date_cols) >= 1 and len(numeric_cols) >= 1:
        return create_line_chart(
            df, date_cols[0], numeric_cols[0],
            title=f"{numeric_cols[0]} over time"
        )
    
    # If we have multiple numeric columns - correlation heatmap
    if len(numeric_cols) > 2:
        corr_matrix = df[numeric_cols].corr()
        return create_heatmap(corr_matrix, title="Correlation Matrix")
    
    # If we have two numeric columns - scatter plot
    if len(numeric_cols) == 2:
        color = categorical_cols[0] if categorical_cols else None
        return create_scatter_plot(
            df, numeric_cols[0], numeric_cols[1], 
            color_col=color,
            title=f"{numeric_cols[1]} vs {numeric_cols[0]}"
        )
    
    # Default: just show the table
    print("Showing data as table")
    return df
