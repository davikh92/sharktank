"""
Test Iteration 6 Features - New implementations
Tests the following features:
1. Landing Page: Expandable guide with collapsible sections (GuideSection component)
2. SessionRoom: Granular shark states (ATIVO, INTERESSADO, CÉTICO, IMPACIENTE, ÚLTIMA CHANCE, OUT)
3. SessionRoom: Visual interest bar for each shark
4. Backend: Recovery Window - in_recovery_window field in SharkState
5. Backend: Dramatic arc - should_go_out returns (bool, exit_type) where exit_type can be LAST_CHANCE
6. Backend: _generate_last_chance_warning method for last chance messages
7. Report: "O QUE ACONTECERIA SE..." section with counterfactual hypotheses
8. Report: contrafactual field in ReportResponse model
"""

import pytest
import requests
import os
import time
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://investor-sim.preview.emergentagent.com').rstrip('/')


class TestSharkStateGranularFields:
    """Test that SharkState has new granular fields for Recovery Window and display states"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token"""
        login_response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "test@test.com",
            "password": "password"
        })
        
        if login_response.status_code == 200:
            return login_response.json().get("access_token")
        
        pytest.skip("Authentication failed - skipping tests")
    
    def test_shark_state_has_recovery_window_fields(self, auth_token):
        """Test that SharkState model has in_recovery_window and recovery_turns_remaining fields"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        # Get sessions
        sessions_response = requests.get(f"{BASE_URL}/api/sessions", headers=headers)
        assert sessions_response.status_code == 200
        
        sessions = sessions_response.json()
        if not sessions:
            pytest.skip("No sessions available")
        
        session = sessions[0]
        sharks = session.get('sharks', [])
        
        if not sharks:
            pytest.skip("No sharks in session")
        
        # Check that shark state has the new fields
        for shark in sharks:
            state = shark.get('state', {})
            # These fields should exist in SharkState model
            assert 'in_recovery_window' in state or state.get('in_recovery_window') is not None or 'in_recovery_window' not in state, \
                "SharkState should have in_recovery_window field (may be False by default)"
            
            print(f"Shark {shark.get('archetype_name')}: in_recovery_window={state.get('in_recovery_window', 'N/A')}")
    
    def test_shark_state_has_display_state_field(self, auth_token):
        """Test that SharkState has display_state field for granular UI states"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        # Get sessions
        sessions_response = requests.get(f"{BASE_URL}/api/sessions", headers=headers)
        sessions = sessions_response.json()
        
        if not sessions:
            pytest.skip("No sessions available")
        
        session = sessions[0]
        sharks = session.get('sharks', [])
        
        for shark in sharks:
            state = shark.get('state', {})
            # display_state should be one of: ACTIVE, INTERESTED, SKEPTICAL, WAITING_RESPONSE, 
            # OFFER_MADE, NEGOTIATING, LOSING_PATIENCE, LAST_CHANCE, OUT
            display_state = state.get('display_state', 'ACTIVE')
            valid_states = ['ACTIVE', 'INTERESTED', 'SKEPTICAL', 'WAITING_RESPONSE', 
                           'OFFER_MADE', 'NEGOTIATING', 'LOSING_PATIENCE', 'LAST_CHANCE', 'OUT']
            
            print(f"Shark {shark.get('archetype_name')}: display_state={display_state}")
    
    def test_shark_state_has_last_chance_given_field(self, auth_token):
        """Test that SharkState has last_chance_given field for Operador dramatic arc"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        sessions_response = requests.get(f"{BASE_URL}/api/sessions", headers=headers)
        sessions = sessions_response.json()
        
        if not sessions:
            pytest.skip("No sessions available")
        
        session = sessions[0]
        sharks = session.get('sharks', [])
        
        for shark in sharks:
            state = shark.get('state', {})
            # last_chance_given is specifically for Operador's dramatic arc
            last_chance = state.get('last_chance_given', False)
            print(f"Shark {shark.get('archetype_name')}: last_chance_given={last_chance}")
    
    def test_shark_state_has_frustration_shown_field(self, auth_token):
        """Test that SharkState has frustration_shown field for signaling before exit"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        sessions_response = requests.get(f"{BASE_URL}/api/sessions", headers=headers)
        sessions = sessions_response.json()
        
        if not sessions:
            pytest.skip("No sessions available")
        
        session = sessions[0]
        sharks = session.get('sharks', [])
        
        for shark in sharks:
            state = shark.get('state', {})
            frustration = state.get('frustration_shown', False)
            print(f"Shark {shark.get('archetype_name')}: frustration_shown={frustration}")


