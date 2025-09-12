"""Data profiling and visualization utilities using YData profiling and matplotlib."""

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from loguru import logger


def generate_exploratory_data_analysis_report(
    ts_data: pd.DataFrame,
    output_html_path: str,
) -> None:
    """
    Generates an HTML file exploratory data analysis charts for the given `ts_data` and
    saves it locally to the given `output_html_path`

    Args:
        ts_data: Time series DataFrame to analyze
        output_html_path: Path to save the HTML EDA report
    """
    from ydata_profiling import ProfileReport

    profile = ProfileReport(
        ts_data, tsmode=True, sortby='window_start_ms', title='Technical indicators EDA'
    )
    profile.to_file(output_html_path)
    logger.info(f"EDA report saved to: {output_html_path}")


def generate_training_data_plots(
    ts_data: pd.DataFrame,
    train_data: pd.DataFrame,
    test_data: pd.DataFrame,
    output_plot_path: str,
) -> None:
    """
    Generates comprehensive plots of the training data and saves them to a single image file.

    Args:
        ts_data: Full time series dataset
        train_data: Training subset of the data
        test_data: Test subset of the data
        output_plot_path: Path to save the combined plot image
    """
    # Set style for better-looking plots
    plt.style.use('default')
    sns.set_palette("husl")

    # Create a figure with subplots
    fig, axes = plt.subplots(2, 3, figsize=(20, 12))
    fig.suptitle('Training Data Analysis', fontsize=16, fontweight='bold')

    # Convert window_start_ms to datetime for better x-axis
    ts_data_plot = ts_data.copy()
    ts_data_plot['datetime'] = pd.to_datetime(
        ts_data_plot['window_start_ms'], unit='ms')

    # 1. Time series plot of OHLC data
    ax1 = axes[0, 0]
    ax1.plot(ts_data_plot['datetime'], ts_data_plot['close'],
             label='Close Price', linewidth=1)
    ax1.fill_between(ts_data_plot['datetime'], ts_data_plot['low'], ts_data_plot['high'],
                     alpha=0.3, label='High-Low Range')
    ax1.set_title('Price Time Series')
    ax1.set_xlabel('Time')
    ax1.set_ylabel('Price')
    ax1.legend()
    ax1.tick_params(axis='x', rotation=45)

    # 2. Price distribution
    ax2 = axes[0, 1]
    ax2.hist(ts_data['close'], bins=50, alpha=0.7, edgecolor='black')
    ax2.axvline(ts_data['close'].mean(), color='red',
                linestyle='--', label=f'Mean: {ts_data["close"].mean():.2f}')
    ax2.set_title('Close Price Distribution')
    ax2.set_xlabel('Price')
    ax2.set_ylabel('Frequency')
    ax2.legend()

    # 3. Feature correlation heatmap (subset of features for readability)
    ax3 = axes[0, 2]
    numeric_features = ['open', 'high', 'low', 'close', 'target']
    corr_matrix = ts_data[numeric_features].corr()
    sns.heatmap(corr_matrix, annot=True, cmap='coolwarm',
                center=0, ax=ax3, fmt='.2f')
    ax3.set_title('Feature Correlations')

    # 4. Target distribution
    ax4 = axes[1, 0]
    ax4.hist(ts_data['target'].dropna(), bins=50, alpha=0.7, edgecolor='black')
    ax4.axvline(ts_data['target'].mean(), color='red', linestyle='--',
                label=f'Mean: {ts_data["target"].mean():.2f}')
    ax4.set_title('Target Distribution')
    ax4.set_xlabel('Target Value')
    ax4.set_ylabel('Frequency')
    ax4.legend()

    # 5. Train/Test split visualization
    ax5 = axes[1, 1]
    train_indices = range(len(train_data))
    test_indices = range(len(train_data), len(train_data) + len(test_data))

    ax5.scatter(train_indices, train_data['close'],
                alpha=0.6, s=1, label='Train', color='blue')
    ax5.scatter(test_indices, test_data['close'],
                alpha=0.6, s=1, label='Test', color='orange')
    ax5.axvline(len(train_data), color='red',
                linestyle='--', label='Train/Test Split')
    ax5.set_title('Train/Test Split')
    ax5.set_xlabel('Sample Index')
    ax5.set_ylabel('Close Price')
    ax5.legend()

    # 6. Data quality metrics
    ax6 = axes[1, 2]
    quality_metrics = {
        'Total Samples': len(ts_data),
        'Train Samples': len(train_data),
        'Test Samples': len(test_data),
        'Missing Values': ts_data.isnull().sum().sum(),
        'Unique OHLC': len(ts_data[['open', 'high', 'low', 'close']].drop_duplicates())
    }

    bars = ax6.bar(range(len(quality_metrics)), list(quality_metrics.values()))
    ax6.set_xticks(range(len(quality_metrics)))
    ax6.set_xticklabels(quality_metrics.keys(), rotation=45, ha='right')
    ax6.set_title('Data Quality Metrics')
    ax6.set_ylabel('Count')

    # Add value labels on bars
    for bar, value in zip(bars, quality_metrics.values()):
        ax6.text(bar.get_x() + bar.get_width()/2, bar.get_height() + max(quality_metrics.values())*0.01,
                 str(value), ha='center', va='bottom', fontsize=9)

    # Adjust layout and save
    plt.tight_layout()
    plt.savefig(output_plot_path, dpi=300, bbox_inches='tight')
    plt.close()
    logger.info(f"Training data plots saved to: {output_plot_path}")


def generate_data_drift_report(current_data: pd.DataFrame, model_name: str) -> None:
    """
    Generate a data drift report comparing current data to the data used by the model in the registry.
    
    Args:
        current_data: Current dataset to analyze
        model_name: Name of the model to compare against
    """
    # TODO: Implement data drift analysis
    # This would compare current_data statistical properties with 
    # the data used to train the model stored in the registry
    logger.info(f"Data drift analysis for model {model_name} - TODO: Implementation needed")
    pass