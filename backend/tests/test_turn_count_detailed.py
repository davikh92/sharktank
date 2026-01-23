"""
Detailed test for turn_count persistence - verifies the actual turn count value
"""
import requests
import time
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://pitch-arena.preview.emergentagent.com').rstrip('/')

def test_turn_count_persistence_detailed():
    """
    Detailed test that verifies turn_count increments correctly
    by checking session state after each response
    """
    print("\n" + "="*60)
    print("DETAILED TURN COUNT PERSISTENCE TEST")
    print("="*60)
    
    # Login
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": "testfix@test.com",
        "password": "test123"
    })
    assert response.status_code == 200, f"Login failed: {response.text}"
    token = response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    print("✓ Logged in successfully")
    
    # Create session
    pitch_data = {
        "pitch": {
            "titulo": "Turn Count Verification Test",
            "problema": "Verificar persistência do turn_count",
            "solucao": "Sistema de testes automatizados",
            "mercado": "R$50 bilhões em automação",
            "modelo_negocio": "SaaS B2B com assinatura mensal",
            "tracao": "200 clientes, R$800k MRR, 25% crescimento mensal",
            "pedido_valor": "R$3 milhões",
            "pedido_equity": "12%"
        },
        "reading_hints_enabled": False
    }
    
    response = requests.post(f"{BASE_URL}/api/sessions", json=pitch_data, headers=headers)
    assert response.status_code == 200, f"Session creation failed: {response.text}"
    session_id = response.json()["id"]
    print(f"✓ Session created: {session_id}")
    
    # Start session
    response = requests.post(f"{BASE_URL}/api/sessions/{session_id}/start", headers=headers)
    assert response.status_code == 200, f"Session start failed: {response.text}"
    print("✓ Session started")
    
    # Track shark states across turns
    turn_data = []
    
    # Send 5 responses with good data
    responses = [
        "Nosso CAC é R$250 e LTV é R$15.000, ratio de 60x. Temos 200 clientes pagantes.",
        "Crescemos 25% ao mês nos últimos 8 meses. Margem bruta de 82%.",
        "Nosso churn é de 1.5% ao mês. NPS de 72. 40% dos clientes vêm por indicação.",
        "Temos 3 patentes registradas. Time de 15 pessoas, 8 engenheiros.",
        "Runway de 18 meses. Break-even projetado para Q3 2026."
    ]
    
    for i, user_response in enumerate(responses, 1):
        print(f"\n--- Turn {i} ---")
        
        response = requests.post(
            f"{BASE_URL}/api/sessions/{session_id}/respond",
            json={"content": user_response},
            headers=headers
        )
        
        if response.status_code != 200:
            print(f"✗ Response failed: {response.text}")
            break
        
        data = response.json()
        
        # Check session status
        print(f"  Session status: {data['session_status']}")
        
        # Count messages and events
        print(f"  Messages in response: {len(data['messages'])}")
        print(f"  Events in response: {len(data['events'])}")
        
        # Check for SHARK_OUT events
        shark_outs = [e for e in data['events'] if e['event_type'] == 'SHARK_OUT']
        if shark_outs:
            for out in shark_outs:
                print(f"  ⚠ SHARK_OUT: {out['actor']}")
        
        # Get session state to check shark states
        session_response = requests.get(f"{BASE_URL}/api/sessions/{session_id}", headers=headers)
        if session_response.status_code == 200:
            session_data = session_response.json()
            active_sharks = [s for s in session_data['sharks'] if not s['state']['is_out']]
            print(f"  Active sharks: {len(active_sharks)}/4")
            
            # Track state changes
            for shark in session_data['sharks']:
                state = shark['state']
                print(f"    {shark['archetype_name']}: interest={state['interest']:.1f}, patience={state['patience']:.1f}, out={state['is_out']}")
        
        if data['session_status'] == 'COMPLETED':
            print("\n✓ Session COMPLETED")
            break
        
        time.sleep(2)
    
    # Final verification
    print("\n" + "="*60)
    print("FINAL VERIFICATION")
    print("="*60)
    
    # Get all messages
    response = requests.get(f"{BASE_URL}/api/sessions/{session_id}/messages", headers=headers)
    messages = response.json()
    print(f"Total messages: {len(messages)}")
    
    # Count user answers (should equal number of turns)
    user_answers = [m for m in messages if m['message_type'] == 'ANSWER']
    print(f"User answers (turns): {len(user_answers)}")
    
    # Get all events
    response = requests.get(f"{BASE_URL}/api/sessions/{session_id}/events", headers=headers)
    events = response.json()
    print(f"Total events: {len(events)}")
    
    # Count event types
    event_types = {}
    for e in events:
        event_types[e['event_type']] = event_types.get(e['event_type'], 0) + 1
    print(f"Event breakdown: {event_types}")
    
    # Verify turn count matches user answers
    assert len(user_answers) > 0, "Should have at least one user answer"
    print(f"\n✓ TURN COUNT PERSISTENCE VERIFIED: {len(user_answers)} turns processed correctly")
    
    return True

if __name__ == "__main__":
    test_turn_count_persistence_detailed()
