"""
Test for shark exit behavior with generic/evasive responses
"""
import requests
import time
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://pitch-arena.preview.emergentagent.com').rstrip('/')

def test_shark_exit_with_generic_responses():
    """
    Test that sharks exit when receiving generic/evasive responses
    """
    print("\n" + "="*60)
    print("SHARK EXIT BEHAVIOR TEST")
    print("="*60)
    
    # Login
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": "testfix@test.com",
        "password": "test123"
    })
    assert response.status_code == 200
    token = response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    print("✓ Logged in successfully")
    
    # Create session with vague pitch
    pitch_data = {
        "pitch": {
            "titulo": "Startup Genérica",
            "problema": "Problemas diversos",
            "solucao": "Solução inovadora",
            "mercado": "Grande",
            "modelo_negocio": "Vamos ver",
            "tracao": "Alguns clientes",
            "pedido_valor": "Muito dinheiro",
            "pedido_equity": "Pouco equity"
        },
        "reading_hints_enabled": False
    }
    
    response = requests.post(f"{BASE_URL}/api/sessions", json=pitch_data, headers=headers)
    assert response.status_code == 200
    session_id = response.json()["id"]
    print(f"✓ Session created: {session_id}")
    
    # Start session
    response = requests.post(f"{BASE_URL}/api/sessions/{session_id}/start", headers=headers)
    assert response.status_code == 200
    print("✓ Session started")
    
    # Send generic/evasive responses
    generic_responses = [
        "É disruptivo.",
        "Vamos ver.",
        "O mercado é grande.",
        "Temos uma visão transformadora.",
        "É revolucionário.",
        "Game changer.",
        "Estamos bem posicionados.",
        "Vamos crescer muito.",
        "É inovador.",
        "Temos potencial.",
        "O futuro é promissor.",
        "Vamos dominar o mercado.",
    ]
    
    sharks_out = []
    session_completed = False
    
    for i, user_response in enumerate(generic_responses, 1):
        print(f"\n--- Turn {i} ---")
        print(f"  User: '{user_response}'")
        
        response = requests.post(
            f"{BASE_URL}/api/sessions/{session_id}/respond",
            json={"content": user_response},
            headers=headers
        )
        
        if response.status_code != 200:
            print(f"  ✗ Response failed: {response.text}")
            break
        
        data = response.json()
        
        # Check for SHARK_OUT events
        for event in data['events']:
            if event['event_type'] == 'SHARK_OUT':
                sharks_out.append(event['actor'])
                print(f"  🦈 SHARK_OUT: {event['actor']}")
        
        # Get session state
        session_response = requests.get(f"{BASE_URL}/api/sessions/{session_id}", headers=headers)
        if session_response.status_code == 200:
            session_data = session_response.json()
            active_sharks = [s for s in session_data['sharks'] if not s['state']['is_out']]
            print(f"  Active sharks: {len(active_sharks)}/4")
            
            for shark in session_data['sharks']:
                state = shark['state']
                status = "OUT" if state['is_out'] else f"interest={state['interest']:.1f}, patience={state['patience']:.1f}"
                print(f"    {shark['archetype_name']}: {status}")
        
        if data['session_status'] == 'COMPLETED':
            session_completed = True
            print("\n✓ Session COMPLETED - all sharks exited!")
            break
        
        time.sleep(2)
    
    # Final summary
    print("\n" + "="*60)
    print("FINAL SUMMARY")
    print("="*60)
    print(f"Sharks that exited: {len(sharks_out)}")
    for shark in sharks_out:
        print(f"  - {shark}")
    print(f"Session completed: {session_completed}")
    
    # Verify at least one shark exited
    assert len(sharks_out) > 0 or session_completed, "At least one shark should exit with generic responses"
    print("\n✓ SHARK EXIT BEHAVIOR VERIFIED")
    
    return True

if __name__ == "__main__":
    test_shark_exit_with_generic_responses()
