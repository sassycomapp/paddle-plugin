"""
Token Usage Analytics and Reporting

This module provides comprehensive analytics and reporting functionality for token usage data,
including historical analysis, trend detection, and export capabilities.
"""

import logging
import json
import csv
import io
import gzip
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Union, Callable
from dataclasses import dataclass, asdict
from enum import Enum
import pandas as pd
import numpy as np
from collections import defaultdict, Counter
import statistics
import hashlib

from simba.simba.database.postgres import PostgresDB
from simba.simba.database.token_models import TokenUsage
from src.token_usage_logger import TokenUsageRecord, LoggingConfig

logger = logging.getLogger(__name__)


class AnalyticsGranularity(Enum):
    """Granularity levels for analytics."""
    MINUTE = "minute"
    HOUR = "hour"
    DAY = "day"
    WEEK = "week"
    MONTH = "month"
    YEAR = "year"


class ExportFormat(Enum):
    """Export formats for analytics data."""
    JSON = "json"
    CSV = "csv"
    EXCEL = "excel"
    PARQUET = "parquet"
    HTML = "html"


@dataclass
class UsageSummary:
    """Summary of token usage statistics."""
    total_tokens: int
    total_requests: int
    average_tokens_per_request: float
    min_tokens_per_request: int
    max_tokens_per_request: int
    median_tokens_per_request: float
    std_dev_tokens_per_request: float
    unique_users: int
    unique_sessions: int
    unique_endpoints: int
    time_period: Dict[str, datetime]
    top_users: List[Dict[str, Any]]
    top_endpoints: List[Dict[str, Any]]
    priority_distribution: Dict[str, int]


@dataclass
class TrendAnalysis:
    """Trend analysis results."""
    period_start: datetime
    period_end: datetime
    trend_direction: str  # 'increasing', 'decreasing', 'stable'
    trend_strength: float  # 0.0 to 1.0
    growth_rate: float  # percentage change
    seasonal_patterns: Dict[str, float]
    anomalies: List[Dict[str, Any]]
    forecast: Optional[Dict[str, Any]] = None


@dataclass
class AnalyticsConfig:
    """Configuration for analytics operations."""
    default_granularity: AnalyticsGranularity = AnalyticsGranularity.DAY
    default_time_range: int = 30  # days
    max_records: int = 1000000
    enable_trend_analysis: bool = True
    enable_anomaly_detection: bool = True
    enable_forecasting: bool = False
    forecast_periods: int = 7
    anomaly_threshold: float = 2.0  # standard deviations
    cache_results: bool = True
    cache_ttl: int = 3600  # seconds


