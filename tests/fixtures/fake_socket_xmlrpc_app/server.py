"""A simple XML-RPC server exposing inventory management functions."""

from xmlrpc.server import SimpleXMLRPCServer

INVENTORY: dict = {}


def add_item(item_id: str, name: str, quantity: int) -> dict:
    """Add an item to the inventory."""
    INVENTORY[item_id] = {"id": item_id, "name": name, "quantity": quantity}
    return INVENTORY[item_id]


def get_item(item_id: str) -> dict:
    """Get details of an inventory item by ID."""
    return INVENTORY.get(item_id, {"error": "Item not found"})


def update_quantity(item_id: str, quantity: int) -> dict:
    """Update the quantity of an existing inventory item."""
    if item_id not in INVENTORY:
        return {"error": "Item not found"}
    INVENTORY[item_id]["quantity"] = quantity
    return INVENTORY[item_id]


def remove_item(item_id: str) -> bool:
    """Remove an item from the inventory."""
    return INVENTORY.pop(item_id, None) is not None


def list_items() -> list:
    """List all inventory items."""
    return list(INVENTORY.values())


def main():
    server = SimpleXMLRPCServer(("localhost", 8001), allow_none=True)
    server.register_function(add_item)
    server.register_function(get_item)
    server.register_function(update_quantity)
    server.register_function(remove_item)
    server.register_function(list_items)
    print("XML-RPC server listening on port 8001")
    server.serve_forever()


if __name__ == "__main__":
    main()
