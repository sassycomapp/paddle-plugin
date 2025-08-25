"""
Token Analytics and Reporting System

This module provides comprehensive analytics and reporting capabilities for the token management system.
It supports usage trend analysis, cost analysis, forecasting, and various report formats.
"""

import logging
import json
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Union
from dataclasses import dataclass, asdict
from enum import Enum
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import io
import base64

from simba.simba.database.postgres import PostgresDB
from src.token_monitoring import TokenMonitoringSystem, TokenUsageStatus, SystemHealthMetrics

logger = logging.getLogger(__name__)


class ReportFormat(Enum):
    """Report output formats."""
    JSON = "json"
    CSV = "csv"
    HTML = "html"
    PDF = "pdf"
    EXCEL = "excel"
    PNG = "png"


class TimeGranularity(Enum):
    """Time granularity for analytics."""
    HOURLY = "hourly"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"


class TrendDirection(Enum):
    """Trend direction indicators."""
    INCREASING = "increasing"
    DECREASING = "decreasing"
    STABLE = "stable"
    VOLATILE = "volatile"


@dataclass
class UsageTrend:
    """Usage trend data."""
    period_start: datetime
    period_end: datetime
    total_tokens: int
    average_tokens_per_request: float
    trend_direction: TrendDirection
    growth_rate: float
    user_count: int
    top_endpoints: List[str]


@dataclass
class CostAnalysis:
    """Cost analysis data."""
    total_cost: float
    cost_per_token: float
    cost_per_user: float
    cost_trend: TrendDirection
    projected_cost: float
    budget_utilization: float
    cost_breakdown: Dict[str, float]


@dataclass
class ForecastData:
    """Forecasting data."""
    forecast_period: datetime
    predicted_usage: int
    confidence_interval: tuple
    factors: List[str]
    accuracy_score: float


@dataclass
class Recommendation:
    """System recommendation."""
    id: str
    type: str
    priority: str
    description: str
    impact: str
    estimated_savings: Optional[float] = None
    implementation_effort: str = "low"


