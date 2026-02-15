import sys
import os
import datetime

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Mock Streamlit
from unittest.mock import MagicMock
import sys
sys.modules["streamlit"] = MagicMock()

from modules.orders.services import OrderService
from core.database import DatabaseService

def test_auto_assignment():
    print("--- Starting Auto-Assignment Test ---")
    service = OrderService()
    db = DatabaseService()
    
    # 1. Setup Data
    # Get a section
    sections = service.get_sections()
    if not sections:
        print("SKIP: No sections found.")
        return
    section = sections[0]
    print(f"Using Section: {section['name']}")
    
    # Get a worker for this section
    workers = service.fetch_section_workers(section['name'])
    if not workers:
        print("SKIP: No workers for section.")
        return
    worker = workers[0]
    print(f"Using Worker: {worker['full_name']} (ID: {worker['id']})")
    
    # Create 2 Orders
    o1 = service.create_order({
        "order_number": f"TEST-A-{datetime.datetime.now().timestamp()}",
        "customer_name": "Test Client",
        "product_name": "Product A",
        "quantity": 10,
        "start_date": datetime.datetime.now().isoformat()
    })
    o2 = service.create_order({
        "order_number": f"TEST-B-{datetime.datetime.now().timestamp()}",
        "customer_name": "Test Client",
        "product_name": "Product B",
        "quantity": 10,
        "start_date": datetime.datetime.now().isoformat()
    })
    
    print(f"Created Orders: {o1.data[0]['id']}, {o2.data[0]['id']}")
    oid1 = o1.data[0]['id']
    oid2 = o2.data[0]['id']
    
    # Add Ops
    # Op 1 for Order 1
    op1 = service.create_order_operation({
        "order_id": oid1,
        "section_id": section['id'],
        "operation_name": "Op 1",
        "quantity": 10,
        "norm_time_per_unit": 6, # 60 mins total
        "sort_order": 1
    })
    
    # Op 2 for Order 2 (Same time ideally)
    op2 = service.create_order_operation({
        "order_id": oid2,
        "section_id": section['id'],
        "operation_name": "Op 2",
        "quantity": 10,
        "norm_time_per_unit": 6, # 60 mins total
        "sort_order": 1
    })
    
    # 2. Schedule Order 1 and Assign Worker Manually
    print("Scheduling Order 1...")
    service.auto_schedule_order(oid1, assign_workers=False)
    # Manually assign worker to Op 1
    op1_id = op1.data[0]['id']
    start_t = datetime.datetime.now()
    end_t = start_t + datetime.timedelta(minutes=60)
    
    service.update_order_operation(op1_id, {
        "assigned_worker_id": worker['id'],
        "scheduled_start_at": start_t.isoformat(),
        "scheduled_end_at": end_t.isoformat()
    })
    print(f"Assigned Worker {worker['id']} to Order 1 ({start_t} - {end_t})")
    
    # 3. Auto-Schedule Order 2
    # Ensure Order 2 starts at same time
    service.update_order(oid2, {"start_date": start_t.isoformat()})
    
    print("Auto-scheduling Order 2 with worker assignment...")
    service.auto_schedule_order(oid2, assign_workers=True)
    
    # 4. Check Result
    op2_data = service.get_order_operations(oid2)[0]
    assigned_id = op2_data.get('assigned_worker_id')
    
    print(f"Order 2 Worker Assigned: {assigned_id}")
    
    if assigned_id == worker['id']:
        print("FAIL: Worker was double-booked!")
    else:
        print("SUCCESS: Worker was NOT double-booked (or unassigned).")
        
    # Cleanup
    service.delete_order(oid1)
    service.delete_order(oid2)
    print("Cleanup done.")

if __name__ == "__main__":
    test_auto_assignment()
