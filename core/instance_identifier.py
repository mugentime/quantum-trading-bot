#!/usr/bin/env python3
"""
Instance Identification System
Hard-coded identification for all interaction types
"""

import os
import json
from datetime import datetime
from enum import Enum

class InstanceType(Enum):
    CLAUDE_MAIN = "CLAUDE-MAIN"
    AGENT_RESEARCHER = "AGENT-RESEARCHER"
    AGENT_CODER = "AGENT-CODER"
    AGENT_TESTER = "AGENT-TESTER"
    AGENT_REVIEWER = "AGENT-REVIEWER"
    AGENT_PLANNER = "AGENT-PLANNER"
    AGENT_ANALYZER = "AGENT-ANALYZER"
    AGENT_ARCHITECT = "AGENT-ARCHITECT"
    HIVE_COORDINATOR = "HIVE-COORDINATOR"
    HIVE_WORKER = "HIVE-WORKER"
    SWARM_MESH = "SWARM-MESH"
    SWARM_HIERARCHICAL = "SWARM-HIERARCHICAL"
    MCP_TASKMASTER = "MCP-TASKMASTER"
    MCP_BINANCE = "MCP-BINANCE"
    BOT_TRADING = "BOT-TRADING"
    BOT_SCALPING = "BOT-SCALPING"

class InstanceIdentifier:
    def __init__(self, instance_type: InstanceType, session_id: str = None):
        self.instance_type = instance_type
        self.session_id = session_id or self._generate_session_id()
        self.start_time = datetime.utcnow()
        
    def _generate_session_id(self):
        """Generate unique session ID"""
        timestamp = int(datetime.utcnow().timestamp())
        return f"{timestamp}-{os.getpid()}"
    
    def get_id_prefix(self):
        """Get formatted ID prefix for responses"""
        return f"[{self.instance_type.value}]"
    
    def get_full_id(self):
        """Get full identification string"""
        return f"[{self.instance_type.value}-{self.session_id}]"
    
    def log_interaction(self, message: str, interaction_type: str = "response"):
        """Log interaction with identification"""
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "instance_type": self.instance_type.value,
            "session_id": self.session_id,
            "interaction_type": interaction_type,
            "message": message[:200] + "..." if len(message) > 200 else message
        }
        
        # Save to interaction log
        log_file = "interaction_log.json"
        try:
            if os.path.exists(log_file):
                with open(log_file, 'r') as f:
                    logs = json.load(f)
            else:
                logs = []
            
            logs.append(log_entry)
            
            # Keep only last 100 interactions
            if len(logs) > 100:
                logs = logs[-100:]
            
            with open(log_file, 'w') as f:
                json.dump(logs, f, indent=2)
        except Exception as e:
            print(f"Warning: Could not log interaction: {e}")
    
    def format_response(self, message: str):
        """Format response with ID prefix"""
        prefix = self.get_id_prefix()
        formatted = f"{prefix} {message}"
        self.log_interaction(message)
        return formatted

# Global instance for Claude Main
claude_main = InstanceIdentifier(InstanceType.CLAUDE_MAIN)

def get_claude_response(message: str) -> str:
    """Format Claude main response with ID"""
    return claude_main.format_response(message)

def get_agent_response(agent_type: str, message: str) -> str:
    """Format agent response with ID"""
    # Map agent types to enum values
    agent_map = {
        "researcher": InstanceType.AGENT_RESEARCHER,
        "coder": InstanceType.AGENT_CODER,
        "tester": InstanceType.AGENT_TESTER,
        "reviewer": InstanceType.AGENT_REVIEWER,
        "planner": InstanceType.AGENT_PLANNER,
        "analyst": InstanceType.AGENT_ANALYZER,
        "architect": InstanceType.AGENT_ARCHITECT
    }
    
    instance_type = agent_map.get(agent_type, InstanceType.AGENT_RESEARCHER)
    agent_id = InstanceIdentifier(instance_type)
    return agent_id.format_response(message)

def get_hive_response(message: str, worker_id: int = None) -> str:
    """Format hive mind response with ID"""
    if worker_id:
        hive_id = InstanceIdentifier(InstanceType.HIVE_WORKER, f"worker-{worker_id}")
    else:
        hive_id = InstanceIdentifier(InstanceType.HIVE_COORDINATOR)
    return hive_id.format_response(message)

def get_bot_response(message: str, bot_type: str = "trading") -> str:
    """Format trading bot response with ID"""
    bot_types = {
        "trading": InstanceType.BOT_TRADING,
        "scalping": InstanceType.BOT_SCALPING
    }
    instance_type = bot_types.get(bot_type, InstanceType.BOT_TRADING)
    bot_id = InstanceIdentifier(instance_type)
    return bot_id.format_response(message)

# Auto-initialization (silent)