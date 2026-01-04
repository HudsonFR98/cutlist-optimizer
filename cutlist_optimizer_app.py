from cutlist_optimizer import create_app
from cutlist_optimizer.lib import config
import os

app = create_app()

if __name__ == '__main__':
    # Run the app in debug mode if in development
    debug_mode = config.CONTEXT == 'dev' and getattr(config, 'DEBUG', False)
    
    if debug_mode:
        # In development mode, Flask's reloader will automatically watch
        # the main application file and imported modules
        print("Starting Flask development server with hot reloading enabled...")
        print("Changes to Python files will trigger automatic reloading.")
        print("Flask's classic error reporting and debug toolbar are enabled.")
        print("Access the debug toolbar at the bottom of any page in development mode.")
    
    app.run(
        debug=debug_mode, 
        host='0.0.0.0', 
        port=8080, 
        use_reloader=debug_mode
    )
