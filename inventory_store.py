"""
External Supplier Warehouse Store.
Manages global stock allocations for external B2B partner fulfillment.
"""

from typing import Dict, Any

SUPPLIER_INVENTORY: Dict[str, Dict[str, Any]] = {
    "SKU-LAPTOP-01": {
        "name": "Enterprise Pro Laptop 16-inch",
        "stock": 50,
        "warehouse_location": "Render-Partner-Hub-A1",
        "supplier": "Global Tech Logistics"
    },
    "SKU-PHONE-02": {
        "name": "Flagship 5G Smartphone",
        "stock": 100,
        "warehouse_location": "Render-Partner-Hub-B3",
        "supplier": "Global Tech Logistics"
    },
    "SKU-MONITOR-03": {
        "name": "4K Ultra-Wide Studio Monitor",
        "stock": 35,
        "warehouse_location": "Render-Partner-Hub-C2",
        "supplier": "Global Tech Logistics"
    }
}

def get_stock(sku: str) -> Dict[str, Any]:
    item = SUPPLIER_INVENTORY.get(sku.upper())
    if not item:
        return {"error": f"SKU '{sku}' not recognized in external supplier catalog."}
    return {
        "sku": sku.upper(),
        "name": item["name"],
        "stock": item["stock"],
        "warehouse_location": item["warehouse_location"],
        "supplier": item["supplier"]
    }

def reserve_stock(sku: str, quantity: int) -> Dict[str, Any]:
    sku_upper = sku.upper()
    item = SUPPLIER_INVENTORY.get(sku_upper)
    if not item:
        return {"status": "FAILED", "reason": f"SKU '{sku}' not found in supplier catalog."}
    
    if item["stock"] < quantity:
        return {
            "status": "FAILED",
            "reason": f"Insufficient stock for {sku_upper}. Requested {quantity}, available: {item['stock']}."
        }
    
    item["stock"] -= quantity
    return {
        "status": "RESERVED",
        "sku": sku_upper,
        "quantity_reserved": quantity,
        "remaining_stock": item["stock"],
        "warehouse_location": item["warehouse_location"],
        "supplier": item["supplier"],
        "confirmation_id": f"PARTNER-RES-{sku_upper[-4:]}-{quantity}"
    }
