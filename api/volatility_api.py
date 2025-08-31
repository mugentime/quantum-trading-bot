#!/usr/bin/env python3
"""
VOLATILITY SCANNER API ENDPOINTS
RESTful API for accessing real-time volatility data, opportunities,
and scanner control functionality.
"""

from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Union
from datetime import datetime, timedelta
from enum import Enum
import json
import asyncio
import logging
from contextlib import asynccontextmanager

from core.volatility_scanner import AdvancedVolatilityScanner, VolatilityProfile, TradingOpportunity, VolatilityState, MarketCondition

logger = logging.getLogger(__name__)

# Global scanner instance
scanner: Optional[AdvancedVolatilityScanner] = None

# Pydantic models for API
class VolatilityStateEnum(str, Enum):
    DORMANT = "dormant"
    NORMAL = "normal"
    ELEVATED = "elevated"
    HIGH = "high"
    EXTREME = "extreme"
    BREAKOUT = "breakout"

class MarketConditionEnum(str, Enum):
    TRENDING_UP = "trending_up"
    TRENDING_DOWN = "trending_down"
    RANGING = "ranging"
    BREAKOUT = "breakout"
    EXHAUSTION = "exhaustion"
    ACCUMULATION = "accumulation"
    DISTRIBUTION = "distribution"

class VolatilityProfileResponse(BaseModel):
    symbol: str
    timestamp: datetime
    atr: float
    atr_percent: float
    vol_5min: float
    vol_1h: float
    vol_24h: float
    volume_24h: float
    volume_spike_ratio: float
    volatility_state: VolatilityStateEnum
    market_condition: MarketConditionEnum
    breakout_detected: bool
    volatility_score: float
    opportunity_score: float
    risk_score: float
    price_change_5min: float
    price_change_1h: float
    price_change_24h: float

class OpportunityResponse(BaseModel):
    symbol: str
    detected_at: datetime
    entry_signal: str
    confidence: float
    expected_move: float
    risk_reward_ratio: float
    priority: int
    expires_at: datetime
    volatility_profile: VolatilityProfileResponse
    metadata: Dict

class ScannerStatusResponse(BaseModel):
    running: bool
    scan_count: int
    last_scan: Optional[datetime]
    active_pairs: List[str]
    candidate_pairs: List[str]
    dormant_pairs: List[str]
    opportunities_found: int
    current_opportunities: int
    monitored_pairs: int
    avg_scan_time: float
    success_rate: float

class VolatilityRankingResponse(BaseModel):
    symbol: str
    volatility_score: float
    opportunity_score: float
    risk_score: float
    state: VolatilityStateEnum
    last_updated: datetime

class ScanRequest(BaseModel):
    pairs: Optional[List[str]] = None
    include_candidates: bool = True

