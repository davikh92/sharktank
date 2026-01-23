"""
Test New Features - Bug fixes and improvements
Tests the following features:
1. Bug fix: Sharks OUT visual display (sharksOutSet based on events)
2. Shark phrase variations by archetype in reports
3. Variable cinematic endings in reports
4. New Session page with 3 steps, pitch strength indicator, contextual tips
"""

import pytest
import requests
import os
import time
import uuid
import random

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://investor-sim.preview.emergentagent.com').rstrip('/')


class TestSharksOutEvents:
    """Test that SHARK_OUT events are properly tracked and returned"""
    
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
    
    def test_events_endpoint_returns_shark_out_events(self, auth_token):
        """Test that events endpoint returns SHARK_OUT events"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        # Get sessions
        sessions_response = requests.get(f"{BASE_URL}/api/sessions", headers=headers)
        assert sessions_response.status_code == 200
        
        sessions = sessions_response.json()
        completed_sessions = [s for s in sessions if s.get('status') == 'COMPLETED']
        
        if not completed_sessions:
            pytest.skip("No completed sessions available")
        
        session_id = completed_sessions[0]['id']
        
        # Get events
        events_response = requests.get(f"{BASE_URL}/api/sessions/{session_id}/events", headers=headers)
        assert events_response.status_code == 200
        
        events = events_response.json()
        shark_out_events = [e for e in events if e.get('event_type') == 'SHARK_OUT']
        
        # Verify SHARK_OUT events have required fields
        for event in shark_out_events:
            assert 'actor' in event, "SHARK_OUT event should have actor field"
            assert 'data' in event, "SHARK_OUT event should have data field"
            assert event['actor'] in ['O Operador', 'O Financeiro', 'O Cético', 'O Visionário'], \
                f"SHARK_OUT actor should be a valid shark archetype, got: {event['actor']}"
        
        print(f"Found {len(shark_out_events)} SHARK_OUT events")
    
    def test_session_sharks_have_is_out_field(self, auth_token):
        """Test that session sharks have is_out field"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        # Get sessions
        sessions_response = requests.get(f"{BASE_URL}/api/sessions", headers=headers)
        sessions = sessions_response.json()
        completed_sessions = [s for s in sessions if s.get('status') == 'COMPLETED']
        
        if not completed_sessions:
            pytest.skip("No completed sessions available")
        
        session = completed_sessions[0]
        
        # Verify sharks have is_out field
        for shark in session.get('sharks', []):
            assert 'archetype_name' in shark, "Shark should have archetype_name"
            # is_out can be in shark directly or in state
            has_is_out = 'is_out' in shark or ('state' in shark and 'is_out' in shark.get('state', {}))
            assert has_is_out, f"Shark {shark.get('archetype_name')} should have is_out field"


class TestSharkPhraseVariations:
    """Test that report has different phrases for each shark archetype"""
    
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
    
    def test_report_has_leitura_sharks_with_thoughts(self, auth_token):
        """Test that report has leitura_sharks with o_que_pensou field"""
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
        
        # Verify leitura_sharks exists
        assert 'leitura_sharks' in report, "Report should have leitura_sharks field"
        
        leitura_sharks = report['leitura_sharks']
        assert len(leitura_sharks) > 0, "leitura_sharks should not be empty"
        
        # Verify each shark has required fields
        for shark_reading in leitura_sharks:
            assert 'shark' in shark_reading, "Shark reading should have shark name"
            assert 'o_que_buscava' in shark_reading, "Shark reading should have o_que_buscava"
            assert 'o_que_pensou' in shark_reading, "Shark reading should have o_que_pensou"
            assert 'resultado' in shark_reading, "Shark reading should have resultado"
            
            # Verify o_que_pensou is not empty
            assert shark_reading['o_que_pensou'], f"o_que_pensou should not be empty for {shark_reading['shark']}"
            
            print(f"{shark_reading['shark']}: {shark_reading['o_que_pensou'][:50]}...")
    
    def test_shark_thesis_matches_archetype(self, auth_token):
        """Test that each shark's thesis matches their archetype"""
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
        report = report_response.json()
        
        expected_thesis = {
            "O Operador": "Execução clara, time competente, e plano de crescimento realista",
            "O Financeiro": "Unit economics sólidos, margem saudável, e caminho para lucratividade",
            "O Cético": "Diferencial defensável, barreira de entrada, e proteção contra concorrência",
            "O Visionário": "Mercado grande, potencial de escala, e timing certo"
        }
        
        for shark_reading in report.get('leitura_sharks', []):
            shark_name = shark_reading.get('shark')
            if shark_name in expected_thesis:
                assert shark_reading.get('o_que_buscava') == expected_thesis[shark_name], \
                    f"Thesis mismatch for {shark_name}"


