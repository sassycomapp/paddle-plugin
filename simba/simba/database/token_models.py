"""
SQLAlchemy models for token management system.

This module defines the database models for tracking token usage,
enforcing quotas, and managing token revocations.
"""
from sqlalchemy import Column, Integer, String, DateTime, Interval, CheckConstraint, Index, func
from sqlalchemy.dialects.postgresql import TEXT
from sqlalchemy.orm import relationship
from simba.simba.database.postgres import Base


class TokenUsage(Base):
    """SQLAlchemy model for token_usage table.
    
    Logs tokens consumed per request with user and session context.
    """
    __tablename__ = "token_usage"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(String, nullable=False, index=True)
    session_id = Column(String, nullable=False, index=True)
    tokens_used = Column(Integer, nullable=False)
    api_endpoint = Column(String, nullable=False)
    priority_level = Column(String, nullable=False)
    __table_args__ = (
        CheckConstraint("priority_level IN ('Low', 'Medium', 'High')"),
    )
    timestamp = Column(DateTime, nullable=False, server_default=func.now(), index=True)
    
    # Add relationship to user if user model exists
    # user = relationship("User", back_populates="token_usage")
    
    def __repr__(self):
        return (f"<TokenUsage(id={self.id}, user_id='{self.user_id}', "
                f"tokens_used={self.tokens_used}, timestamp='{self.timestamp}')>")


class TokenLimits(Base):
    """SQLAlchemy model for token_limits table.
    
    Store per-user or per-API token quota and limits.
    """
    __tablename__ = "token_limits"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(String, nullable=False, index=True)
    max_tokens_per_period = Column(Integer, nullable=False)
    period_interval = Column(Interval, nullable=False, default='1 day')
    tokens_used_in_period = Column(Integer, nullable=False, default=0)
    period_start = Column(DateTime, nullable=False, server_default=func.now(), index=True)
    
    # Add relationship to user if user model exists
    # user = relationship("User", back_populates="token_limits")
    
    def __repr__(self):
        return (f"<TokenLimits(id={self.id}, user_id='{self.user_id}', "
                f"max_tokens={self.max_tokens_per_period}, "
                f"used={self.tokens_used_in_period}, period_start='{self.period_start}')>")


class TokenRevocations(Base):
    """SQLAlchemy model for token_revocations table.
    
    Optional table for revoked tokens if applicable.
    """
    __tablename__ = "token_revocations"
    
    token = Column(String, primary_key=True)
    revoked_at = Column(DateTime, nullable=False, server_default=func.now(), index=True)
    reason = Column(String, nullable=True)
    
    def __repr__(self):
        return (f"<TokenRevocations(token='{self.token}', "
                f"revoked_at='{self.revoked_at}', reason='{self.reason}')>")


# Create indexes for performance optimization
Index('idx_token_usage_user_session', TokenUsage.user_id, TokenUsage.session_id)
Index('idx_token_usage_timestamp', TokenUsage.timestamp)
Index('idx_token_limits_user_period', TokenLimits.user_id, TokenLimits.period_start)
Index('idx_token_revocations_token', TokenRevocations.token)
Index('idx_token_revocations_revoked_at', TokenRevocations.revoked_at)