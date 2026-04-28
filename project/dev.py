import os
from app import create_app

app = create_app('development')

if __name__ == '__main__':
    host = os.environ.get('APP_HOST', '0.0.0.0')
    port = int(os.environ.get('APP_PORT', 5000))
    
    print(f"""
    ========================================
    ComeHere Rider - Development Server
    ========================================
    Starting server at http://{host}:{port}
    Press CTRL+C to quit
    ========================================
    """)
    
    app.run(host=host, port=port, debug=True)