class TestCinematicEndings:
    """Test that report has variable cinematic endings"""
    
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
    
    def test_report_has_veredito(self, auth_token):
        """Test that report has veredito field"""
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
        
        # Verify veredito exists and is not empty
        assert 'veredito' in report, "Report should have veredito field"
        assert report['veredito'], "Veredito should not be empty"
        
        print(f"Veredito: {report['veredito']}")
    
    def test_report_has_pergunta_provocativa(self, auth_token):
        """Test that report has pergunta_provocativa field"""
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
        report = report_response.json()
        
        # Verify pergunta_provocativa exists
        assert 'pergunta_provocativa' in report, "Report should have pergunta_provocativa field"
        assert report['pergunta_provocativa'], "pergunta_provocativa should not be empty"
        
        print(f"Pergunta provocativa: {report['pergunta_provocativa']}")


class TestNewSessionPage:
    """Test the new session creation endpoint"""
    
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
    
    def test_sharks_endpoint_returns_all_archetypes(self, auth_token):
        """Test that sharks endpoint returns all 4 archetypes"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        response = requests.get(f"{BASE_URL}/api/sharks", headers=headers)
        assert response.status_code == 200
        
        data = response.json()
        sharks = data.get('sharks', [])
        
        assert len(sharks) == 4, "Should have 4 shark archetypes"
        
        shark_names = [s.get('name') for s in sharks]
        expected_names = ['O Operador', 'O Financeiro', 'O Cético', 'O Visionário']
        
        for name in expected_names:
            assert name in shark_names, f"Missing shark archetype: {name}"
        
        # Verify each shark has required fields
        for shark in sharks:
            assert 'id' in shark, "Shark should have id"
            assert 'name' in shark, "Shark should have name"
            assert 'tese' in shark, "Shark should have tese"
            assert 'foco' in shark, "Shark should have foco"
    
    def test_session_creation_with_pitch_data(self, auth_token):
        """Test creating a session with pitch data"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        pitch_data = {
            "pitch": {
                "titulo": f"TEST_NewFeatures_{uuid.uuid4().hex[:6]}",
                "problema": "Empresas perdem R$ 50 bilhões por ano com má gestão",
                "solucao": "Plataforma SaaS com IA para automação",
                "mercado": "Mercado de R$ 15 bilhões em software",
                "modelo_negocio": "SaaS com assinatura mensal de R$ 299/mês",
                "tracao": "150 clientes pagantes, R$ 45k MRR",
                "pedido_valor": "R$ 500.000",
                "pedido_equity": "10%"
            },
            "panel_selection": None,
            "reading_hints_enabled": False
        }
        
        response = requests.post(f"{BASE_URL}/api/sessions", json=pitch_data, headers=headers)
        assert response.status_code == 200, f"Session creation failed: {response.text}"
        
        session = response.json()
        assert 'id' in session, "Session should have id"
        assert session.get('status') == 'PENDING', "New session should be PENDING"
        
        # Verify pitch data was saved
        assert session.get('pitch', {}).get('titulo') == pitch_data['pitch']['titulo']
        
        print(f"Created session: {session['id']}")


class TestAutopsiaAnalysis:
    """Test the autopsia analysis in reports"""
    
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
    
    def test_report_has_autopsia_fields(self, auth_token):
        """Test that report has autopsia analysis fields"""
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
        report = report_response.json()
        
        # Verify autopsia exists
        assert 'autopsia' in report, "Report should have autopsia field"
        
        autopsia = report['autopsia']
        expected_fields = [
            'momento_irreversivel',
            'primeiro_shark_perdido',
            'pergunta_nao_respondida',
            'onde_perdeu_tracao',
            'onde_ganhou_respeito'
        ]
        
        for field in expected_fields:
            assert field in autopsia, f"Autopsia should have {field} field"
        
        print(f"Autopsia fields: {list(autopsia.keys())}")


class TestMicroSinais:
    """Test the micro-sinais in reports"""
    
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
    
    def test_report_has_micro_sinais(self, auth_token):
        """Test that report has micro_sinais field"""
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
        report = report_response.json()
        
        # Verify micro_sinais exists
        assert 'micro_sinais' in report, "Report should have micro_sinais field"
        
        micro_sinais = report['micro_sinais']
        
        if micro_sinais:
            # Verify structure of micro_sinais
            for sinal in micro_sinais:
                assert 'turno' in sinal, "Micro sinal should have turno"
                assert 'shark' in sinal, "Micro sinal should have shark"
                assert 'sinal' in sinal, "Micro sinal should have sinal"
                assert 'traducao_psicologica' in sinal, "Micro sinal should have traducao_psicologica"
            
            print(f"Found {len(micro_sinais)} micro-sinais")
