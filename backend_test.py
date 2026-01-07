import requests
import sys
import json
from datetime import datetime
import subprocess

class FinancialDashboardTester:
    def __init__(self, base_url="https://finanzo.preview.emergentagent.com"):
        self.base_url = base_url
        self.session_token = None
        self.admin_token = None
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []

    def log_test(self, name, success, details=""):
        """Log test result"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name}")
        else:
            print(f"❌ {name} - {details}")
        
        self.test_results.append({
            "test": name,
            "success": success,
            "details": details
        })

    def run_test(self, name, method, endpoint, expected_status, data=None, headers=None):
        """Run a single API test"""
        url = f"{self.base_url}/api/{endpoint}"
        test_headers = {'Content-Type': 'application/json'}
        
        if headers:
            test_headers.update(headers)
        
        if self.session_token and 'Authorization' not in test_headers:
            test_headers['Authorization'] = f'Bearer {self.session_token}'

        try:
            if method == 'GET':
                response = requests.get(url, headers=test_headers, timeout=10)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=test_headers, timeout=10)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=test_headers, timeout=10)
            elif method == 'DELETE':
                response = requests.delete(url, headers=test_headers, timeout=10)

            success = response.status_code == expected_status
            details = f"Status: {response.status_code}"
            
            if not success:
                details += f", Expected: {expected_status}"
                try:
                    error_data = response.json()
                    details += f", Response: {error_data}"
                except:
                    details += f", Response: {response.text[:100]}"
            
            self.log_test(name, success, details)
            
            if success:
                try:
                    return response.json()
                except:
                    return {"status": "success"}
            return None

        except Exception as e:
            self.log_test(name, False, f"Error: {str(e)}")
            return None

    def create_test_user_session(self):
        """Create test user and session in MongoDB"""
        print("\n🔧 Creating test user and session...")
        
        try:
            # Create test user and session using mongosh
            timestamp = int(datetime.now().timestamp())
            user_id = f"test-user-{timestamp}"
            session_token = f"test_session_{timestamp}"
            email = f"test.user.{timestamp}@example.com"
            
            mongo_script = f"""
            use('test_database');
            var userId = '{user_id}';
            var sessionToken = '{session_token}';
            var email = '{email}';
            
            // Insert test user
            db.users.insertOne({{
              user_id: userId,
              email: email,
              name: 'Test User',
              picture: 'https://via.placeholder.com/150',
              role: 'user',
              created_at: new Date().toISOString()
            }});
            
            // Insert test session
            db.user_sessions.insertOne({{
              user_id: userId,
              session_token: sessionToken,
              expires_at: new Date(Date.now() + 7*24*60*60*1000),
              created_at: new Date()
            }});
            
            print('Created user: ' + userId);
            print('Session token: ' + sessionToken);
            """
            
            result = subprocess.run(['mongosh', '--eval', mongo_script], 
                                  capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                self.session_token = session_token
                print(f"✅ Test user created: {user_id}")
                print(f"✅ Session token: {session_token}")
                return True
            else:
                print(f"❌ Failed to create test user: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"❌ Error creating test user: {str(e)}")
            return False

    def create_test_admin_session(self):
        """Create test admin user and session"""
        print("\n🔧 Creating test admin user and session...")
        
        try:
            timestamp = int(datetime.now().timestamp())
            admin_id = f"test-admin-{timestamp}"
            admin_token = f"test_admin_session_{timestamp}"
            admin_email = f"test.admin.{timestamp}@example.com"
            
            mongo_script = f"""
            use('test_database');
            var adminId = '{admin_id}';
            var adminToken = '{admin_token}';
            var adminEmail = '{admin_email}';
            
            // Insert test admin
            db.users.insertOne({{
              user_id: adminId,
              email: adminEmail,
              name: 'Test Admin',
              picture: 'https://via.placeholder.com/150',
              role: 'admin',
              created_at: new Date().toISOString()
            }});
            
            // Insert test admin session
            db.user_sessions.insertOne({{
              user_id: adminId,
              session_token: adminToken,
              expires_at: new Date(Date.now() + 7*24*60*60*1000),
              created_at: new Date()
            }});
            
            print('Created admin: ' + adminId);
            print('Admin token: ' + adminToken);
            """
            
            result = subprocess.run(['mongosh', '--eval', mongo_script], 
                                  capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                self.admin_token = admin_token
                print(f"✅ Test admin created: {admin_id}")
                print(f"✅ Admin token: {admin_token}")
                return True
            else:
                print(f"❌ Failed to create test admin: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"❌ Error creating test admin: {str(e)}")
            return False

    def test_auth_endpoints(self):
        """Test authentication endpoints"""
        print("\n🔐 Testing Authentication Endpoints...")
        
        # Test /auth/me with valid session
        self.run_test("Auth Me - Valid Session", "GET", "auth/me", 200)
        
        # Test /auth/me without session
        temp_token = self.session_token
        self.session_token = None
        self.run_test("Auth Me - No Session", "GET", "auth/me", 401)
        self.session_token = temp_token
        
        # Test logout
        self.run_test("Logout", "POST", "auth/logout", 200)

    def test_markets_endpoints(self):
        """Test markets endpoints"""
        print("\n🏪 Testing Markets Endpoints...")
        
        # Test get markets (public)
        markets_data = self.run_test("Get Markets", "GET", "markets", 200)
        
        # Test create market (admin only)
        if self.admin_token:
            old_token = self.session_token
            self.session_token = self.admin_token
            
            market_data = {
                "name_ar": "سوق الاختبار",
                "name_en": "Test Market",
                "region": "Test Region"
            }
            
            created_market = self.run_test("Create Market - Admin", "POST", "markets", 200, market_data)
            
            self.session_token = old_token
            
            # Test create market as regular user (should fail)
            self.run_test("Create Market - User (Should Fail)", "POST", "markets", 403, market_data)
        
        return markets_data

    def test_assets_endpoints(self, markets_data):
        """Test assets endpoints"""
        print("\n📊 Testing Assets Endpoints...")
        
        # Test get assets
        assets_data = self.run_test("Get Assets", "GET", "assets", 200)
        
        # Test create asset (admin only)
        if self.admin_token and markets_data:
            old_token = self.session_token
            self.session_token = self.admin_token
            
            # Use first market for testing
            market_id = markets_data[0]['market_id'] if markets_data else "test_market"
            
            asset_data = {
                "market_id": market_id,
                "name_ar": "أصل الاختبار",
                "name_en": "Test Asset",
                "type": "stock"
            }
            
            created_asset = self.run_test("Create Asset - Admin", "POST", "assets", 200, asset_data)
            
            self.session_token = old_token
            
            # Test create asset as regular user (should fail)
            self.run_test("Create Asset - User (Should Fail)", "POST", "assets", 403, asset_data)
        
        return assets_data

    def test_analysis_endpoints(self, assets_data):
        """Test analysis endpoints"""
        print("\n📈 Testing Analysis Endpoints...")
        
        if not assets_data:
            print("⚠️ No assets available for analysis testing")
            return
        
        asset_id = assets_data[0]['asset_id'] if assets_data else "test_asset"
        
        # Test get analysis
        self.run_test("Get Analysis", "GET", f"analysis/{asset_id}", 200)
        
        # Test create analysis (admin only)
        if self.admin_token:
            old_token = self.session_token
            self.session_token = self.admin_token
            
            analysis_data = {
                "asset_id": asset_id,
                "bias": "صاعد",
                "key_levels": "دعم: 100، مقاومة: 120",
                "scenario_text": "سيناريو اختبار للتحليل",
                "insight_text": "ملاحظات إضافية",
                "risk_note": "تحذير من المخاطر",
                "confidence_level": "High"
            }
            
            self.run_test("Create Analysis - Admin", "POST", "analysis", 200, analysis_data)
            
            self.session_token = old_token
            
            # Test create analysis as regular user (should fail)
            self.run_test("Create Analysis - User (Should Fail)", "POST", "analysis", 403, analysis_data)

    def test_chart_endpoints(self):
        """Test chart data endpoints for dashboard"""
        print("\n📊 Testing Chart Data Endpoints...")
        
        # Test line chart data endpoint
        line_data = self.run_test("Line Chart Data", "GET", "daily-analysis/line-chart-data", 200)
        if line_data is not None:
            self.log_test("Line Chart Data Structure", 
                         isinstance(line_data, list), 
                         f"Response type: {type(line_data)}")
        
        # Test pie chart data endpoint  
        pie_data = self.run_test("Pie Chart Data", "GET", "daily-analysis/chart-data", 200)
        if pie_data is not None:
            self.log_test("Pie Chart Data Structure", 
                         isinstance(pie_data, list), 
                         f"Response type: {type(pie_data)}")
        
        # Test last sync endpoint
        sync_data = self.run_test("Last Sync Timestamp", "GET", "daily-analysis/last-sync", 200)
        if sync_data is not None:
            has_last_sync = 'last_sync' in sync_data
            self.log_test("Last Sync Response Structure", 
                         has_last_sync, 
                         f"Response keys: {list(sync_data.keys()) if isinstance(sync_data, dict) else 'Not a dict'}")

    def test_sample_data(self):
        """Test if sample data exists"""
        print("\n📋 Testing Sample Data...")
        
        # Get markets and check for expected ones
        markets_data = self.run_test("Get Sample Markets", "GET", "markets", 200)
        
        if markets_data:
            market_names = [market.get('name_en', '') for market in markets_data]
            expected_markets = ['GCC', 'Istanbul', 'Cairo']
            
            for expected in expected_markets:
                found = any(expected.lower() in name.lower() for name in market_names)
                self.log_test(f"Sample Market - {expected}", found, 
                            f"Found markets: {market_names}" if not found else "")
        
        # Get assets and check for expected ones
        assets_data = self.run_test("Get Sample Assets", "GET", "assets", 200)
        
        if assets_data:
            asset_names = [asset.get('name_en', '') for asset in assets_data]
            expected_assets = ['Aramco', 'SABIC', 'BIST 100', 'EGX 30']
            
            for expected in expected_assets:
                found = any(expected.lower() in name.lower() for name in asset_names)
                self.log_test(f"Sample Asset - {expected}", found,
                            f"Found assets: {asset_names}" if not found else "")

    def cleanup_test_data(self):
        """Clean up test data"""
        print("\n🧹 Cleaning up test data...")
        
        try:
            mongo_script = """
            use('test_database');
            
            // Clean up test users and sessions
            var deletedUsers = db.users.deleteMany({email: /test\\.user\\./});
            var deletedSessions = db.user_sessions.deleteMany({session_token: /test_session/});
            var deletedAdmins = db.users.deleteMany({email: /test\\.admin\\./});
            var deletedAdminSessions = db.user_sessions.deleteMany({session_token: /test_admin_session/});
            
            print('Deleted users: ' + deletedUsers.deletedCount);
            print('Deleted sessions: ' + deletedSessions.deletedCount);
            print('Deleted admins: ' + deletedAdmins.deletedCount);
            print('Deleted admin sessions: ' + deletedAdminSessions.deletedCount);
            """
            
            result = subprocess.run(['mongosh', '--eval', mongo_script], 
                                  capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                print("✅ Test data cleaned up")
            else:
                print(f"⚠️ Cleanup warning: {result.stderr}")
                
        except Exception as e:
            print(f"⚠️ Cleanup error: {str(e)}")

    def run_all_tests(self):
        """Run all backend tests"""
        print("🚀 Starting Financial Dashboard Backend Tests")
        print(f"🌐 Testing against: {self.base_url}")
        
        # Create test users
        if not self.create_test_user_session():
            print("❌ Failed to create test user, stopping tests")
            return False
        
        if not self.create_test_admin_session():
            print("⚠️ Failed to create test admin, some tests will be skipped")
        
        # Run tests
        self.test_auth_endpoints()
        markets_data = self.test_markets_endpoints()
        assets_data = self.test_assets_endpoints(markets_data)
        self.test_analysis_endpoints(assets_data)
        self.test_sample_data()
        
        # Cleanup
        self.cleanup_test_data()
        
        # Print results
        print(f"\n📊 Backend Test Results: {self.tests_passed}/{self.tests_run} passed")
        
        if self.tests_passed < self.tests_run:
            print("\n❌ Failed Tests:")
            for result in self.test_results:
                if not result['success']:
                    print(f"  - {result['test']}: {result['details']}")
        
        return self.tests_passed == self.tests_run

def main():
    tester = FinancialDashboardTester()
    success = tester.run_all_tests()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())