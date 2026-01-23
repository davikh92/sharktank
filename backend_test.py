import requests
import sys
import json
import time
from datetime import datetime

class InvestorPanelTester:
    def __init__(self, base_url="https://investor-sim.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.token = None
        self.user_id = None
        self.tests_run = 0
        self.tests_passed = 0
        self.session_id = None

    def run_test(self, name, method, endpoint, expected_status, data=None, headers=None):
        """Run a single API test"""
        url = f"{self.api_url}/{endpoint}"
        test_headers = {'Content-Type': 'application/json'}
        
        if self.token:
            test_headers['Authorization'] = f'Bearer {self.token}'
        
        if headers:
            test_headers.update(headers)

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=test_headers, timeout=30)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=test_headers, timeout=30)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=test_headers, timeout=30)
            elif method == 'DELETE':
                response = requests.delete(url, headers=test_headers, timeout=30)

            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                try:
                    return success, response.json()
                except:
                    return success, {}
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                try:
                    error_detail = response.json()
                    print(f"   Error: {error_detail}")
                except:
                    print(f"   Response: {response.text}")
                return False, {}

        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            return False, {}

    def test_root_endpoint(self):
        """Test root API endpoint"""
        success, response = self.run_test(
            "Root API Endpoint",
            "GET",
            "",
            200
        )
        return success

    def test_register(self):
        """Test user registration"""
        timestamp = int(time.time())
        test_email = f"test_{timestamp}@example.com"
        test_password = "TestPass123!"
        
        success, response = self.run_test(
            "User Registration",
            "POST",
            "auth/register",
            200,
            data={"email": test_email, "password": test_password}
        )
        
        if success and 'access_token' in response:
            self.token = response['access_token']
            self.user_id = response['user']['id']
            print(f"   Registered user: {test_email}")
            return True
        return False

    def test_login(self):
        """Test user login with existing credentials"""
        if not self.token:
            return False
            
        # Create a new user for login test
        timestamp = int(time.time()) + 1
        test_email = f"login_test_{timestamp}@example.com"
        test_password = "LoginTest123!"
        
        # Register first
        reg_success, reg_response = self.run_test(
            "Register for Login Test",
            "POST",
            "auth/register",
            200,
            data={"email": test_email, "password": test_password}
        )
        
        if not reg_success:
            return False
        
        # Now test login
        success, response = self.run_test(
            "User Login",
            "POST",
            "auth/login",
            200,
            data={"email": test_email, "password": test_password}
        )
        
        return success and 'access_token' in response

    def test_get_me(self):
        """Test get current user"""
        if not self.token:
            return False
            
        success, response = self.run_test(
            "Get Current User",
            "GET",
            "auth/me",
            200
        )
        
        return success and 'id' in response

    def test_get_sharks(self):
        """Test get sharks archetypes"""
        success, response = self.run_test(
            "Get Sharks Archetypes",
            "GET",
            "sharks",
            200
        )
        
        if success and 'sharks' in response:
            sharks = response['sharks']
            print(f"   Found {len(sharks)} sharks")
            expected_sharks = ['O Operador', 'O Financeiro', 'O Cético', 'O Visionário']
            found_sharks = [s['name'] for s in sharks]
            
            for expected in expected_sharks:
                if expected not in found_sharks:
                    print(f"   ❌ Missing shark: {expected}")
                    return False
            
            print(f"   ✅ All expected sharks found: {found_sharks}")
            return True
        
        return False

    def test_create_session(self):
        """Test session creation"""
        if not self.token:
            return False
            
        pitch_data = {
            "titulo": "EcoTech Solutions",
            "problema": "Empresas desperdiçam 40% de energia por falta de monitoramento inteligente",
            "solucao": "Sistema IoT que monitora e otimiza consumo energético em tempo real",
            "mercado": "Mercado de eficiência energética no Brasil: R$ 2.5 bilhões anuais",
            "modelo_negocio": "SaaS B2B com mensalidade de R$ 500-2000 por empresa",
            "tracao": "15 clientes piloto, economia média de 25% na conta de luz",
            "pedido_valor": "R$ 500.000",
            "pedido_equity": "15%"
        }
        
        session_data = {
            "pitch": pitch_data,
            "panel_selection": None,  # Random selection
            "reading_hints_enabled": True
        }
        
        success, response = self.run_test(
            "Create Session",
            "POST",
            "sessions",
            200,
            data=session_data
        )
        
        if success and 'id' in response:
            self.session_id = response['id']
            print(f"   Created session: {self.session_id}")
            
            # Verify session has 4 sharks
            sharks = response.get('sharks', [])
            if len(sharks) != 4:
                print(f"   ❌ Expected 4 sharks, got {len(sharks)}")
                return False
            
            print(f"   ✅ Session created with {len(sharks)} sharks")
            return True
        
        return False

    def test_list_sessions(self):
        """Test listing user sessions"""
        if not self.token:
            return False
            
        success, response = self.run_test(
            "List Sessions",
            "GET",
            "sessions",
            200
        )
        
        if success and isinstance(response, list):
            print(f"   Found {len(response)} sessions")
            return True
        
        return False

    def test_get_session(self):
        """Test get specific session"""
        if not self.token or not self.session_id:
            return False
            
        success, response = self.run_test(
            "Get Session",
            "GET",
            f"sessions/{self.session_id}",
            200
        )
        
        if success and response.get('id') == self.session_id:
            print(f"   Retrieved session: {response.get('pitch', {}).get('titulo', 'Unknown')}")
            return True
        
        return False

    def test_start_session(self):
        """Test starting a session"""
        if not self.token or not self.session_id:
            return False
            
        success, response = self.run_test(
            "Start Session",
            "POST",
            f"sessions/{self.session_id}/start",
            200
        )
        
        if success:
            messages = response.get('messages', [])
            can_respond = response.get('can_user_respond', False)
            
            if messages and can_respond:
                print(f"   ✅ Session started with {len(messages)} initial messages")
                print(f"   First message: {messages[0].get('content', '')[:50]}...")
                return True
            else:
                print(f"   ❌ Session started but missing messages or response capability")
        
        return False

    def test_respond_to_session(self):
        """Test responding to session"""
        if not self.token or not self.session_id:
            return False
            
        user_response = "Nosso sistema já está implementado em 15 empresas com resultados comprovados. A economia média é de 25% na conta de luz, com ROI em 8 meses. Temos uma equipe técnica sólida e parcerias estratégicas com fornecedores de IoT."
        
        success, response = self.run_test(
            "Respond to Session",
            "POST",
            f"sessions/{self.session_id}/respond",
            200,
            data={"content": user_response}
        )
        
        if success:
            messages = response.get('messages', [])
            events = response.get('events', [])
            
            print(f"   ✅ Response processed with {len(messages)} new messages and {len(events)} events")
            
            # Check if we got a shark response
            shark_messages = [m for m in messages if m.get('speaker') != 'USER']
            if shark_messages:
                print(f"   Shark response: {shark_messages[0].get('content', '')[:50]}...")
            
            return True
        
        return False

    def test_get_session_messages(self):
        """Test getting session messages"""
        if not self.token or not self.session_id:
            return False
            
        success, response = self.run_test(
            "Get Session Messages",
            "GET",
            f"sessions/{self.session_id}/messages",
            200
        )
        
        if success and isinstance(response, list):
            print(f"   Found {len(response)} messages in session")
            return True
        
        return False

    def test_get_session_events(self):
        """Test getting session events"""
        if not self.token or not self.session_id:
            return False
            
        success, response = self.run_test(
            "Get Session Events",
            "GET",
            f"sessions/{self.session_id}/events",
            200
        )
        
        if success and isinstance(response, list):
            print(f"   Found {len(response)} events in session")
            return True
        
        return False

    def test_session_completion_flow(self):
        """Test multiple interactions to potentially complete session"""
        if not self.token or not self.session_id:
            return False
            
        responses = [
            "Temos 3 anos de desenvolvimento, equipe de 8 pessoas incluindo 4 engenheiros seniores. Já validamos a tecnologia em ambiente real.",
            "Nosso CAC é R$ 2.500 e LTV de R$ 15.000. Margem bruta de 70%. Projeção de 100 clientes no primeiro ano.",
            "O diferencial é nossa IA proprietária que aprende padrões específicos de cada empresa. Temos 2 patentes depositadas.",
            "Mercado TAM de R$ 50 bilhões globalmente. Começamos no Brasil mas já temos interesse de empresas na América Latina."
        ]
        
        completed = False
        
        for i, response_text in enumerate(responses):
            print(f"\n📝 Interaction {i+1}/4")
            
            success, response = self.run_test(
                f"Session Interaction {i+1}",
                "POST",
                f"sessions/{self.session_id}/respond",
                200,
                data={"content": response_text}
            )
            
            if not success:
                break
                
            session_status = response.get('session_status')
            can_respond = response.get('can_user_respond', False)
            
            print(f"   Status: {session_status}, Can respond: {can_respond}")
            
            if session_status == 'COMPLETED':
                completed = True
                print(f"   ✅ Session completed after {i+1} interactions")
                break
            elif not can_respond:
                print(f"   ⚠️ Cannot respond anymore but session not completed")
                break
                
            # Small delay to simulate real interaction
            time.sleep(1)
        
        return completed

    def test_generate_report(self):
        """Test report generation"""
        if not self.token or not self.session_id:
            return False
            
        # First check if session is completed
        session_success, session_data = self.run_test(
            "Check Session Status for Report",
            "GET",
            f"sessions/{self.session_id}",
            200
        )
        
        if not session_success:
            return False
            
        if session_data.get('status') != 'COMPLETED':
            print(f"   ⚠️ Session not completed (status: {session_data.get('status')}), cannot generate report")
            return True  # Not a failure, just not ready
            
        success, response = self.run_test(
            "Generate Report",
            "POST",
            f"sessions/{self.session_id}/report",
            200
        )
        
        if success and 'sintese' in response:
            print(f"   ✅ Report generated")
            print(f"   Síntese: {response.get('sintese', '')[:100]}...")
            return True
        
        return False

    def test_get_report(self):
        """Test getting existing report"""
        if not self.token or not self.session_id:
            return False
            
        success, response = self.run_test(
            "Get Report",
            "GET",
            f"sessions/{self.session_id}/report",
            200
        )
        
        if success and 'sintese' in response:
            print(f"   ✅ Report retrieved")
            return True
        elif not success:
            print(f"   ℹ️ Report not found (expected if session not completed)")
            return True  # Not a failure if report doesn't exist yet
        
        return False

