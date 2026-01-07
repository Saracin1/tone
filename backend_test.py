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
            
            // Insert test user with Premium subscription
            db.users.insertOne({{
              user_id: userId,
              google_user_id: 'google_' + userId,
              email: email,
              name: 'Test User',
              picture: 'https://via.placeholder.com/150',
              access_level: 'Limited',
              subscription_type: 'Premium',
              subscription_status: 'active',
              subscription_start_date: new Date().toISOString(),
              subscription_end_date: new Date(Date.now() + 30*24*60*60*1000).toISOString(),
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
              google_user_id: 'google_' + adminId,
              email: adminEmail,
              name: 'Test Admin',
              picture: 'https://via.placeholder.com/150',
              access_level: 'admin',
              subscription_type: 'Premium',
              subscription_status: 'active',
              subscription_start_date: new Date().toISOString(),
              subscription_end_date: new Date(Date.now() + 30*24*60*60*1000).toISOString(),
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

    def setup_forecast_test_data(self):
        """Setup test forecast data in MongoDB"""
        print("\n🔧 Setting up forecast test data...")
        
        try:
            timestamp = int(datetime.now().timestamp())
            
            mongo_script = f"""
            use('test_database');
            
            // Clear existing test forecast data
            db.forecast_history.deleteMany({{instrument_code: /TEST_/}});
            
            // Insert test forecast data
            var testForecasts = [
                {{
                    record_id: 'forecast_test_success_1',
                    instrument_code: 'TEST_AAPL',
                    market: 'NASDAQ',
                    forecast_date: '2024-01-15',
                    forecast_direction: 'Bullish',
                    entry_price: 150.0,
                    forecast_target_price: 160.0,
                    actual_result_price: 165.0,
                    result_date: '2024-01-20',
                    calculated_pl_percent: 10.0,
                    status: 'success',
                    notes: 'Test successful forecast',
                    created_at: new Date().toISOString(),
                    updated_at: new Date().toISOString()
                }},
                {{
                    record_id: 'forecast_test_failed_1',
                    instrument_code: 'TEST_TSLA',
                    market: 'NASDAQ',
                    forecast_date: '2024-01-10',
                    forecast_direction: 'Bearish',
                    entry_price: 200.0,
                    forecast_target_price: 180.0,
                    actual_result_price: 210.0,
                    result_date: '2024-01-18',
                    calculated_pl_percent: -5.0,
                    status: 'failed',
                    notes: 'Test failed forecast',
                    created_at: new Date().toISOString(),
                    updated_at: new Date().toISOString()
                }},
                {{
                    record_id: 'forecast_test_pending_1',
                    instrument_code: 'TEST_GOOGL',
                    market: 'NASDAQ',
                    forecast_date: '2024-01-25',
                    forecast_direction: 'Bullish',
                    entry_price: 120.0,
                    forecast_target_price: 130.0,
                    actual_result_price: null,
                    result_date: null,
                    calculated_pl_percent: null,
                    status: 'pending',
                    notes: 'Test pending forecast',
                    created_at: new Date().toISOString(),
                    updated_at: new Date().toISOString()
                }}
            ];
            
            db.forecast_history.insertMany(testForecasts);
            print('Inserted ' + testForecasts.length + ' test forecasts');
            """
            
            result = subprocess.run(['mongosh', '--eval', mongo_script], 
                                  capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                print("✅ Test forecast data created")
                return True
            else:
                print(f"❌ Failed to create test forecast data: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"❌ Error creating test forecast data: {str(e)}")
            return False

    def test_history_endpoints(self):
        """Test History of Success endpoints"""
        print("\n📈 Testing History of Success Endpoints...")
        
        # Test authentication required for all endpoints
        temp_token = self.session_token
        self.session_token = None
        
        self.run_test("History Summary - No Auth", "GET", "history/summary", 401)
        self.run_test("History Forecasts - No Auth", "GET", "history/forecasts", 401)
        self.run_test("History Performance - No Auth", "GET", "history/performance", 401)
        self.run_test("History Cumulative - No Auth", "GET", "history/cumulative", 401)
        self.run_test("History Markets - No Auth", "GET", "history/markets", 401)
        
        self.session_token = temp_token
        
        # Test authenticated endpoints
        summary_data = self.run_test("History Summary", "GET", "history/summary", 200)
        if summary_data:
            expected_fields = ['total_forecasts', 'completed_forecasts', 'successful_forecasts', 
                             'pending_forecasts', 'win_rate', 'total_return_percent', 
                             'avg_return_percent', 'best_trade_percent', 'worst_trade_percent']
            
            for field in expected_fields:
                has_field = field in summary_data
                self.log_test(f"Summary Field - {field}", has_field, 
                            f"Missing field: {field}" if not has_field else "")
        
        forecasts_data = self.run_test("History Forecasts", "GET", "history/forecasts", 200)
        if forecasts_data:
            self.log_test("Forecasts Data Structure", isinstance(forecasts_data, list), 
                         f"Response type: {type(forecasts_data)}")
            
            if forecasts_data and len(forecasts_data) > 0:
                forecast = forecasts_data[0]
                expected_fields = ['record_id', 'instrument_code', 'market', 'forecast_date', 
                                 'forecast_direction', 'entry_price', 'forecast_target_price', 'status']
                
                for field in expected_fields:
                    has_field = field in forecast
                    self.log_test(f"Forecast Field - {field}", has_field, 
                                f"Missing field: {field}" if not has_field else "")
        
        performance_data = self.run_test("History Performance", "GET", "history/performance", 200)
        if performance_data:
            self.log_test("Performance Data Structure", isinstance(performance_data, list), 
                         f"Response type: {type(performance_data)}")
        
        cumulative_data = self.run_test("History Cumulative", "GET", "history/cumulative", 200)
        if cumulative_data:
            self.log_test("Cumulative Data Structure", isinstance(cumulative_data, list), 
                         f"Response type: {type(cumulative_data)}")
        
        markets_data = self.run_test("History Markets", "GET", "history/markets", 200)
        if markets_data:
            has_markets_field = 'markets' in markets_data
            self.log_test("Markets Response Structure", has_markets_field, 
                         f"Response keys: {list(markets_data.keys()) if isinstance(markets_data, dict) else 'Not a dict'}")
        
        # Test query parameters
        self.run_test("History Forecasts - Market Filter", "GET", "history/forecasts?market=NASDAQ", 200)
        self.run_test("History Forecasts - Status Filter", "GET", "history/forecasts?status=success", 200)
        self.run_test("History Forecasts - Limit", "GET", "history/forecasts?limit=5", 200)

    def test_admin_history_endpoints(self):
        """Test admin History of Success endpoints"""
        print("\n🔐 Testing Admin History Endpoints...")
        
        if not self.admin_token:
            print("⚠️ No admin token available, skipping admin tests")
            return None
        
        # Test admin access required
        self.run_test("Admin Get Forecasts - User Access", "GET", "admin/history/forecasts", 403)
        
        # Switch to admin token
        old_token = self.session_token
        self.session_token = self.admin_token
        
        # Test admin get all forecasts
        admin_forecasts = self.run_test("Admin Get All Forecasts", "GET", "admin/history/forecasts", 200)
        
        # Test create new forecast
        new_forecast_data = {
            "instrument_code": "TEST_MSFT",
            "market": "NASDAQ",
            "forecast_date": "2024-01-30",
            "forecast_direction": "Bullish",
            "entry_price": 300.0,
            "forecast_target_price": 320.0,
            "notes": "Test admin created forecast"
        }
        
        created_forecast = self.run_test("Admin Create Forecast", "POST", "admin/history/forecast", 200, new_forecast_data)
        
        forecast_id = None
        if created_forecast and 'record_id' in created_forecast:
            forecast_id = created_forecast['record_id']
            
            # Test update forecast with result
            update_data = {
                "actual_result_price": 325.0,
                "result_date": "2024-02-05",
                "notes": "Updated with actual result"
            }
            
            updated_forecast = self.run_test(f"Admin Update Forecast", "PUT", 
                                           f"admin/history/forecast/{forecast_id}", 200, update_data)
            
            if updated_forecast:
                # Verify P/L calculation
                expected_pl = ((325.0 - 300.0) / 300.0) * 100  # Should be ~8.33%
                actual_pl = updated_forecast.get('calculated_pl_percent', 0)
                pl_correct = abs(actual_pl - expected_pl) < 0.1
                self.log_test("P/L Calculation Correct", pl_correct, 
                            f"Expected: {expected_pl:.2f}%, Got: {actual_pl}%")
                
                # Verify status determination
                expected_status = "success"  # 325 >= 320 (target)
                actual_status = updated_forecast.get('status')
                status_correct = actual_status == expected_status
                self.log_test("Status Determination Correct", status_correct, 
                            f"Expected: {expected_status}, Got: {actual_status}")
        
        # Test delete forecast
        if forecast_id:
            self.run_test("Admin Delete Forecast", "DELETE", f"admin/history/forecast/{forecast_id}", 200)
            
            # Verify deletion
            self.run_test("Admin Delete Forecast - Verify", "DELETE", f"admin/history/forecast/{forecast_id}", 404)
        
        # Test non-existent forecast operations
        self.run_test("Admin Update Non-existent", "PUT", "admin/history/forecast/non_existent", 404, update_data)
        self.run_test("Admin Delete Non-existent", "DELETE", "admin/history/forecast/non_existent", 404)
        
        # Switch back to regular user
        self.session_token = old_token
        
        # Test regular user cannot access admin endpoints
        self.run_test("User Create Forecast - Should Fail", "POST", "admin/history/forecast", 403, new_forecast_data)
        self.run_test("User Update Forecast - Should Fail", "PUT", "admin/history/forecast/test_id", 403, update_data)
        self.run_test("User Delete Forecast - Should Fail", "DELETE", "admin/history/forecast/test_id", 403)
        
        return admin_forecasts

    def test_pl_calculation_logic(self):
        """Test P/L calculation logic for different scenarios"""
        print("\n🧮 Testing P/L Calculation Logic...")
        
        if not self.admin_token:
            print("⚠️ No admin token available, skipping P/L calculation tests")
            return
        
        old_token = self.session_token
        self.session_token = self.admin_token
        
        # Test Bullish successful trade
        bullish_success = {
            "instrument_code": "TEST_PL_BULL_SUCCESS",
            "market": "TEST",
            "forecast_date": "2024-01-01",
            "forecast_direction": "Bullish",
            "entry_price": 100.0,
            "forecast_target_price": 110.0,
            "actual_result_price": 115.0,
            "result_date": "2024-01-10",
            "notes": "Bullish success test"
        }
        
        result = self.run_test("P/L Test - Bullish Success", "POST", "admin/history/forecast", 200, bullish_success)
        if result:
            expected_pl = ((115.0 - 100.0) / 100.0) * 100  # 15%
            actual_pl = result.get('calculated_pl_percent', 0)
            expected_status = "success"  # 115 >= 110
            actual_status = result.get('status')
            
            self.log_test("Bullish Success P/L", abs(actual_pl - expected_pl) < 0.1, 
                         f"Expected: {expected_pl}%, Got: {actual_pl}%")
            self.log_test("Bullish Success Status", actual_status == expected_status, 
                         f"Expected: {expected_status}, Got: {actual_status}")
        
        # Test Bullish failed trade
        bullish_failed = {
            "instrument_code": "TEST_PL_BULL_FAILED",
            "market": "TEST",
            "forecast_date": "2024-01-01",
            "forecast_direction": "Bullish",
            "entry_price": 100.0,
            "forecast_target_price": 110.0,
            "actual_result_price": 95.0,
            "result_date": "2024-01-10",
            "notes": "Bullish failed test"
        }
        
        result = self.run_test("P/L Test - Bullish Failed", "POST", "admin/history/forecast", 200, bullish_failed)
        if result:
            expected_pl = ((95.0 - 100.0) / 100.0) * 100  # -5%
            actual_pl = result.get('calculated_pl_percent', 0)
            expected_status = "failed"  # 95 < 110
            actual_status = result.get('status')
            
            self.log_test("Bullish Failed P/L", abs(actual_pl - expected_pl) < 0.1, 
                         f"Expected: {expected_pl}%, Got: {actual_pl}%")
            self.log_test("Bullish Failed Status", actual_status == expected_status, 
                         f"Expected: {expected_status}, Got: {actual_status}")
        
        # Test Bearish successful trade
        bearish_success = {
            "instrument_code": "TEST_PL_BEAR_SUCCESS",
            "market": "TEST",
            "forecast_date": "2024-01-01",
            "forecast_direction": "Bearish",
            "entry_price": 100.0,
            "forecast_target_price": 90.0,
            "actual_result_price": 85.0,
            "result_date": "2024-01-10",
            "notes": "Bearish success test"
        }
        
        result = self.run_test("P/L Test - Bearish Success", "POST", "admin/history/forecast", 200, bearish_success)
        if result:
            expected_pl = ((100.0 - 85.0) / 100.0) * 100  # 15%
            actual_pl = result.get('calculated_pl_percent', 0)
            expected_status = "success"  # 85 <= 90
            actual_status = result.get('status')
            
            self.log_test("Bearish Success P/L", abs(actual_pl - expected_pl) < 0.1, 
                         f"Expected: {expected_pl}%, Got: {actual_pl}%")
            self.log_test("Bearish Success Status", actual_status == expected_status, 
                         f"Expected: {expected_status}, Got: {actual_status}")
        
        # Test Bearish failed trade
        bearish_failed = {
            "instrument_code": "TEST_PL_BEAR_FAILED",
            "market": "TEST",
            "forecast_date": "2024-01-01",
            "forecast_direction": "Bearish",
            "entry_price": 100.0,
            "forecast_target_price": 90.0,
            "actual_result_price": 105.0,
            "result_date": "2024-01-10",
            "notes": "Bearish failed test"
        }
        
        result = self.run_test("P/L Test - Bearish Failed", "POST", "admin/history/forecast", 200, bearish_failed)
        if result:
            expected_pl = ((100.0 - 105.0) / 100.0) * 100  # -5%
            actual_pl = result.get('calculated_pl_percent', 0)
            expected_status = "failed"  # 105 > 90
            actual_status = result.get('status')
            
            self.log_test("Bearish Failed P/L", abs(actual_pl - expected_pl) < 0.1, 
                         f"Expected: {expected_pl}%, Got: {actual_pl}%")
            self.log_test("Bearish Failed Status", actual_status == expected_status, 
                         f"Expected: {expected_status}, Got: {actual_status}")
        
        self.session_token = old_token

    def cleanup_forecast_test_data(self):
        """Clean up forecast test data"""
        print("\n🧹 Cleaning up forecast test data...")
        
        try:
            mongo_script = """
            use('test_database');
            
            // Clean up test forecast data
            var deletedForecasts = db.forecast_history.deleteMany({
                $or: [
                    {instrument_code: /TEST_/},
                    {record_id: /forecast_test_/}
                ]
            });
            
            print('Deleted test forecasts: ' + deletedForecasts.deletedCount);
            """
            
            result = subprocess.run(['mongosh', '--eval', mongo_script], 
                                  capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                print("✅ Forecast test data cleaned up")
            else:
                print(f"⚠️ Forecast cleanup warning: {result.stderr}")
                
        except Exception as e:
            print(f"⚠️ Forecast cleanup error: {str(e)}")

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
            
            // Clean up test forecast data
            var deletedForecasts = db.forecast_history.deleteMany({
                $or: [
                    {instrument_code: /TEST_/},
                    {record_id: /forecast_test_/}
                ]
            });
            
            print('Deleted users: ' + deletedUsers.deletedCount);
            print('Deleted sessions: ' + deletedSessions.deletedCount);
            print('Deleted admins: ' + deletedAdmins.deletedCount);
            print('Deleted admin sessions: ' + deletedAdminSessions.deletedCount);
            print('Deleted test forecasts: ' + deletedForecasts.deletedCount);
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
        
        # Setup test data for History of Success
        self.setup_forecast_test_data()
        
        # Run tests
        self.test_auth_endpoints()
        markets_data = self.test_markets_endpoints()
        assets_data = self.test_assets_endpoints(markets_data)
        self.test_analysis_endpoints(assets_data)
        self.test_chart_endpoints()
        self.test_sample_data()
        
        # Test History of Success feature
        self.test_history_endpoints()
        self.test_admin_history_endpoints()
        self.test_pl_calculation_logic()
        
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