class ConfigUpdateRequest(BaseModel):
    scan_interval: Optional[int] = None
    max_monitored_pairs: Optional[int] = None
    volatility_thresholds: Optional[Dict] = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan"""
    global scanner
    
    # Startup
    try:
        import os
        api_key = os.getenv('BINANCE_API_KEY')
        api_secret = os.getenv('BINANCE_SECRET_KEY')
        testnet = os.getenv('TRADING_MODE', 'testnet').lower() == 'testnet'
        
        if not api_key or not api_secret:
            logger.error("Missing Binance API credentials")
            yield
            return
        
        scanner = AdvancedVolatilityScanner(
            api_key=api_key,
            api_secret=api_secret,
            testnet=testnet,
            scan_interval=30,
            max_monitored_pairs=50
        )
        
        # Start scanner in background
        await scanner.start()
        logger.info("Volatility Scanner API started")
        yield
        
    except Exception as e:
        logger.error(f"Failed to start scanner: {e}")
        yield
    finally:
        # Shutdown
        if scanner:
            await scanner.stop()
        logger.info("Volatility Scanner API stopped")

# Create FastAPI app
app = FastAPI(
    title="Advanced Volatility Scanner API",
    description="Real-time volatility monitoring and trading opportunity detection",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dependency to get scanner
async def get_scanner():
    """Get scanner instance"""
    if not scanner:
        raise HTTPException(status_code=503, detail="Scanner not initialized")
    return scanner

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now(),
        "scanner_running": scanner.running if scanner else False
    }

# Scanner status endpoint
@app.get("/scanner/status", response_model=ScannerStatusResponse)
async def get_scanner_status(scanner: AdvancedVolatilityScanner = Depends(get_scanner)):
    """Get current scanner status and statistics"""
    try:
        status = scanner.get_scanner_status()
        return ScannerStatusResponse(
            running=status['running'],
            scan_count=status['scan_count'],
            last_scan=datetime.fromisoformat(status['last_scan']) if status['last_scan'] else None,
            active_pairs=status['active_pairs'],
            candidate_pairs=status['candidate_pairs'],
            dormant_pairs=status['dormant_pairs'],
            opportunities_found=status['opportunities_found'],
            current_opportunities=status['current_opportunities'],
            monitored_pairs=status['monitored_pairs'],
            avg_scan_time=status['performance']['avg_scan_time'],
            success_rate=status['performance']['success_rate']
        )
    except Exception as e:
        logger.error(f"Error getting scanner status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Volatility profiles endpoint
@app.get("/volatility/profiles", response_model=List[VolatilityProfileResponse])
async def get_volatility_profiles(
    limit: Optional[int] = 50,
    min_score: Optional[float] = 0,
    state: Optional[VolatilityStateEnum] = None,
    scanner: AdvancedVolatilityScanner = Depends(get_scanner)
):
    """Get volatility profiles for all monitored pairs"""
    try:
        profiles = []
        
        for symbol, profile in scanner.volatility_profiles.items():
            # Apply filters
            if profile.opportunity_score < min_score:
                continue
            
            if state and profile.volatility_state.value != state.value:
                continue
            
            profiles.append(VolatilityProfileResponse(
                symbol=profile.symbol,
                timestamp=profile.timestamp,
                atr=profile.atr,
                atr_percent=profile.atr_percent,
                vol_5min=profile.vol_5min,
                vol_1h=profile.vol_1h,
                vol_24h=profile.vol_24h,
                volume_24h=profile.volume_24h,
                volume_spike_ratio=profile.volume_spike_ratio,
                volatility_state=VolatilityStateEnum(profile.volatility_state.value),
                market_condition=MarketConditionEnum(profile.market_condition.value),
                breakout_detected=profile.breakout_detected,
                volatility_score=profile.volatility_score,
                opportunity_score=profile.opportunity_score,
                risk_score=profile.risk_score,
                price_change_5min=profile.price_change_5min,
                price_change_1h=profile.price_change_1h,
                price_change_24h=profile.price_change_24h
            ))
        
        # Sort by opportunity score
        profiles.sort(key=lambda x: x.opportunity_score, reverse=True)
        
        return profiles[:limit]
        
    except Exception as e:
        logger.error(f"Error getting volatility profiles: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Single pair volatility endpoint
@app.get("/volatility/profiles/{symbol}", response_model=VolatilityProfileResponse)
async def get_volatility_profile(
    symbol: str,
    scanner: AdvancedVolatilityScanner = Depends(get_scanner)
):
    """Get volatility profile for a specific pair"""
    try:
        if symbol not in scanner.volatility_profiles:
            raise HTTPException(status_code=404, detail=f"Profile not found for {symbol}")
        
        profile = scanner.volatility_profiles[symbol]
        
        return VolatilityProfileResponse(
            symbol=profile.symbol,
            timestamp=profile.timestamp,
            atr=profile.atr,
            atr_percent=profile.atr_percent,
            vol_5min=profile.vol_5min,
            vol_1h=profile.vol_1h,
            vol_24h=profile.vol_24h,
            volume_24h=profile.volume_24h,
            volume_spike_ratio=profile.volume_spike_ratio,
            volatility_state=VolatilityStateEnum(profile.volatility_state.value),
            market_condition=MarketConditionEnum(profile.market_condition.value),
            breakout_detected=profile.breakout_detected,
            volatility_score=profile.volatility_score,
            opportunity_score=profile.opportunity_score,
            risk_score=profile.risk_score,
            price_change_5min=profile.price_change_5min,
            price_change_1h=profile.price_change_1h,
            price_change_24h=profile.price_change_24h
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting profile for {symbol}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Trading opportunities endpoint
@app.get("/opportunities", response_model=List[OpportunityResponse])
async def get_trading_opportunities(
    limit: Optional[int] = 10,
    min_confidence: Optional[float] = 0.6,
    entry_signal: Optional[str] = None,
    scanner: AdvancedVolatilityScanner = Depends(get_scanner)
):
    """Get current trading opportunities"""
    try:
        opportunities = scanner.get_top_opportunities(limit=100)  # Get more for filtering
        
        # Filter opportunities
        filtered_opportunities = []
        for opp in opportunities:
            if opp.confidence < min_confidence:
                continue
            
            if entry_signal and opp.entry_signal != entry_signal:
                continue
            
            # Convert volatility profile
            vol_profile = VolatilityProfileResponse(
                symbol=opp.volatility_profile.symbol,
                timestamp=opp.volatility_profile.timestamp,
                atr=opp.volatility_profile.atr,
                atr_percent=opp.volatility_profile.atr_percent,
                vol_5min=opp.volatility_profile.vol_5min,
                vol_1h=opp.volatility_profile.vol_1h,
                vol_24h=opp.volatility_profile.vol_24h,
                volume_24h=opp.volatility_profile.volume_24h,
                volume_spike_ratio=opp.volatility_profile.volume_spike_ratio,
                volatility_state=VolatilityStateEnum(opp.volatility_profile.volatility_state.value),
                market_condition=MarketConditionEnum(opp.volatility_profile.market_condition.value),
                breakout_detected=opp.volatility_profile.breakout_detected,
                volatility_score=opp.volatility_profile.volatility_score,
                opportunity_score=opp.volatility_profile.opportunity_score,
                risk_score=opp.volatility_profile.risk_score,
                price_change_5min=opp.volatility_profile.price_change_5min,
                price_change_1h=opp.volatility_profile.price_change_1h,
                price_change_24h=opp.volatility_profile.price_change_24h
            )
            
            filtered_opportunities.append(OpportunityResponse(
                symbol=opp.symbol,
                detected_at=opp.detected_at,
                entry_signal=opp.entry_signal,
                confidence=opp.confidence,
                expected_move=opp.expected_move,
                risk_reward_ratio=opp.risk_reward_ratio,
                priority=opp.priority,
                expires_at=opp.expires_at,
                volatility_profile=vol_profile,
                metadata=opp.metadata
            ))
        
        return filtered_opportunities[:limit]
        
    except Exception as e:
        logger.error(f"Error getting opportunities: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Volatility rankings endpoint
@app.get("/volatility/rankings", response_model=List[VolatilityRankingResponse])
async def get_volatility_rankings(
    limit: Optional[int] = 20,
    scanner: AdvancedVolatilityScanner = Depends(get_scanner)
):
    """Get volatility rankings for all pairs"""
    try:
        rankings = []
        
        for symbol, profile in scanner.volatility_profiles.items():
            rankings.append(VolatilityRankingResponse(
                symbol=symbol,
                volatility_score=profile.volatility_score,
                opportunity_score=profile.opportunity_score,
                risk_score=profile.risk_score,
                state=VolatilityStateEnum(profile.volatility_state.value),
                last_updated=profile.timestamp
            ))
        
        # Sort by volatility score
        rankings.sort(key=lambda x: x.volatility_score, reverse=True)
        
        return rankings[:limit]
        
    except Exception as e:
        logger.error(f"Error getting rankings: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Breakout detection endpoint
@app.get("/volatility/breakouts")
async def get_volatility_breakouts(
    scanner: AdvancedVolatilityScanner = Depends(get_scanner)
):
    """Get pairs with detected volatility breakouts"""
    try:
        breakouts = []
        
        for symbol, profile in scanner.volatility_profiles.items():
            if profile.breakout_detected:
                breakouts.append({
                    'symbol': symbol,
                    'breakout_strength': profile.breakout_strength,
                    'volatility_state': profile.volatility_state.value,
                    'market_condition': profile.market_condition.value,
                    'opportunity_score': profile.opportunity_score,
                    'price_change_1h': profile.price_change_1h,
                    'volume_spike_ratio': profile.volume_spike_ratio,
                    'detected_at': profile.timestamp
                })
        
        # Sort by breakout strength
        breakouts.sort(key=lambda x: x['breakout_strength'], reverse=True)
        
        return {
            'breakouts': breakouts,
            'count': len(breakouts),
            'timestamp': datetime.now()
        }
        
    except Exception as e:
        logger.error(f"Error getting breakouts: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Manual scan trigger endpoint
@app.post("/scanner/scan")
async def trigger_manual_scan(
    request: ScanRequest,
    background_tasks: BackgroundTasks,
    scanner: AdvancedVolatilityScanner = Depends(get_scanner)
):
    """Trigger manual scan of pairs"""
    try:
        # Run scan in background
        background_tasks.add_task(scanner.scan_all_pairs)
        
        return {
            'status': 'scan_initiated',
            'message': 'Manual scan started in background',
            'timestamp': datetime.now()
        }
        
    except Exception as e:
        logger.error(f"Error triggering scan: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Configuration update endpoint
@app.put("/scanner/config")
async def update_scanner_config(
    request: ConfigUpdateRequest,
    scanner: AdvancedVolatilityScanner = Depends(get_scanner)
):
    """Update scanner configuration"""
    try:
        updated_fields = []
        
        if request.scan_interval is not None:
            scanner.scan_interval = request.scan_interval
            updated_fields.append('scan_interval')
        
        if request.max_monitored_pairs is not None:
            scanner.max_monitored_pairs = request.max_monitored_pairs
            updated_fields.append('max_monitored_pairs')
        
        if request.volatility_thresholds is not None:
            scanner.volatility_thresholds.update(request.volatility_thresholds)
            updated_fields.append('volatility_thresholds')
        
        return {
            'status': 'config_updated',
            'updated_fields': updated_fields,
            'timestamp': datetime.now()
        }
        
    except Exception as e:
        logger.error(f"Error updating config: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Export data endpoint
@app.get("/data/export")
async def export_volatility_data(
    format: str = "json",
    scanner: AdvancedVolatilityScanner = Depends(get_scanner)
):
    """Export volatility data"""
    try:
        if format.lower() != "json":
            raise HTTPException(status_code=400, detail="Only JSON format supported")
        
        # Create export data
        export_data = {
            'timestamp': datetime.now().isoformat(),
            'scanner_status': scanner.get_scanner_status(),
            'volatility_profiles': {
                symbol: profile.to_dict() 
                for symbol, profile in scanner.volatility_profiles.items()
            },
            'opportunities': [
                {
                    'symbol': opp.symbol,
                    'detected_at': opp.detected_at.isoformat(),
                    'entry_signal': opp.entry_signal,
                    'confidence': opp.confidence,
                    'expected_move': opp.expected_move,
                    'priority': opp.priority,
                    'metadata': opp.metadata
                }
                for opp in scanner.opportunities
            ],
            'rankings': scanner.get_volatility_rankings()
        }
        
        return JSONResponse(content=export_data)
        
    except Exception as e:
        logger.error(f"Error exporting data: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# WebSocket endpoint for real-time updates
@app.websocket("/ws/volatility")
async def volatility_websocket(websocket):
    """WebSocket endpoint for real-time volatility updates"""
    await websocket.accept()
    
    try:
        scanner = await get_scanner()
        
        # Send initial data
        initial_data = {
            'type': 'initial',
            'data': {
                'status': scanner.get_scanner_status(),
                'opportunities': len(scanner.opportunities),
                'top_profiles': [
                    profile.to_dict() 
                    for profile in list(scanner.volatility_profiles.values())[:10]
                ]
            }
        }
        
        await websocket.send_json(initial_data)
        
        # Send updates every 30 seconds
        while True:
            await asyncio.sleep(30)
            
            # Send updated data
            update_data = {
                'type': 'update',
                'timestamp': datetime.now().isoformat(),
                'data': {
                    'opportunities_count': len(scanner.opportunities),
                    'new_breakouts': [
                        {'symbol': symbol, 'strength': profile.breakout_strength}
                        for symbol, profile in scanner.volatility_profiles.items()
                        if profile.breakout_detected
                    ],
                    'top_movers': [
                        {'symbol': symbol, 'change_1h': profile.price_change_1h}
                        for symbol, profile in 
                        sorted(scanner.volatility_profiles.items(), 
                              key=lambda x: abs(x[1].price_change_1h), reverse=True)[:5]
                    ]
                }
            }
            
            await websocket.send_json(update_data)
            
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        await websocket.close()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)