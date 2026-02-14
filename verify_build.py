import sys
import os

# Add project root to path
sys.path.append(os.getcwd())

print("Verifying imports...")

try:
    import core.config
    print("✅ core.config")
    import core.database
    print("✅ core.database")
    import core.auth
    print("✅ core.auth")
    import ui.layout
    print("✅ ui.layout")
    import modules.dashboard.view
    print("✅ modules.dashboard.view")
    import modules.orders.view
    print("✅ modules.orders.view")
    import modules.planning.view
    print("✅ modules.planning.view")
    import modules.inventory.view
    print("✅ modules.inventory.view")
    import modules.workers.view
    print("✅ modules.workers.view")
    import app
    print("✅ app")
    
    print("\nAll modules imported successfully!")

except ImportError as e:
    print(f"\n❌ Import Error: {e}")
    sys.exit(1)
except SyntaxError as e:
    print(f"\n❌ Syntax Error: {e}")
    sys.exit(1)
except Exception as e:
    print(f"\n❌ Unexpected Error: {e}")
    sys.exit(1)
