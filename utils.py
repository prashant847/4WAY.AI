"""
Utility functions for the traffic management system
"""
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List
import matplotlib.pyplot as plt
import numpy as np
from config import Config


def save_results_to_json(results: Dict, filename: str = None) -> str:
    """
    Save analysis results to JSON file
    
    Args:
        results: Results dictionary
        filename: Output filename (optional)
        
    Returns:
        Path to saved file
    """
    if filename is None:
        filename = f"results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    
    filepath = Config.OUTPUT_DIR / filename
    
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    return str(filepath)


def load_results_from_json(filepath: str) -> Dict:
    """Load results from JSON file"""
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)


def create_congestion_chart(lane_results: List[Dict], output_path: str = None):
    """
    Create a bar chart showing congestion levels across lanes
    
    Args:
        lane_results: List of lane analysis results
        output_path: Output path for chart image
    """
    if not lane_results:
        return None
    
    lane_names = [r['lane_name'] for r in lane_results]
    congestion_scores = [r['congestion_score'] for r in lane_results]
    total_vehicles = [r['total_vehicles'] for r in lane_results]
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
    
    # Congestion scores
    colors = ['red' if score >= 60 else 'orange' if score >= 35 else 'yellow' if score >= 15 else 'green' 
              for score in congestion_scores]
    
    ax1.bar(lane_names, congestion_scores, color=colors, alpha=0.7)
    ax1.set_ylabel('Congestion Score', fontsize=12)
    ax1.set_title('Traffic Congestion by Lane', fontsize=14, fontweight='bold')
    ax1.set_ylim(0, 100)
    ax1.grid(axis='y', alpha=0.3)
    
    # Add value labels
    for i, (name, score) in enumerate(zip(lane_names, congestion_scores)):
        ax1.text(i, score + 2, f'{score:.1f}', ha='center', va='bottom', fontweight='bold')
    
    # Total vehicles
    ax2.bar(lane_names, total_vehicles, color='steelblue', alpha=0.7)
    ax2.set_ylabel('Total Vehicles', fontsize=12)
    ax2.set_title('Vehicle Count by Lane', fontsize=14, fontweight='bold')
    ax2.grid(axis='y', alpha=0.3)
    
    # Add value labels
    for i, (name, count) in enumerate(zip(lane_names, total_vehicles)):
        ax2.text(i, count + max(total_vehicles)*0.02, str(count), ha='center', va='bottom', fontweight='bold')
    
    plt.tight_layout()
    
    if output_path is None:
        output_path = Config.OUTPUT_DIR / f"congestion_chart_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
    
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    
    return str(output_path)


def create_vehicle_distribution_chart(lane_results: List[Dict], output_path: str = None):
    """
    Create pie charts showing vehicle type distribution for each lane
    
    Args:
        lane_results: List of lane analysis results
        output_path: Output path for chart image
    """
    if not lane_results or len(lane_results) == 0:
        return None
    
    fig, axes = plt.subplots(2, 2, figsize=(14, 12))
    axes = axes.flatten()
    
    colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#FFA07A', '#98D8C8']
    
    for idx, result in enumerate(lane_results[:4]):
        vehicle_counts = result.get('vehicle_counts', {})
        
        # Filter out zero counts
        filtered_counts = {k: v for k, v in vehicle_counts.items() if v > 0}
        
        if filtered_counts:
            labels = list(filtered_counts.keys())
            sizes = list(filtered_counts.values())
            
            wedges, texts, autotexts = axes[idx].pie(
                sizes,
                labels=labels,
                autopct='%1.1f%%',
                colors=colors[:len(labels)],
                startangle=90
            )
            
            # Beautify text
            for text in texts:
                text.set_fontsize(10)
                text.set_fontweight('bold')
            
            for autotext in autotexts:
                autotext.set_color('white')
                autotext.set_fontsize(9)
                autotext.set_fontweight('bold')
        
        axes[idx].set_title(
            f"{result['lane_name']}\nTotal: {result['total_vehicles']} vehicles",
            fontsize=12,
            fontweight='bold'
        )
    
    plt.suptitle('Vehicle Type Distribution by Lane', fontsize=16, fontweight='bold', y=0.98)
    plt.tight_layout()
    
    if output_path is None:
        output_path = Config.OUTPUT_DIR / f"vehicle_distribution_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
    
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    
    return str(output_path)


