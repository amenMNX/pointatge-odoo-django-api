import xmlrpc.client
from django.conf import settings
from django.utils import timezone
from .models import Pointage

def sync_pointages_to_odoo():
    """
    Sync unsynced pointages to Odoo hr.pointage model.
    Uses PIN to find employee and maps to correct Odoo fields.
    """
    # Get Odoo connection settings
    url = settings.ODOO_URL
    db = settings.ODOO_DB
    username = settings.ODOO_USERNAME
    password = settings.ODOO_PASSWORD
    
    if not all([url, db, username, password]):
        raise Exception("Odoo connection settings are incomplete")

    try:
        # Authenticate with Odoo
        common = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/common")
        uid = common.authenticate(db, username, password, {})
        
        if not uid:
            raise Exception("Odoo authentication failed - invalid credentials")
        
        print(f"✅ Authenticated with Odoo (UID: {uid})")
        
        models = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/object")
        
        # Get unsynced pointages
        pointages = Pointage.objects.filter(synced_to_odoo=False).select_related('employee')
        
        if not pointages.exists():
            print("ℹ️ No unsynced pointages found")
            return
        
        print(f"🔄 Found {pointages.count()} unsynced pointage(s)")
        
        success_count = 0
        error_count = 0
        
        for p in pointages:
            try:
                print(f"📤 Processing Pointage ID {p.id} for employee {p.employee.pin}...")
                
                # 1. Find Odoo employee by PIN
                employee_ids = models.execute_kw(
                    db, uid, password,
                    'hr.employee', 'search',
                    [[['pin', '=', str(p.employee.pin)]]]  # Ensure PIN is string
                )
                
                if not employee_ids:
                    print(f"❌ Employee with PIN '{p.employee.pin}' not found in Odoo")
                    error_count += 1
                    continue
                
                odoo_employee_id = employee_ids[0]
                
                # 2. Prepare data for Odoo hr.pointage model
                # Get date from check_time
                date = p.check_time.date().strftime("%Y-%m-%d")
                
                # Determine if this is check_in or check_out based on state
                check_time_str = p.check_time.strftime("%Y-%m-%d %H:%M:%S")
                
                # 3. First, check if a pointage record already exists for this employee and date
                existing_pointage_ids = models.execute_kw(
                    db, uid, password,
                    'hr.pointage', 'search',
                    [[
                        ['employee_id', '=', odoo_employee_id],
                        ['date', '=', date]
                    ]]
                )
                
                if existing_pointage_ids:
                    # Update existing record
                    pointage_id = existing_pointage_ids[0]
                    
                    if p.state == "IN":
                        # Set check_in if it's IN
                        models.execute_kw(
                            db, uid, password,
                            'hr.pointage', 'write',
                            [[pointage_id], {
                                'check_in': check_time_str,
                                'state': 'validated'  # Auto-validate if desired
                            }]
                        )
                        print(f"  ↪️ Updated check_in for existing pointage")
                    else:  # OUT
                        # Set check_out if it's OUT
                        models.execute_kw(
                            db, uid, password,
                            'hr.pointage', 'write',
                            [[pointage_id], {
                                'check_out': check_time_str,
                                'state': 'validated'  # Auto-validate if desired
                            }]
                        )
                        print(f"  ↪️ Updated check_out for existing pointage")
                    
                    odoo_id = pointage_id
                else:
                    # Create new pointage record
                    vals = {
                        'employee_id': odoo_employee_id,
                        'date': date,
                        'state': 'validated',  # Or 'draft' if you want manual validation
                    }
                    
                    # Set check_in or check_out based on state
                    if p.state == "IN":
                        vals['check_in'] = check_time_str
                    else:  # OUT
                        vals['check_out'] = check_time_str
                    
                    # Create new record in Odoo
                    odoo_id = models.execute_kw(
                        db, uid, password,
                        'hr.pointage', 'create',
                        [vals]
                    )
                    print(f"  ↪️ Created new pointage record")
                
                # 4. Mark as synced in Django
                p.synced_to_odoo = True
                p.external_id = str(odoo_id)
                p.save(update_fields=["synced_to_odoo", "external_id"])
                
                success_count += 1
                print(f"✅ Successfully synced Pointage {p.id} → Odoo ID {odoo_id}")
                
            except xmlrpc.client.Fault as e:
                print(f"❌ XML-RPC Fault for Pointage {p.id}: {e.faultString}")
                error_count += 1
            except Exception as e:
                print(f"❌ Failed to sync pointage {p.id}: {str(e)}")
                error_count += 1
        
        # Summary
        print("\n" + "="*50)
        print(f"📊 SYNC SUMMARY")
        print(f"   Successful: {success_count}")
        print(f"   Failed:     {error_count}")
        print(f"   Total:      {success_count + error_count}")
        
        if success_count > 0:
            print(f"✅ Sync completed successfully!")
        elif error_count > 0:
            raise Exception(f"All {error_count} sync attempts failed")
            
    except xmlrpc.client.Fault as e:
        raise Exception(f"Odoo XML-RPC Fault: {e.faultString}")
    except Exception as e:
        raise Exception(f"Sync failed: {str(e)}")