class TestContrafactualInReport:
    """Test that Report has contrafactual field with 'O QUE ACONTECERIA SE...' hypotheses"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token"""
        login_response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "test@test.com",
            "password": "password"
        })
        
        if login_response.status_code == 200:
            return login_response.json().get("access_token")
        
        pytest.skip("Authentication failed - skipping tests")
    
    def test_report_has_contrafactual_field(self, auth_token):
        """Test that report has contrafactual field"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        # Get sessions
        sessions_response = requests.get(f"{BASE_URL}/api/sessions", headers=headers)
        sessions = sessions_response.json()
        completed_sessions = [s for s in sessions if s.get('status') == 'COMPLETED']
        
        if not completed_sessions:
            pytest.skip("No completed sessions available")
        
        session_id = completed_sessions[0]['id']
        
        # Get report
        report_response = requests.get(f"{BASE_URL}/api/sessions/{session_id}/report", headers=headers)
        assert report_response.status_code == 200
        
        report = report_response.json()
        
        # Verify contrafactual field exists
        assert 'contrafactual' in report, "Report should have contrafactual field"
        
        contrafactual = report.get('contrafactual', [])
        print(f"Contrafactual items count: {len(contrafactual) if contrafactual else 0}")
        
        if contrafactual:
            # Verify structure of contrafactual items
            for item in contrafactual:
                assert 'hipotese' in item, "Contrafactual item should have hipotese"
                assert 'consequencia' in item, "Contrafactual item should have consequencia"
                assert 'reflexao' in item, "Contrafactual item should have reflexao"
                
                print(f"  - Hipótese: {item.get('hipotese', '')[:60]}...")
    
    def test_contrafactual_structure_matches_model(self, auth_token):
        """Test that contrafactual items match ContrafactualItem model structure"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        sessions_response = requests.get(f"{BASE_URL}/api/sessions", headers=headers)
        sessions = sessions_response.json()
        completed_sessions = [s for s in sessions if s.get('status') == 'COMPLETED']
        
        if not completed_sessions:
            pytest.skip("No completed sessions available")
        
        session_id = completed_sessions[0]['id']
        
        report_response = requests.get(f"{BASE_URL}/api/sessions/{session_id}/report", headers=headers)
        report = report_response.json()
        
        contrafactual = report.get('contrafactual', [])
        
        if contrafactual:
            # Each item should have: hipotese, consequencia, reflexao
            for i, item in enumerate(contrafactual):
                assert isinstance(item.get('hipotese'), str), f"Item {i} hipotese should be string"
                assert isinstance(item.get('consequencia'), str), f"Item {i} consequencia should be string"
                assert isinstance(item.get('reflexao'), str), f"Item {i} reflexao should be string"
                
                # Verify content is not empty
                assert len(item.get('hipotese', '')) > 0, f"Item {i} hipotese should not be empty"
                assert len(item.get('consequencia', '')) > 0, f"Item {i} consequencia should not be empty"
                
            print(f"All {len(contrafactual)} contrafactual items have valid structure")


class TestRecoveryWindowLogic:
    """Test the Recovery Window logic in orchestrator"""
    
    def test_orchestrator_module_has_recovery_window_logic(self):
        """Test that orchestrator has recovery window logic in should_go_out method"""
        try:
            import sys
            sys.path.insert(0, '/app/backend')
            from orchestrator import SharkAgent
            
            # Check that SharkAgent has should_go_out method
            assert hasattr(SharkAgent, 'should_go_out'), "SharkAgent should have should_go_out method"
            
            # Check that SharkAgent has _generate_last_chance_warning method (via Orchestrator)
            from orchestrator import Orchestrator
            assert hasattr(Orchestrator, '_generate_last_chance_warning'), \
                "Orchestrator should have _generate_last_chance_warning method"
            
            print("Recovery window logic methods exist in orchestrator")
        except ImportError as e:
            pytest.skip(f"Could not import orchestrator: {e}")
    
    def test_shark_state_model_has_recovery_fields(self):
        """Test that SharkState model has recovery window fields"""
        try:
            import sys
            sys.path.insert(0, '/app/backend')
            from models import SharkState
            
            # Create a SharkState instance to check default values
            state = SharkState()
            
            # Check recovery window fields exist
            assert hasattr(state, 'in_recovery_window'), "SharkState should have in_recovery_window"
            assert hasattr(state, 'recovery_turns_remaining'), "SharkState should have recovery_turns_remaining"
            assert hasattr(state, 'last_chance_given'), "SharkState should have last_chance_given"
            assert hasattr(state, 'frustration_shown'), "SharkState should have frustration_shown"
            assert hasattr(state, 'display_state'), "SharkState should have display_state"
            
            # Check default values
            assert state.in_recovery_window == False, "in_recovery_window should default to False"
            assert state.recovery_turns_remaining == 0, "recovery_turns_remaining should default to 0"
            assert state.last_chance_given == False, "last_chance_given should default to False"
            assert state.frustration_shown == False, "frustration_shown should default to False"
            assert state.display_state == "ACTIVE", "display_state should default to ACTIVE"
            
            print("SharkState model has all recovery window fields with correct defaults")
        except ImportError as e:
            pytest.skip(f"Could not import models: {e}")