def generate_report(analysis_result: Dict, output_path: str = None) -> str:
    """
    Generate a comprehensive text report
    
    Args:
        analysis_result: Complete analysis results
        output_path: Output path for report file
        
    Returns:
        Path to saved report
    """
    if output_path is None:
        output_path = Config.OUTPUT_DIR / f"traffic_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("="*80 + "\n")
        f.write("          ADVANCED TRAFFIC MANAGEMENT SYSTEM - ANALYSIS REPORT\n")
        f.write("="*80 + "\n\n")
        
        f.write(f"Report Generated: {analysis_result.get('timestamp', 'N/A')}\n")
        f.write(f"Total Lanes Analyzed: {analysis_result.get('total_lanes', 0)}\n\n")
        
        # Lane Statistics
        f.write("-"*80 + "\n")
        f.write("LANE STATISTICS\n")
        f.write("-"*80 + "\n\n")
        
        stats = analysis_result.get('lane_statistics', {})
        f.write(f"Total Vehicles (All Lanes): {stats.get('total_vehicles_all_lanes', 0)}\n")
        f.write(f"Average Congestion Score: {stats.get('average_congestion_score', 0):.2f}\n")
        f.write(f"Most Congested Lane: {stats.get('most_congested_lane', 'N/A')}\n")
        f.write(f"Least Congested Lane: {stats.get('least_congested_lane', 'N/A')}\n\n")
        
        # Priority Ranking
        f.write("-"*80 + "\n")
        f.write("PRIORITY RANKING\n")
        f.write("-"*80 + "\n\n")
        
        priorities = analysis_result.get('priority_ranking', [])
        for priority in priorities:
            f.write(f"Rank {priority['rank']}: {priority['lane_name']}\n")
            f.write(f"  Priority Score: {priority['priority_score']:.2f}\n")
            f.write(f"  Congestion Level: {priority['congestion_level']}\n")
            f.write(f"  Total Vehicles: {priority['total_vehicles']}\n")
            f.write(f"  Max Vehicles in Frame: {priority['max_vehicles_in_frame']}\n")
            f.write(f"  Heavy Vehicles: {priority['heavy_vehicles']}\n\n")
        
        # Signal Assignment
        f.write("-"*80 + "\n")
        f.write("SIGNAL ASSIGNMENT\n")
        f.write("-"*80 + "\n\n")
        
        signals = analysis_result.get('signal_assignment', {})
        for lane_id, signal in signals.items():
            lane_name = Config.LANE_NAMES[lane_id] if lane_id < len(Config.LANE_NAMES) else f'Lane {lane_id}'
            icon = '🟢' if signal == 'GREEN' else '🔴'
            f.write(f"{icon} {lane_name}: {signal}\n")
        
        f.write("\n")
        
        # Recommendations
        f.write("-"*80 + "\n")
        f.write("RECOMMENDATIONS\n")
        f.write("-"*80 + "\n\n")
        
        recommendations = analysis_result.get('recommendations', [])
        for i, rec in enumerate(recommendations, 1):
            f.write(f"{i}. {rec}\n")
        
        f.write("\n" + "="*80 + "\n")
        f.write("                              END OF REPORT\n")
        f.write("="*80 + "\n")
    
    return str(output_path)


def format_duration(seconds: int) -> str:
    """Format duration in seconds to human-readable string"""
    if seconds < 60:
        return f"{seconds}s"
    elif seconds < 3600:
        minutes = seconds // 60
        secs = seconds % 60
        return f"{minutes}m {secs}s"
    else:
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        return f"{hours}h {minutes}m"