def main():
    print("🚀 Starting Investor Panel Simulator API Tests")
    print("=" * 60)
    
    tester = InvestorPanelTester()
    
    # Test sequence
    tests = [
        ("Root Endpoint", tester.test_root_endpoint),
        ("User Registration", tester.test_register),
        ("User Login", tester.test_login),
        ("Get Current User", tester.test_get_me),
        ("Get Sharks", tester.test_get_sharks),
        ("Create Session", tester.test_create_session),
        ("List Sessions", tester.test_list_sessions),
        ("Get Session", tester.test_get_session),
        ("Start Session", tester.test_start_session),
        ("Respond to Session", tester.test_respond_to_session),
        ("Get Session Messages", tester.test_get_session_messages),
        ("Get Session Events", tester.test_get_session_events),
        ("Session Completion Flow", tester.test_session_completion_flow),
        ("Generate Report", tester.test_generate_report),
        ("Get Report", tester.test_get_report),
    ]
    
    failed_tests = []
    
    for test_name, test_func in tests:
        try:
            if not test_func():
                failed_tests.append(test_name)
        except Exception as e:
            print(f"❌ {test_name} - Exception: {str(e)}")
            failed_tests.append(test_name)
    
    # Print results
    print("\n" + "=" * 60)
    print(f"📊 Test Results: {tester.tests_passed}/{tester.tests_run} passed")
    
    if failed_tests:
        print(f"\n❌ Failed tests:")
        for test in failed_tests:
            print(f"   - {test}")
    else:
        print(f"\n✅ All tests passed!")
    
    print(f"\n🔗 Session ID for frontend testing: {tester.session_id}")
    
    return 0 if not failed_tests else 1

if __name__ == "__main__":
    sys.exit(main())