class TokenUsageAnalytics:
    """
    Comprehensive analytics and reporting for token usage data.
    
    Features:
    - Historical usage analysis with configurable granularity
    - Trend detection and forecasting
    - Anomaly detection
    - User and endpoint analytics
    - Export capabilities in multiple formats
    - Performance optimization with caching
    """
    
    def __init__(self, db: Optional[PostgresDB] = None, config: Optional[AnalyticsConfig] = None):
        """
        Initialize the analytics system.
        
        Args:
            db: Database instance for analytics operations
            config: Analytics configuration
        """
        self.db = db or PostgresDB()
        self.config = config or AnalyticsConfig()
        
        # Cache for analytics results
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._cache_ttl = {}
        
        logger.info(f"TokenUsageAnalytics initialized with {self.config.default_granularity.value} granularity")
    
    def _generate_cache_key(self, operation: str, **kwargs) -> str:
        """Generate a cache key for the given operation and parameters."""
        key_data = {
            'operation': operation,
            'params': kwargs,
            'timestamp': datetime.utcnow().isoformat()
        }
        return hashlib.md5(json.dumps(key_data, sort_keys=True).encode()).hexdigest()
    
    def _get_from_cache(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """Get analytics result from cache if available and not expired."""
        if cache_key not in self._cache:
            return None
        
        # Check TTL
        if cache_key in self._cache_ttl:
            if datetime.utcnow() > self._cache_ttl[cache_key]:
                del self._cache[cache_key]
                del self._cache_ttl[cache_key]
                return None
        
        return self._cache[cache_key]
    
    def _add_to_cache(self, cache_key: str, result: Dict[str, Any], ttl: Optional[int] = None):
        """Add analytics result to cache."""
        if not self.config.cache_results:
            return
        
        self._cache[cache_key] = result
        
        # Set TTL
        ttl = ttl or self.config.cache_ttl
        self._cache_ttl[cache_key] = datetime.utcnow() + timedelta(seconds=ttl)
        
        # Simple cache cleanup - remove expired entries
        current_time = datetime.utcnow()
        expired_keys = [
            key for key, expiry in self._cache_ttl.items()
            if current_time > expiry
        ]
        for key in expired_keys:
            del self._cache[key]
            del self._cache_ttl[key]
    
    def get_token_usage_history(self, user_id: Optional[str] = None,
                               start_date: Optional[datetime] = None,
                               end_date: Optional[datetime] = None,
                               granularity: Optional[AnalyticsGranularity] = None,
                               limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Get historical token usage data with configurable granularity.
        
        Args:
            user_id: Filter by specific user (optional)
            start_date: Start date for the query (optional)
            end_date: End date for the query (optional)
            granularity: Time granularity for aggregation (optional)
            limit: Maximum number of records to return (optional)
            
        Returns:
            List of historical token usage records
        """
        granularity = granularity or self.config.default_granularity
        
        # Generate cache key
        cache_key = self._generate_cache_key(
            'get_token_usage_history',
            user_id=user_id,
            start_date=start_date,
            end_date=end_date,
            granularity=granularity.value,
            limit=limit
        )
        
        # Check cache
        cached_result = self._get_from_cache(cache_key)
        if cached_result:
            return cached_result['data']
        
        try:
            # Build query
            query = "SELECT * FROM token_usage WHERE 1=1"
            params = []
            
            if user_id:
                query += " AND user_id = %s"
                params.append(user_id)
            
            if start_date:
                query += " AND timestamp >= %s"
                params.append(start_date)
            
            if end_date:
                query += " AND timestamp <= %s"
                params.append(end_date)
            
            query += " ORDER BY timestamp DESC"
            
            if limit:
                query += " LIMIT %s"
                params.append(limit)
            
            # Execute query
            results = self.db.fetch_all(query, params)
            
            # Apply time aggregation if needed
            if granularity != AnalyticsGranularity.MINUTE:
                results = self._aggregate_by_time(results, granularity)
            
            # Cache result
            self._add_to_cache(cache_key, {'data': results})
            
            return results
            
        except Exception as e:
            logger.error(f"Failed to get token usage history: {e}")
            return []
    
    def _aggregate_by_time(self, records: List[Dict[str, Any]], 
                          granularity: AnalyticsGranularity) -> List[Dict[str, Any]]:
        """Aggregate records by time period."""
        if not records:
            return []
        
        # Group by time period
        grouped = defaultdict(list)
        
        for record in records:
            timestamp = record['timestamp']
            
            if granularity == AnalyticsGranularity.HOUR:
                period_key = timestamp.replace(minute=0, second=0, microsecond=0)
            elif granularity == AnalyticsGranularity.DAY:
                period_key = timestamp.replace(hour=0, minute=0, second=0, microsecond=0)
            elif granularity == AnalyticsGranularity.WEEK:
                # Start of week (Monday)
                days_since_monday = timestamp.weekday()
                period_key = timestamp - timedelta(days=days_since_monday)
                period_key = period_key.replace(hour=0, minute=0, second=0, microsecond=0)
            elif granularity == AnalyticsGranularity.MONTH:
                period_key = timestamp.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            elif granularity == AnalyticsGranularity.YEAR:
                period_key = timestamp.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
            else:  # MINUTE
                period_key = timestamp
            
            grouped[period_key].append(record)
        
        # Aggregate each period
        aggregated = []
        for period_key, period_records in grouped.items():
            total_tokens = sum(r['tokens_used'] for r in period_records)
            total_requests = len(period_records)
            
            aggregated.append({
                'period_start': period_key.isoformat(),
                'period_end': (period_key + self._get_period_duration(granularity)).isoformat(),
                'total_tokens': total_tokens,
                'total_requests': total_requests,
                'average_tokens_per_request': total_tokens / total_requests if total_requests > 0 else 0,
                'unique_users': len(set(r['user_id'] for r in period_records)),
                'unique_sessions': len(set(r['session_id'] for r in period_records)),
                'unique_endpoints': len(set(r['api_endpoint'] for r in period_records)),
                'records': period_records
            })
        
        return aggregated
    
    def _get_period_duration(self, granularity: AnalyticsGranularity) -> timedelta:
        """Get the duration for a time period."""
        if granularity == AnalyticsGranularity.MINUTE:
            return timedelta(minutes=1)
        elif granularity == AnalyticsGranularity.HOUR:
            return timedelta(hours=1)
        elif granularity == AnalyticsGranularity.DAY:
            return timedelta(days=1)
        elif granularity == AnalyticsGranularity.WEEK:
            return timedelta(weeks=1)
        elif granularity == AnalyticsGranularity.MONTH:
            return timedelta(days=30)  # Approximation
        elif granularity == AnalyticsGranularity.YEAR:
            return timedelta(days=365)  # Approximation
        else:
            return timedelta(days=1)
    
    def get_token_usage_summary(self, user_id: Optional[str] = None,
                               start_date: Optional[datetime] = None,
                               end_date: Optional[datetime] = None) -> UsageSummary:
        """
        Generate comprehensive usage summary statistics.
        
        Args:
            user_id: Filter by specific user (optional)
            start_date: Start date for the query (optional)
            end_date: End date for the query (optional)
            
        Returns:
            UsageSummary with comprehensive statistics
        """
        # Generate cache key
        cache_key = self._generate_cache_key(
            'get_token_usage_summary',
            user_id=user_id,
            start_date=start_date,
            end_date=end_date
        )
        
        # Check cache
        cached_result = self._get_from_cache(cache_key)
        if cached_result:
            return UsageSummary(**cached_result['data'])
        
        try:
            # Get all records
            records = self.get_token_usage_history(
                user_id=user_id,
                start_date=start_date,
                end_date=end_date,
                granularity=AnalyticsGranularity.MINUTE
            )
            
            if not records:
                return UsageSummary(
                    total_tokens=0,
                    total_requests=0,
                    average_tokens_per_request=0,
                    min_tokens_per_request=0,
                    max_tokens_per_request=0,
                    median_tokens_per_request=0,
                    std_dev_tokens_per_request=0,
                    unique_users=0,
                    unique_sessions=0,
                    unique_endpoints=0,
                    time_period={'start': None, 'end': None},
                    top_users=[],
                    top_endpoints=[],
                    priority_distribution={}
                )
            
            # Calculate basic statistics
            tokens_used = [r['tokens_used'] for r in records]
            total_tokens = sum(tokens_used)
            total_requests = len(records)
            average_tokens = total_tokens / total_requests if total_requests > 0 else 0
            min_tokens = min(tokens_used) if tokens_used else 0
            max_tokens = max(tokens_used) if tokens_used else 0
            median_tokens = statistics.median(tokens_used) if tokens_used else 0
            std_dev_tokens = statistics.stdev(tokens_used) if len(tokens_used) > 1 else 0
            
            # Calculate unique values
            unique_users = len(set(r['user_id'] for r in records))
            unique_sessions = len(set(r['session_id'] for r in records))
            unique_endpoints = len(set(r['api_endpoint'] for r in records))
            
            # Get time period
            timestamps = [r['timestamp'] for r in records]
            time_period = {
                'start': min(timestamps),
                'end': max(timestamps)
            }
            
            # Get top users
            user_counts = Counter(r['user_id'] for r in records)
            top_users = [
                {'user_id': user, 'tokens': user_counts[user]}
                for user in user_counts.most_common(10)
            ]
            
            # Get top endpoints
            endpoint_counts = Counter(r['api_endpoint'] for r in records)
            top_endpoints = [
                {'endpoint': endpoint, 'tokens': endpoint_counts[endpoint]}
                for endpoint in endpoint_counts.most_common(10)
            ]
            
            # Get priority distribution
            priority_counts = Counter(r['priority_level'] for r in records)
            priority_distribution = dict(priority_counts)
            
            # Create summary
            summary = UsageSummary(
                total_tokens=total_tokens,
                total_requests=total_requests,
                average_tokens_per_request=average_tokens,
                min_tokens_per_request=min_tokens,
                max_tokens_per_request=max_tokens,
                median_tokens_per_request=median_tokens,
                std_dev_tokens_per_request=std_dev_tokens,
                unique_users=unique_users,
                unique_sessions=unique_sessions,
                unique_endpoints=unique_endpoints,
                time_period=time_period,
                top_users=top_users,
                top_endpoints=top_endpoints,
                priority_distribution=priority_distribution
            )
            
            # Cache result
            self._add_to_cache(cache_key, {'data': asdict(summary)})
            
            return summary
            
        except Exception as e:
            logger.error(f"Failed to get token usage summary: {e}")
            return UsageSummary(
                total_tokens=0,
                total_requests=0,
                average_tokens_per_request=0,
                min_tokens_per_request=0,
                max_tokens_per_request=0,
                median_tokens_per_request=0,
                std_dev_tokens_per_request=0,
                unique_users=0,
                unique_sessions=0,
                unique_endpoints=0,
                time_period={'start': None, 'end': None},
                top_users=[],
                top_endpoints=[],
                priority_distribution={}
            )
    
    def get_trend_analysis(self, user_id: Optional[str] = None,
                          start_date: Optional[datetime] = None,
                          end_date: Optional[datetime] = None,
                          granularity: Optional[AnalyticsGranularity] = None) -> TrendAnalysis:
        """
        Analyze trends in token usage data.
        
        Args:
            user_id: Filter by specific user (optional)
            start_date: Start date for the query (optional)
            end_date: End date for the query (optional)
            granularity: Time granularity for analysis (optional)
            
        Returns:
            TrendAnalysis with trend information
        """
        if not self.config.enable_trend_analysis:
            return TrendAnalysis(
                period_start=start_date or datetime.utcnow() - timedelta(days=self.config.default_time_range),
                period_end=end_date or datetime.utcnow(),
                trend_direction='stable',
                trend_strength=0.0,
                growth_rate=0.0,
                seasonal_patterns={},
                anomalies=[]
            )
        
        granularity = granularity or self.config.default_granularity
        
        # Get aggregated data
        records = self.get_token_usage_history(
            user_id=user_id,
            start_date=start_date,
            end_date=end_date,
            granularity=granularity
        )
        
        if len(records) < 2:
            return TrendAnalysis(
                period_start=records[0]['period_start'] if records else datetime.utcnow(),
                period_end=records[-1]['period_end'] if records else datetime.utcnow(),
                trend_direction='stable',
                trend_strength=0.0,
                growth_rate=0.0,
                seasonal_patterns={},
                anomalies=[]
            )
        
        # Extract time series data
        timestamps = [datetime.fromisoformat(r['period_start']) for r in records]
        token_values = [r['total_tokens'] for r in records]
        
        # Calculate trend using linear regression
        trend_direction, trend_strength, growth_rate = self._calculate_trend(timestamps, token_values)
        
        # Detect anomalies
        anomalies = self._detect_anomalies(token_values) if self.config.enable_anomaly_detection else []
        
        # Analyze seasonal patterns
        seasonal_patterns = self._analyze_seasonal_patterns(records)
        
        # Generate forecast if enabled
        forecast = None
        if self.config.enable_forecasting and len(records) >= 3:
            forecast = self._generate_forecast(records, self.config.forecast_periods)
        
        return TrendAnalysis(
            period_start=datetime.fromisoformat(records[0]['period_start']),
            period_end=datetime.fromisoformat(records[-1]['period_end']),
            trend_direction=trend_direction,
            trend_strength=trend_strength,
            growth_rate=growth_rate,
            seasonal_patterns=seasonal_patterns,
            anomalies=anomalies,
            forecast=forecast
        )
    
    def _calculate_trend(self, timestamps: List[datetime], values: List[float]) -> tuple:
        """Calculate trend direction, strength, and growth rate."""
        if len(values) < 2:
            return 'stable', 0.0, 0.0
        
        # Convert timestamps to numeric values for regression
        x = list(range(len(values)))
        y = values
        
        # Calculate linear regression
        n = len(x)
        sum_x = sum(x)
        sum_y = sum(y)
        sum_xy = sum(xi * yi for xi, yi in zip(x, y))
        sum_x2 = sum(xi * xi for xi in x)
        
        # Calculate slope (trend)
        slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x * sum_x)
        
        # Calculate correlation coefficient (strength)
        mean_x = sum_x / n
        mean_y = sum_y / n
        
        numerator = sum((xi - mean_x) * (yi - mean_y) for xi, yi in zip(x, y))
        denominator = (sum((xi - mean_x) ** 2 for xi in x) * sum((yi - mean_y) ** 2 for yi in y)) ** 0.5
        
        correlation = numerator / denominator if denominator != 0 else 0
        
        # Determine trend direction
        if abs(slope) < 0.01:  # Very small slope
            direction = 'stable'
        elif slope > 0:
            direction = 'increasing'
        else:
            direction = 'decreasing'
        
        # Calculate growth rate
        if values[0] != 0:
            growth_rate = ((values[-1] - values[0]) / values[0]) * 100
        else:
            growth_rate = 0.0
        
        return direction, abs(correlation), growth_rate
    
    def _detect_anomalies(self, values: List[float]) -> List[Dict[str, Any]]:
        """Detect anomalies in the data using statistical methods."""
        if len(values) < 3:
            return []
        
        # Calculate mean and standard deviation
        mean = statistics.mean(values)
        std_dev = statistics.stdev(values) if len(values) > 1 else 0
        
        if std_dev == 0:
            return []
        
        # Find anomalies (values beyond threshold standard deviations)
        anomalies = []
        threshold = self.config.anomaly_threshold
        
        for i, value in enumerate(values):
            z_score = abs((value - mean) / std_dev)
            if z_score > threshold:
                anomalies.append({
                    'index': i,
                    'value': value,
                    'z_score': z_score,
                    'severity': 'high' if z_score > threshold * 1.5 else 'medium'
                })
        
        return anomalies
    
    def _analyze_seasonal_patterns(self, records: List[Dict[str, Any]]) -> Dict[str, float]:
        """Analyze seasonal patterns in the data."""
        if len(records) < 7:  # Need at least a week of data
            return {}
        
        # Group by day of week
        day_of_week_counts = defaultdict(list)
        
        for record in records:
            timestamp = datetime.fromisoformat(record['period_start'])
            day_of_week = timestamp.weekday()  # Monday is 0, Sunday is 6
            day_of_week_counts[day_of_week].append(record['total_tokens'])
        
        # Calculate average for each day
        day_patterns = {}
        day_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        
        for day, tokens in day_of_week_counts.items():
            if tokens:
                day_patterns[day_names[day]] = statistics.mean(tokens)
        
        # Normalize to percentages
        if day_patterns:
            total_avg = statistics.mean(day_patterns.values())
            day_patterns = {
                day: (tokens / total_avg - 1) * 100
                for day, tokens in day_patterns.items()
            }
        
        return day_patterns
    
    def _generate_forecast(self, records: List[Dict[str, Any]], periods: int) -> Dict[str, Any]:
        """Generate forecast for future token usage."""
        if len(records) < 3:
            return {}
        
        # Simple moving average forecast
        values = [r['total_tokens'] for r in records]
        
        # Calculate moving averages
        window_size = min(3, len(values))
        moving_avg = sum(values[-window_size:]) / window_size
        
        # Simple trend adjustment
        if len(values) >= 2:
            trend = values[-1] - values[-2]
        else:
            trend = 0
        
        # Generate forecast
        forecast = []
        for i in range(periods):
            forecast_value = moving_avg + (trend * (i + 1))
            forecast.append({
                'period': i + 1,
                'forecast_tokens': max(0, forecast_value),
                'confidence': max(0, 1 - (i * 0.1))  # Decreasing confidence over time
            })
        
        return {
            'method': 'moving_average',
            'window_size': window_size,
            'forecast': forecast
        }
    
    def export_token_usage_logs(self, user_id: Optional[str] = None,
                               start_date: Optional[datetime] = None,
                               end_date: Optional[datetime] = None,
                               format: ExportFormat = ExportFormat.JSON,
                               compression: bool = False) -> Union[str, bytes]:
        """
        Export token usage logs in various formats.
        
        Args:
            user_id: Filter by specific user (optional)
            start_date: Start date for the query (optional)
            end_date: End date for the query (optional)
            format: Export format
            compression: Whether to compress the output
            
        Returns:
            Exported data as string or bytes
        """
        try:
            # Get records
            records = self.get_token_usage_history(
                user_id=user_id,
                start_date=start_date,
                end_date=end_date,
                granularity=AnalyticsGranularity.MINUTE
            )
            
            if not records:
                return ""
            
            # Convert to DataFrame for easier processing
            df = pd.DataFrame(records)
            
            # Export based on format
            if format == ExportFormat.JSON:
                output = df.to_json(orient='records', indent=2)
            elif format == ExportFormat.CSV:
                output = df.to_csv(index=False)
            elif format == ExportFormat.EXCEL:
                output = io.BytesIO()
                df.to_excel(output, index=False)
                output.seek(0)
                output = output.getvalue()
            elif format == ExportFormat.PARQUET:
                output = io.BytesIO()
                df.to_parquet(output, index=False)
                output.seek(0)
                output = output.getvalue()
            elif format == ExportFormat.HTML:
                output = df.to_html(index=False)
            else:
                raise ValueError(f"Unsupported export format: {format}")
            
            # Compress if requested
            if compression:
                if isinstance(output, str):
                    output_bytes = output.encode('utf-8')
                else:
                    output_bytes = output
                
                compressed = io.BytesIO()
                with gzip.GzipFile(fileobj=compressed, mode='wb') as f:
                    f.write(output_bytes)
                compressed.seek(0)
                output = compressed.getvalue()
            
            return output
            
        except Exception as e:
            logger.error(f"Failed to export token usage logs: {e}")
            return ""
    
    def cleanup_old_logs(self, retention_days: int = 90) -> Dict[str, Any]:
        """
        Clean up old token usage logs based on retention policy.
        
        Args:
            retention_days: Number of days to retain logs
            
        Returns:
            Dictionary with cleanup results
        """
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=retention_days)
            
            # Count records to be deleted
            count_query = """
                SELECT COUNT(*) as count 
                FROM token_usage 
                WHERE timestamp < %s
            """
            count_result = self.db.fetch_one(count_query, (cutoff_date,))
            records_to_delete = count_result['count'] if count_result else 0
            
            if records_to_delete == 0:
                return {
                    'success': True,
                    'records_deleted': 0,
                    'message': 'No old logs to delete'
                }
            
            # Delete old records
            delete_query = """
                DELETE FROM token_usage 
                WHERE timestamp < %s
            """
            deleted_count = self.db.execute_query(delete_query, (cutoff_date,))
            
            return {
                'success': True,
                'records_deleted': deleted_count,
                'message': f'Successfully deleted {deleted_count} old log records'
            }
            
        except Exception as e:
            logger.error(f"Failed to cleanup old logs: {e}")
            return {
                'success': False,
                'records_deleted': 0,
                'error': str(e)
            }
    
    def get_analytics_dashboard_data(self, user_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get comprehensive dashboard data for analytics.
        
        Args:
            user_id: Filter by specific user (optional)
            
        Returns:
            Dictionary with dashboard data
        """
        try:
            # Get time range (last 30 days)
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=self.config.default_time_range)
            
            # Get various analytics
            summary = self.get_token_usage_summary(
                user_id=user_id,
                start_date=start_date,
                end_date=end_date
            )
            
            trend_analysis = self.get_trend_analysis(
                user_id=user_id,
                start_date=start_date,
                end_date=end_date
            )
            
            # Get daily breakdown
            daily_usage = self.get_token_usage_history(
                user_id=user_id,
                start_date=start_date,
                end_date=end_date,
                granularity=AnalyticsGranularity.DAY
            )
            
            # Get hourly breakdown for today
            today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
            hourly_usage = self.get_token_usage_history(
                user_id=user_id,
                start_date=today_start,
                end_date=datetime.utcnow(),
                granularity=AnalyticsGranularity.HOUR
            )
            
            return {
                'summary': asdict(summary),
                'trend_analysis': asdict(trend_analysis),
                'daily_usage': daily_usage,
                'hourly_usage': hourly_usage,
                'generated_at': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to get dashboard data: {e}")
            return {
                'error': str(e),
                'generated_at': datetime.utcnow().isoformat()
            }
    
    def clear_cache(self):
        """Clear the analytics cache."""
        self._cache.clear()
        self._cache_ttl.clear()
        logger.info("Analytics cache cleared")


# Convenience functions for direct usage
def create_analytics_system(db: Optional[PostgresDB] = None,
                           config: Optional[AnalyticsConfig] = None) -> TokenUsageAnalytics:
    """
    Create an analytics system instance.
    
    Args:
        db: Database instance
        config: Analytics configuration
        
    Returns:
        TokenUsageAnalytics instance
    """
    return TokenUsageAnalytics(db, config)


def generate_usage_report(user_id: Optional[str] = None,
                         start_date: Optional[datetime] = None,
                         end_date: Optional[datetime] = None,
                         format: ExportFormat = ExportFormat.JSON,
                         db: Optional[PostgresDB] = None) -> Union[str, bytes]:
    """
    Convenience function to generate a usage report.
    
    Args:
        user_id: Filter by specific user (optional)
        start_date: Start date for the report (optional)
        end_date: End date for the report (optional)
        format: Export format
        db: Database instance
        
    Returns:
        Exported report data
    """
    analytics = TokenUsageAnalytics(db)
    return analytics.export_token_usage_logs(
        user_id=user_id,
        start_date=start_date,
        end_date=end_date,
        format=format
    )