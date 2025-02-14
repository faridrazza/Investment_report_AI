from pydantic import BaseModel
from typing import Dict, List, Optional
from datetime import datetime

class ClientInfo(BaseModel):
    id: str
    name: str
    account_type: str
    risk_profile: str
    investment_strategy: str
    relationship_manager: str
    account_open_date: str

class PortfolioSummary(BaseModel):
    total_value: float
    period_start: str
    period_end: str
    beginning_balance: float
    contributions: float
    withdrawals: float
    realized_gains: float
    unrealized_gains: float
    income_earned: float
    fees: float

class AssetAllocationItem(BaseModel):
    percentage: float
    value: float
    target: float
    variance: float

class AssetAllocation(BaseModel):
    equities: AssetAllocationItem
    fixed_income: AssetAllocationItem
    alternatives: AssetAllocationItem
    cash: AssetAllocationItem

class Performance(BaseModel):
    ytd: float
    one_year: float
    three_year: Optional[float]
    five_year: Optional[float]
    since_inception: float

class Holding(BaseModel):
    security: str
    name: str
    value: float
    weight: float
    gain: float

class Portfolio(BaseModel):
    client_info: ClientInfo
    portfolio_summary: PortfolioSummary
    asset_allocation: AssetAllocation
    performance: Performance
    top_holdings: List[Holding]
    last_updated: datetime = datetime.now() 
    