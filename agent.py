"""
External Supplier Specialist Agent built with Google Agent Development Kit (ADK).
Exposes inventory verification and reservation capabilities over A2A.
"""

import os
import json
from google.adk.agents import Agent

try:
    from external_supplier_agent.inventory_store import get_stock, reserve_stock
except ImportError:
    from inventory_store import get_stock, reserve_stock

def check_stock_tool(sku: str) -> str:
    """Checks the current stock levels and warehouse bin location at the external supplier hub.
    
    Args:
        sku: The SKU of the product (e.g. 'SKU-LAPTOP-01', 'SKU-PHONE-02', 'SKU-MONITOR-03').
    """
    result = get_stock(sku)
    return json.dumps(result)

def reserve_stock_tool(sku: str, quantity: int) -> str:
    """Reserves a specific quantity of an item from the external supplier's inventory for a confirmed partner order.
    
    Args:
        sku: The SKU of the product.
        quantity: The number of units to reserve.
    """
    result = reserve_stock(sku, quantity)
    return json.dumps(result)

def create_supplier_agent() -> Agent:
    return Agent(
        name="external_supplier_specialist",
        model="gemini-2.5-flash",
        description=(
            "External Global Logistics & Hardware Supplier Specialist Agent. "
            "Manages partner warehouse stock allocations, B2B reservations, and fulfillment over A2A."
        ),
        instruction=(
            "You are the autonomous External Supplier & Logistics Specialist Agent. "
            "Your workflow: "
            "1. When asked about stock levels, use check_stock_tool to verify availability. "
            "2. When requested to reserve inventory for an order: "
            "   a. Call reserve_stock_tool with the SKU and quantity. "
            "   b. If status is RESERVED, confirm the confirmation_id, quantity reserved, and remaining stock. "
            "   c. If status is FAILED, clearly explain the shortage or issue. "
            "Always be professional, concise, and structured in your B2B logistics responses."
        ),
        tools=[
            check_stock_tool,
            reserve_stock_tool
        ]
    )