@dataclass
class AnalyticsReport:
    """Comprehensive analytics report."""
    report_id: str
    title: str
    generated_at: datetime
    time_period: Dict[str, datetime]
    summary: Dict[str, Any]
    usage_trends: List[UsageTrend]
    format: ReportFormat
    recommendations: List[Recommendation]
    cost_analysis: Optional[CostAnalysis] = None
    forecast_data: Optional[ForecastData] = None
    metadata: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class TokenAnalytics:
    """
    Comprehensive token analytics and reporting system.
    
    Provides usage trend analysis, cost analysis, forecasting,
    and intelligent recommendations for token optimization.
    """
    
    def __init__(self, db: Optional[PostgresDB] = None):
        """
        Initialize the analytics system.
        
        Args:
            db: Database instance for data retrieval
        """
        self.db = db or PostgresDB()
        self.monitoring = TokenMonitoringSystem(db)
        
        # Analytics configuration
        self.config = {
            'default_forecast_days': 30,
            'cost_per_token': 0.000002,  # $0.002 per 1K tokens
            'budget_threshold': 0.8,  # 80% budget utilization triggers alerts
            'min_data_points': 10,  # Minimum data points for trend analysis
            'confidence_level': 0.95,  # 95% confidence interval
            'enable_recommendations': True,
            'recommendation_threshold': 0.1  # 10% improvement threshold
        }
        
        # Performance metrics
        self.metrics = {
            'total_reports_generated': 0,
            'forecast_accuracy': 0.0,
            'recommendations_generated': 0,
            'last_error': None,
            'error_timestamp': None
        }
        
        logger.info("TokenAnalytics initialized")
    
    def generate_usage_report(self, user_id: Optional[str] = None, 
                             days: int = 7, format: ReportFormat = ReportFormat.JSON) -> AnalyticsReport:
        """
        Generate comprehensive usage report.
        
        Args:
            user_id: Specific user to report on (optional)
            days: Number of days to include in report
            format: Output format for the report
            
        Returns:
            AnalyticsReport with comprehensive usage data
        """
        try:
            start_date = datetime.utcnow() - timedelta(days=days)
            end_date = datetime.utcnow()
            
            # Get usage data
            usage_data = self._get_usage_data(user_id, start_date, end_date)
            
            # Calculate trends
            usage_trends = self._calculate_usage_trends(usage_data)
            
            # Generate summary
            summary = self._generate_summary(usage_data, usage_trends)
            
            # Perform cost analysis
            cost_analysis = self._analyze_costs(usage_data)
            
            # Generate forecast
            forecast_data = self._generate_forecast(usage_data)
            
            # Generate recommendations
            recommendations = []
            if self.config['enable_recommendations']:
                recommendations = self._generate_recommendations(usage_data, cost_analysis)
            
            # Create report
            report = AnalyticsReport(
                report_id=f"report_{int(datetime.now().timestamp())}",
                title=f"Token Usage Report{' for ' + user_id if user_id else ''}",
                generated_at=datetime.utcnow(),
                time_period={'start': start_date, 'end': end_date},
                summary=summary,
                usage_trends=usage_trends,
                cost_analysis=cost_analysis,
                forecast_data=forecast_data,
                recommendations=recommendations,
                format=format
            )
            
            self.metrics['total_reports_generated'] += 1
            
            logger.info(f"Generated usage report: {report.report_id}")
            return report
            
        except Exception as e:
            logger.error(f"Error generating usage report: {e}")
            self.metrics['last_error'] = str(e)
            self.metrics['error_timestamp'] = datetime.utcnow().isoformat()
            raise
    
    def _get_usage_data(self, user_id: Optional[str], start_date: datetime, end_date: datetime) -> pd.DataFrame:
        """Retrieve usage data from database."""
        try:
            # Get token usage records
            usage_records = self.db.get_user_token_usage(
                user_id=user_id,
                start_date=start_date,
                end_date=end_date,
                user_id=user_id if user_id else "default"
            )
            
            if not usage_records:
                # Return empty DataFrame with expected columns
                return pd.DataFrame(columns=[
                    'user_id', 'session_id', 'tokens_used', 'api_endpoint', 
                    'priority_level', 'timestamp'
                ])
            
            # Convert to DataFrame
            df = pd.DataFrame(usage_records)
            
            # Convert timestamp to datetime
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            
            return df
            
        except Exception as e:
            logger.error(f"Error retrieving usage data: {e}")
            raise
    
    def _calculate_usage_trends(self, usage_data: pd.DataFrame) -> List[UsageTrend]:
        """Calculate usage trends from data."""
        try:
            if usage_data.empty:
                return []
            
            trends = []
            
            # Group by different time granularities
            for granularity in [TimeGranularity.DAILY, TimeGranularity.WEEKLY]:
                if granularity == TimeGranularity.DAILY:
                    grouped = usage_data.groupby(pd.Grouper(key='timestamp', freq='D'))
                else:
                    grouped = usage_data.groupby(pd.Grouper(key='timestamp', freq='W'))
                
                for period_start, group in grouped:
                    period_end = (period_start[0] + timedelta(days=1)) if granularity == TimeGranularity.DAILY else (period_start[0] + timedelta(weeks=1))
                    
                    total_tokens = group['tokens_used'].sum()
                    total_requests = len(group)
                    average_tokens = total_tokens / total_requests if total_requests > 0 else 0
                    
                    # Calculate trend
                    trend_direction = self._calculate_trend_direction(group)
                    growth_rate = self._calculate_growth_rate(group)
                    
                    # Get top endpoints
                    top_endpoints = group['api_endpoint'].value_counts().head(3).index.tolist()
                    
                    # Get unique user count
                    user_count = group['user_id'].nunique() if 'user_id' in group.columns else 1
                    
                    trend = UsageTrend(
                        period_start=period_start[0] if isinstance(period_start, tuple) else period_start,
                        period_end=period_end,
                        total_tokens=total_tokens,
                        average_tokens_per_request=average_tokens,
                        trend_direction=trend_direction,
                        growth_rate=growth_rate,
                        user_count=user_count,
                        top_endpoints=top_endpoints
                    )
                    
                    trends.append(trend)
            
            return trends
            
        except Exception as e:
            logger.error(f"Error calculating usage trends: {e}")
            return []
    
    def _calculate_trend_direction(self, data: pd.DataFrame) -> TrendDirection:
        """Calculate trend direction from data."""
        try:
            if len(data) < 2:
                return TrendDirection.STABLE
            
            # Simple trend calculation based on token usage
            tokens = data['tokens_used'].values
            if len(tokens) < 2:
                return TrendDirection.STABLE
            
            # Calculate slope
            x = np.arange(len(tokens))
            slope = np.polyfit(x, tokens.astype(float), 1)[0]
            
            # Determine trend direction
            if abs(slope) < 0.1:
                return TrendDirection.STABLE
            elif slope > 0:
                return TrendDirection.INCREASING
            else:
                return TrendDirection.DECREASING
                
        except Exception as e:
            logger.error(f"Error calculating trend direction: {e}")
            return TrendDirection.STABLE
    
    def _calculate_growth_rate(self, data: pd.DataFrame) -> float:
        """Calculate growth rate from data."""
        try:
            if len(data) < 2:
                return 0.0
            
            # Calculate growth rate as percentage change
            tokens = data['tokens_used'].values
            if len(tokens) >= 2:
                growth_rate = (tokens[-1] - tokens[0]) / tokens[0] * 100
                return round(growth_rate, 2)
            
            return 0.0
            
        except Exception as e:
            logger.error(f"Error calculating growth rate: {e}")
            return 0.0
    
    def _generate_summary(self, usage_data: pd.DataFrame, usage_trends: List[UsageTrend]) -> Dict[str, Any]:
        """Generate summary statistics from usage data."""
        try:
            if usage_data.empty:
                return {
                    'total_tokens': 0,
                    'total_requests': 0,
                    'average_tokens_per_request': 0,
                    'unique_users': 0,
                    'unique_endpoints': 0,
                    'period_days': 0
                }
            
            summary = {
                'total_tokens': int(usage_data['tokens_used'].sum()),
                'total_requests': len(usage_data),
                'average_tokens_per_request': round(usage_data['tokens_used'].mean(), 2),
                'unique_users': usage_data['user_id'].nunique() if 'user_id' in usage_data.columns else 1,
                'unique_endpoints': usage_data['api_endpoint'].nunique(),
                'period_days': (usage_data['timestamp'].max() - usage_data['timestamp'].min()).days + 1
            }
            
            # Add trend summary
            if usage_trends:
                summary['trend_summary'] = {
                    'overall_direction': usage_trends[-1].trend_direction.value if usage_trends else 'stable',
                    'average_growth_rate': round(np.mean([t.growth_rate for t in usage_trends]), 2),
                    'peak_usage_period': usage_trends[-1].period_end.strftime('%Y-%m-%d') if usage_trends else 'N/A'
                }
            
            return summary
            
        except Exception as e:
            logger.error(f"Error generating summary: {e}")
            return {}
    
    def _analyze_costs(self, usage_data: pd.DataFrame) -> Optional[CostAnalysis]:
        """Analyze costs from usage data."""
        try:
            if usage_data.empty:
                return None
            
            total_tokens = usage_data['tokens_used'].sum()
            total_cost = total_tokens * self.config['cost_per_token']
            
            # Calculate cost per user
            unique_users = usage_data['user_id'].nunique() if 'user_id' in usage_data.columns else 1
            cost_per_user = total_cost / unique_users
            
            # Calculate cost trend
            cost_trend = self._calculate_trend_direction(usage_data)
            
            # Project future costs
            projected_cost = total_cost * 1.1  # Simple 10% projection
            
            # Cost breakdown by endpoint
            cost_breakdown = {}
            for endpoint in usage_data['api_endpoint'].unique():
                endpoint_tokens = usage_data[usage_data['api_endpoint'] == endpoint]['tokens_used'].sum()
                cost_breakdown[endpoint] = endpoint_tokens * self.config['cost_per_token']
            
            return CostAnalysis(
                total_cost=round(total_cost, 4),
                cost_per_token=self.config['cost_per_token'],
                cost_per_user=round(cost_per_user, 4),
                cost_trend=cost_trend,
                projected_cost=round(projected_cost, 4),
                budget_utilization=min(1.0, total_cost / (unique_users * 100)),  # Assuming $100 budget per user
                cost_breakdown=cost_breakdown
            )
            
        except Exception as e:
            logger.error(f"Error analyzing costs: {e}")
            return None
    
    def _generate_forecast(self, usage_data: pd.DataFrame) -> Optional[ForecastData]:
        """Generate usage forecast."""
        try:
            if usage_data.empty or len(usage_data) < self.config['min_data_points']:
                return None
            
            # Simple linear regression forecast
            tokens = usage_data['tokens_used'].values
            x = np.arange(len(tokens))
            
            # Fit linear model
            slope, intercept = np.polyfit(x, tokens.astype(float), 1)
            
            # Forecast next period
            forecast_period = usage_data['timestamp'].max() + timedelta(days=self.config['default_forecast_days'])
            predicted_usage = slope * len(tokens) + intercept
            
            # Calculate confidence interval (simplified)
            residuals = tokens - (slope * x + intercept)
            mse = np.mean(residuals**2)
            std_error = np.sqrt(mse)
            
            confidence_interval = (
                predicted_usage - 1.96 * std_error,
                predicted_usage + 1.96 * std_error
            )
            
            # Determine factors affecting forecast
            factors = []
            if slope > 0:
                factors.append("Increasing usage trend")
            if std_error > np.mean(tokens.astype(float)) * 0.2:
                factors.append("High volatility in usage")
            if len(usage_data['api_endpoint'].unique()) > 5:
                factors.append("Multiple API endpoints in use")
            
            # Calculate accuracy score (simplified)
            accuracy_score = max(0, 1 - std_error / np.mean(tokens.astype(float)))
            
            return ForecastData(
                forecast_period=forecast_period,
                predicted_usage=int(predicted_usage),
                confidence_interval=confidence_interval,
                factors=factors,
                accuracy_score=round(accuracy_score, 3)
            )
            
        except Exception as e:
            logger.error(f"Error generating forecast: {e}")
            return None
    
    def _generate_recommendations(self, usage_data: pd.DataFrame, cost_analysis: Optional[CostAnalysis]) -> List[Recommendation]:
        """Generate optimization recommendations."""
        try:
            recommendations = []
            
            if usage_data.empty:
                return recommendations
            
            # Check for high usage patterns
            avg_tokens = usage_data['tokens_used'].mean()
            if avg_tokens > 1000:  # High usage threshold
                recommendations.append(Recommendation(
                    id="high_usage_optimization",
                    type="optimization",
                    priority="high",
                    description=f"High average token usage detected ({avg_tokens:.0f} tokens/request). Consider implementing caching or optimizing prompts.",
                    impact="significant",
                    estimated_savings=avg_tokens * 0.1 * self.config['cost_per_token'] * len(usage_data),
                    implementation_effort="medium"
                ))
            
            # Check for API endpoint optimization
            endpoint_counts = usage_data['api_endpoint'].value_counts()
            if len(endpoint_counts) > 10:  # Too many endpoints
                recommendations.append(Recommendation(
                    id="endpoint_consolidation",
                    type="optimization",
                    priority="medium",
                    description=f"High number of API endpoints ({len(endpoint_counts)}) detected. Consider consolidating similar endpoints.",
                    impact="moderate",
                    estimated_savings=len(endpoint_counts) * 50 * self.config['cost_per_token'],
                    implementation_effort="high"
                ))
            
            # Check for cost optimization
            if cost_analysis and cost_analysis.total_cost > 100:  # High cost threshold
                recommendations.append(Recommendation(
                    id="cost_optimization",
                    type="cost_reduction",
                    priority="high",
                    description=f"High token costs detected (${cost_analysis.total_cost:.4f}). Consider implementing usage quotas or cost monitoring.",
                    impact="significant",
                    estimated_savings=cost_analysis.total_cost * 0.2,
                    implementation_effort="low"
                ))
            
            # Check for user behavior patterns
            user_counts = usage_data['user_id'].value_counts()
            if len(user_counts) > 0:
                top_user_usage = user_counts.iloc[0] / len(usage_data)
                if top_user_usage > 0.5:  # One user dominates usage
                    recommendations.append(Recommendation(
                        id="user_balancing",
                        type="optimization",
                        priority="medium",
                        description=f"Single user accounts for {top_user_usage:.1%} of usage. Consider implementing user-specific quotas.",
                        impact="moderate",
                        estimated_savings=top_user_usage * 0.1 * cost_analysis.total_cost if cost_analysis else 0,
                        implementation_effort="medium"
                    ))
            
            self.metrics['recommendations_generated'] += len(recommendations)
            
            return sorted(recommendations, key=lambda x: (x.priority, x.estimated_savings or 0), reverse=True)
            
        except Exception as e:
            logger.error(f"Error generating recommendations: {e}")
            return []
    
    def export_metrics(self, format: ReportFormat = ReportFormat.JSON) -> Dict[str, Any]:
        """Export analytics metrics for external monitoring."""
        try:
            metrics = {
                'timestamp': datetime.utcnow().isoformat(),
                'system_metrics': self.monitoring.get_performance_metrics(),
                'analytics_metrics': self.metrics,
                'config': self.config
            }
            
            if format == ReportFormat.JSON:
                return metrics
            else:
                # Convert to other formats if needed
                return metrics
                
        except Exception as e:
            logger.error(f"Error exporting metrics: {e}")
            return {}
    
    def get_analytics_metrics(self) -> Dict[str, Any]:
        """Get analytics system metrics."""
        return self.metrics.copy()
    
    def generate_visualization(self, report: AnalyticsReport, chart_type: str = "usage_trends") -> str:
        """Generate visualization charts."""
        try:
            plt.figure(figsize=(12, 8))
            
            if chart_type == "usage_trends" and report.usage_trends:
                # Usage trends chart
                dates = [t.period_start for t in report.usage_trends]
                tokens = [t.total_tokens for t in report.usage_trends]
                
                plt.plot(dates, tokens, marker='o', linewidth=2, markersize=6)
                plt.title('Token Usage Trends')
                plt.xlabel('Date')
                plt.ylabel('Total Tokens')
                plt.xticks(rotation=45)
                plt.grid(True, alpha=0.3)
                
            elif chart_type == "cost_breakdown" and report.cost_analysis:
                # Cost breakdown chart
                costs = list(report.cost_analysis.cost_breakdown.values())
                endpoints = list(report.cost_analysis.cost_breakdown.keys())
                
                plt.pie(costs, labels=endpoints, autopct='%1.1f%%', startangle=90)
                plt.title('Cost Breakdown by Endpoint')
                
            elif chart_type == "forecast" and report.forecast_data:
                # Forecast chart
                dates = [datetime.utcnow() + timedelta(days=i) for i in range(30)]
                predicted = [report.forecast_data.predicted_usage] * 30
                confidence_lower = [report.forecast_data.confidence_interval[0]] * 30
                confidence_upper = [report.forecast_data.confidence_interval[1]] * 30
                
                plt.fill_between(dates, [confidence_lower]*len(dates), [confidence_upper]*len(dates), alpha=0.3, color='blue', label='Confidence Interval')
                plt.plot(dates, predicted, 'r-', linewidth=2, label='Predicted Usage')
                plt.title('Usage Forecast')
                plt.xlabel('Date')
                plt.ylabel('Tokens')
                plt.legend()
            
            plt.tight_layout()
            
            # Convert to base64 string
            buffer = io.BytesIO()
            plt.savefig(buffer, format='png', dpi=150, bbox_inches='tight')
            buffer.seek(0)
            chart_data = base64.b64encode(buffer.getvalue()).decode()
            plt.close()
            
            return chart_data
            
        except Exception as e:
            logger.error(f"Error generating visualization: {e}")
            return ""


# Convenience functions
def get_analytics_system(db: Optional[PostgresDB] = None) -> TokenAnalytics:
    """Get a global analytics system instance."""
    return TokenAnalytics(db)


def generate_usage_report(user_id: Optional[str] = None, days: int = 7,
                         db: Optional[PostgresDB] = None) -> Dict[str, Any]:
    """
    Convenience function to generate usage report.
    
    Args:
        user_id: Specific user to report on (optional)
        days: Number of days to include in report
        db: Database instance (optional)
        
    Returns:
        Dictionary with usage report data
    """
    analytics = TokenAnalytics(db)
    report = analytics.generate_usage_report(user_id, days)
    return asdict(report)