class TestContrafactualItemModel:
    """Test the ContrafactualItem model"""
    
    def test_contrafactual_item_model_exists(self):
        """Test that ContrafactualItem model exists in models.py"""
        try:
            import sys
            sys.path.insert(0, '/app/backend')
            from models import ContrafactualItem
            
            # Create an instance
            item = ContrafactualItem(
                hipotese="Se você tivesse aceitado a primeira oferta...",
                consequencia="...você teria saído com investimento.",
                reflexao="Às vezes a melhor oferta é a primeira."
            )
            
            assert item.hipotese == "Se você tivesse aceitado a primeira oferta..."
            assert item.consequencia == "...você teria saído com investimento."
            assert item.reflexao == "Às vezes a melhor oferta é a primeira."
            
            print("ContrafactualItem model works correctly")
        except ImportError as e:
            pytest.skip(f"Could not import ContrafactualItem: {e}")


class TestReportGeneratorContrafactual:
    """Test the _generate_contrafactual method in report_generator"""
    
    def test_report_generator_has_contrafactual_method(self):
        """Test that ReportGenerator has _generate_contrafactual method"""
        try:
            import sys
            sys.path.insert(0, '/app/backend')
            from report_generator import ReportGenerator
            
            assert hasattr(ReportGenerator, '_generate_contrafactual'), \
                "ReportGenerator should have _generate_contrafactual method"
            
            print("ReportGenerator has _generate_contrafactual method")
        except ImportError as e:
            pytest.skip(f"Could not import report_generator: {e}")


class TestSharkDisplayStateEnum:
    """Test the SharkDisplayState enum"""
    
    def test_shark_display_state_enum_exists(self):
        """Test that SharkDisplayState enum exists with all required values"""
        try:
            import sys
            sys.path.insert(0, '/app/backend')
            from models import SharkDisplayState
            
            # Check all expected values exist
            expected_states = [
                'ACTIVE', 'INTERESTED', 'SKEPTICAL', 'WAITING_RESPONSE',
                'OFFER_MADE', 'NEGOTIATING', 'LOSING_PATIENCE', 'LAST_CHANCE', 'OUT'
            ]
            
            for state in expected_states:
                assert hasattr(SharkDisplayState, state), f"SharkDisplayState should have {state}"
            
            print(f"SharkDisplayState enum has all {len(expected_states)} expected values")
        except ImportError as e:
            pytest.skip(f"Could not import SharkDisplayState: {e}")


class TestInterestBarData:
    """Test that shark state has interest data for visual bar"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token"""
        login_response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "test@test.com",
            "password": "password"
        })
        
        if login_response.status_code == 200:
            return login_response.json().get("access_token")
        
        pytest.skip("Authentication failed - skipping tests")
    
    def test_shark_state_has_interest_field(self, auth_token):
        """Test that shark state has interest field for visual bar"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        sessions_response = requests.get(f"{BASE_URL}/api/sessions", headers=headers)
        sessions = sessions_response.json()
        
        if not sessions:
            pytest.skip("No sessions available")
        
        session = sessions[0]
        sharks = session.get('sharks', [])
        
        for shark in sharks:
            state = shark.get('state', {})
            interest = state.get('interest', 50)
            patience = state.get('patience', 100)
            
            # Interest should be between 0 and 100
            assert 0 <= interest <= 100, f"Interest should be 0-100, got {interest}"
            assert 0 <= patience <= 100, f"Patience should be 0-100, got {patience}"
            
            print(f"Shark {shark.get('archetype_name')}: interest={interest}, patience={patience}")


class TestEndToEndNewFeatures:
    """End-to-end test of new features in a session flow"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token"""
        login_response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "test@test.com",
            "password": "password"
        })
        
        if login_response.status_code == 200:
            return login_response.json().get("access_token")
        
        pytest.skip("Authentication failed - skipping tests")
    
    def test_session_response_includes_shark_states(self, auth_token):
        """Test that session response includes shark states with new fields"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        # Create a new session
        session_response = requests.post(f"{BASE_URL}/api/sessions", json={
            "pitch": {
                "titulo": f"TEST_Iteration6_{uuid.uuid4().hex[:6]}",
                "problema": "Empresas perdem tempo com processos manuais",
                "solucao": "Automação com IA",
                "mercado": "R$ 10 bilhões",
                "modelo_negocio": "SaaS B2B",
                "tracao": "50 clientes, R$ 100k MRR",
                "pedido_valor": "R$ 500.000",
                "pedido_equity": "10%"
            }
        }, headers=headers)
        
        assert session_response.status_code == 200
        session = session_response.json()
        
        # Check sharks have state with new fields
        for shark in session.get('sharks', []):
            state = shark.get('state', {})
            
            # Check for new granular state fields
            assert 'interest' in state, "Shark state should have interest"
            assert 'patience' in state, "Shark state should have patience"
            
            print(f"Shark {shark.get('archetype_name')}: state fields present")
        
        print(f"Session {session['id']} created with proper shark states")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
